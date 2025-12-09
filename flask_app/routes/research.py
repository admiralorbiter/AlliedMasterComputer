# flask_app/routes/research.py

from flask import flash, redirect, render_template, url_for, request, current_app, send_file, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask_app.models import ResearchBrief, Tag, db
from flask_app.forms import ResearchBriefForm, EditBriefForm
from flask_app.utils.openai_service import process_research_brief, calculate_pdf_hash
from io import BytesIO
import os

def register_research_routes(app):
    """Register research brief routes"""
    
    def add_tags_to_brief(brief, tag_input):
        """Helper function to parse and add tags to a brief"""
        if not tag_input or not tag_input.strip():
            return
        
        try:
            # Parse tags (comma-separated, normalize: lowercase, strip)
            tag_names = [tag.strip().lower() for tag in tag_input.split(',') if tag.strip()]
            
            # Add each tag to the brief
            for tag_name in tag_names:
                brief.add_tag(tag_name)
        except Exception as tag_error:
            current_app.logger.error(f"Error adding tags to brief {brief.id}: {str(tag_error)}")
            # Don't fail the whole operation if tags fail
    
    @app.route('/research')
    @login_required
    def research_list():
        """List all research briefs for the current user, optionally filtered by tag"""
        try:
            page = request.args.get('page', 1, type=int)
            tag_id = request.args.get('tag', type=int)
            per_page = 20
            
            # Get briefs, optionally filtered by tag
            if tag_id:
                briefs = ResearchBrief.find_by_user_and_tag(current_user.id, tag_id=tag_id, page=page, per_page=per_page)
            else:
                briefs = ResearchBrief.find_by_user(current_user.id, page=page, per_page=per_page)
            
            if briefs is None:
                flash('An error occurred while loading your research briefs.', 'danger')
                briefs = ResearchBrief.query.filter_by(user_id=current_user.id).paginate(
                    page=page, per_page=per_page, error_out=False
                )
            
            # Get all available tags with counts for filter UI
            tags_with_counts, error = Tag.get_all_tags_with_counts()
            if error:
                current_app.logger.warning(f"Error getting tags with counts: {error}")
                tags_with_counts = []
            
            # Get selected tag if filtering
            selected_tag = None
            if tag_id:
                selected_tag = Tag.query.get(tag_id)
            
            current_app.logger.info(f"Research briefs list accessed by {current_user.username}" + (f" (filtered by tag {tag_id})" if tag_id else ""))
            return render_template('research/list.html', 
                                 briefs=briefs, 
                                 tags_with_counts=tags_with_counts,
                                 selected_tag=selected_tag)
            
        except Exception as e:
            current_app.logger.error(f"Error in research list: {str(e)}")
            flash('An error occurred while loading your research briefs.', 'danger')
            return render_template('research/list.html', briefs=None, tags_with_counts=[], selected_tag=None)
    
    @app.route('/research/create', methods=['GET', 'POST'])
    @login_required
    def research_create():
        """Create a new research brief (supports single or multiple PDF uploads)"""
        form = ResearchBriefForm()
        
        try:
            if form.validate_on_submit():
                # Handle text input (single brief)
                if form.source_type.data == 'text' and form.source_text.data:
                    source_text = form.source_text.data.strip()
                    
                    # Process the brief
                    brief_data, error = process_research_brief(
                        source_text=source_text,
                        pdf_data=None,
                        pdf_filename=None
                    )
                    
                    if error:
                        current_app.logger.error(f"Error generating research brief: {error}")
                        flash(f'Error generating brief: {error}', 'danger')
                        return render_template('research/create.html', form=form)
                    
                    # Validate brief_data exists and has required fields
                    if not brief_data:
                        current_app.logger.error("process_research_brief returned None for brief_data without error")
                        flash('Error generating brief: No data returned from AI service. Please try again.', 'danger')
                        return render_template('research/create.html', form=form)
                    
                    # Validate required fields exist
                    required_fields = ['title', 'citation', 'summary', 'source_text']
                    missing_fields = [field for field in required_fields if field not in brief_data]
                    if missing_fields:
                        current_app.logger.error(f"Missing required fields in brief_data: {missing_fields}")
                        flash(f'Error generating brief: Missing required fields: {", ".join(missing_fields)}. Please try again.', 'danger')
                        return render_template('research/create.html', form=form)
                    
                    # Create the research brief record
                    new_brief, db_error = ResearchBrief.safe_create(
                        user_id=current_user.id,
                        title=brief_data['title'],
                        citation=brief_data['citation'],
                        summary=brief_data['summary'],
                        source_text=brief_data['source_text'],
                        pdf_filename=None,
                        pdf_data=None,
                        source_type='text',
                        model_name=brief_data.get('model_name')
                    )
                    
                    if db_error:
                        flash(f'Error saving brief: {db_error}', 'danger')
                        return render_template('research/create.html', form=form)
                    
                    # Add tags if provided
                    if form.tags.data:
                        add_tags_to_brief(new_brief, form.tags.data)
                    
                    flash('Research brief created successfully!', 'success')
                    current_app.logger.info(f"Research brief {new_brief.id} created by {current_user.username}")
                    return redirect(url_for('research_view', id=new_brief.id))
                
                # Handle manual entry (no AI processing)
                elif form.source_type.data == 'manual':
                    # Create the research brief directly from form data
                    new_brief, db_error = ResearchBrief.safe_create(
                        user_id=current_user.id,
                        title=form.title.data.strip(),
                        citation=form.citation.data.strip(),
                        summary=form.summary.data.strip(),
                        source_text=form.manual_source_text.data.strip() if form.manual_source_text.data else '',
                        url=form.url.data.strip() if form.url.data else None,
                        pdf_filename=None,
                        pdf_data=None,
                        source_type='manual',
                        model_name=form.source_name.data if form.source_name.data else None
                    )
                    
                    if db_error:
                        flash(f'Error saving brief: {db_error}', 'danger')
                        return render_template('research/create.html', form=form)
                    
                    # Add tags if provided
                    if form.tags.data:
                        add_tags_to_brief(new_brief, form.tags.data)
                    
                    flash('Research brief created successfully!', 'success')
                    current_app.logger.info(f"Manual research brief {new_brief.id} created by {current_user.username}")
                    return redirect(url_for('research_view', id=new_brief.id))
                
                # Handle PDF upload(s) - supports both single and multiple files
                elif form.source_type.data == 'pdf':
                    # Get files from request (Flask-WTF FileField doesn't handle multiple files well)
                    pdf_files = request.files.getlist('pdf_file')
                    # Filter out empty files
                    pdf_files = [f for f in pdf_files if f and f.filename]
                    
                    if not pdf_files:
                        flash('Please upload at least one PDF file.', 'danger')
                        return render_template('research/create.html', form=form)
                    
                    # Validate file sizes
                    max_size = 25 * 1024 * 1024  # 25 MB per file
                    max_total_size = 100 * 1024 * 1024  # 100 MB total
                    total_size = 0
                    
                    for pdf_file in pdf_files:
                        pdf_file.seek(0, 2)  # Seek to end
                        size = pdf_file.tell()
                        pdf_file.seek(0)  # Reset to beginning
                        total_size += size
                        
                        if size > max_size:
                            flash(f'File "{pdf_file.filename}" exceeds 25MB limit. Current size: {size / (1024*1024):.2f} MB', 'danger')
                            return render_template('research/create.html', form=form)
                    
                    if total_size > max_total_size:
                        flash(f'Total size of all files exceeds 100MB limit. Current total: {total_size / (1024*1024):.2f} MB', 'danger')
                        return render_template('research/create.html', form=form)
                    
                    # Process each PDF file
                    results = []
                    success_count = 0
                    duplicate_count = 0
                    error_count = 0
                    
                    for pdf_file in pdf_files:
                        if not pdf_file:
                            continue
                        
                        pdf_filename = secure_filename(pdf_file.filename)
                        pdf_data = pdf_file.read()
                        
                        if len(pdf_data) == 0:
                            results.append({
                                'filename': pdf_filename,
                                'status': 'error',
                                'message': 'The uploaded PDF file is empty.',
                                'brief_id': None
                            })
                            error_count += 1
                            continue
                        
                        # Check for duplicates
                        is_duplicate, duplicate_brief, duplicate_reason = ResearchBrief.check_duplicate(
                            pdf_filename, pdf_data
                        )
                        
                        if is_duplicate:
                            results.append({
                                'filename': pdf_filename,
                                'status': 'duplicate',
                                'message': f'Duplicate detected: {duplicate_reason}',
                                'brief_id': duplicate_brief.id if duplicate_brief else None
                            })
                            duplicate_count += 1
                            current_app.logger.info(f"Duplicate PDF detected: {pdf_filename} by {current_user.username}")
                            continue
                        
                        # Process the brief
                        brief_data, error = process_research_brief(
                            source_text=None,
                            pdf_data=pdf_data,
                            pdf_filename=pdf_filename
                        )
                        
                        if error:
                            results.append({
                                'filename': pdf_filename,
                                'status': 'error',
                                'message': error,
                                'brief_id': None
                            })
                            error_count += 1
                            current_app.logger.error(f"Error generating research brief for {pdf_filename}: {error}")
                            continue
                        
                        # Validate brief_data exists and has required fields
                        if not brief_data:
                            results.append({
                                'filename': pdf_filename,
                                'status': 'error',
                                'message': 'No data returned from AI service.',
                                'brief_id': None
                            })
                            error_count += 1
                            current_app.logger.error(f"process_research_brief returned None for {pdf_filename}")
                            continue
                        
                        # Validate required fields exist
                        required_fields = ['title', 'citation', 'summary', 'source_text']
                        missing_fields = [field for field in required_fields if field not in brief_data]
                        if missing_fields:
                            results.append({
                                'filename': pdf_filename,
                                'status': 'error',
                                'message': f'Missing required fields: {", ".join(missing_fields)}',
                                'brief_id': None
                            })
                            error_count += 1
                            current_app.logger.error(f"Missing required fields in brief_data for {pdf_filename}: {missing_fields}")
                            continue
                        
                        # Calculate content hash for storage
                        content_hash = calculate_pdf_hash(pdf_data)
                        
                        # Create the research brief record
                        new_brief, db_error = ResearchBrief.safe_create(
                            user_id=current_user.id,
                            title=brief_data['title'],
                            citation=brief_data['citation'],
                            summary=brief_data['summary'],
                            source_text=brief_data['source_text'],
                            pdf_filename=pdf_filename,
                            pdf_data=pdf_data,
                            content_hash=content_hash,
                            source_type='pdf',
                            model_name=brief_data.get('model_name')
                        )
                        
                        if db_error:
                            results.append({
                                'filename': pdf_filename,
                                'status': 'error',
                                'message': f'Error saving brief: {db_error}',
                                'brief_id': None
                            })
                            error_count += 1
                            current_app.logger.error(f"Error saving brief for {pdf_filename}: {db_error}")
                            continue
                        
                        # Add tags if provided
                        if form.tags.data:
                            add_tags_to_brief(new_brief, form.tags.data)
                        
                        results.append({
                            'filename': pdf_filename,
                            'status': 'success',
                            'message': 'Research brief created successfully!',
                            'brief_id': new_brief.id
                        })
                        success_count += 1
                        current_app.logger.info(f"Research brief {new_brief.id} created from {pdf_filename} by {current_user.username}")
                    
                    # Prepare flash messages and results for template
                    if success_count > 0:
                        flash(f'Successfully processed {success_count} PDF(s)!', 'success')
                    if duplicate_count > 0:
                        flash(f'Found {duplicate_count} duplicate PDF(s) that were skipped.', 'warning')
                    if error_count > 0:
                        flash(f'Failed to process {error_count} PDF(s).', 'danger')
                    
                    # If only one file and it succeeded, redirect to view page
                    if len(results) == 1 and results[0]['status'] == 'success':
                        return redirect(url_for('research_view', id=results[0]['brief_id']))
                    
                    # Otherwise, show results page
                    return render_template('research/create.html', form=form, batch_results=results)
            
            return render_template('research/create.html', form=form)
            
        except Exception as e:
            import traceback
            current_app.logger.error(f"Unexpected error in research create: {str(e)}")
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            flash(f'An unexpected error occurred while creating the research brief: {str(e)}', 'danger')
            return render_template('research/create.html', form=form)
    
    @app.route('/research/<int:id>')
    @login_required
    def research_view(id):
        """View an individual research brief"""
        try:
            brief = ResearchBrief.find_by_id_and_user(id, current_user.id)
            
            if not brief:
                flash('Research brief not found or you do not have permission to view it.', 'danger')
                return redirect(url_for('research_list'))
            
            current_app.logger.info(f"Research brief {id} viewed by {current_user.username}")
            return render_template('research/view.html', brief=brief)
            
        except Exception as e:
            current_app.logger.error(f"Error viewing research brief {id}: {str(e)}")
            flash('An error occurred while loading the research brief.', 'danger')
            return redirect(url_for('research_list'))
    
    @app.route('/research/<int:id>/edit', methods=['GET', 'POST'])
    @login_required
    def research_edit(id):
        """Edit a research brief"""
        brief = ResearchBrief.find_by_id_and_user(id, current_user.id)
        
        if not brief:
            flash('Research brief not found or you do not have permission to edit it.', 'danger')
            return redirect(url_for('research_list'))
        
        form = EditBriefForm(obj=brief)
        
        # Populate tags field with current tags
        if request.method == 'GET':
            current_tags = brief.get_tag_names()
            form.tags.data = ', '.join(current_tags)
        
        try:
            if form.validate_on_submit():
                # Update basic fields
                success, error = brief.safe_update(
                    title=form.title.data.strip(),
                    citation=form.citation.data.strip(),
                    summary=form.summary.data.strip(),
                    url=form.url.data.strip() if form.url.data else None
                )
                
                if error:
                    flash(f'Error updating brief: {error}', 'danger')
                else:
                    # Handle tags update
                    try:
                        # Parse tag input (comma-separated names)
                        tag_input = form.tags.data.strip() if form.tags.data else ''
                        
                        # Get current tag names
                        current_tag_names = set(brief.get_tag_names())
                        
                        # Parse new tags (normalize: lowercase, strip)
                        new_tag_names = set()
                        if tag_input:
                            new_tag_names = {tag.strip().lower() for tag in tag_input.split(',') if tag.strip()}
                        
                        # Tags to add (in new but not in current)
                        tags_to_add = new_tag_names - current_tag_names
                        for tag_name in tags_to_add:
                            brief.add_tag(tag_name)
                        
                        # Tags to remove (in current but not in new)
                        tags_to_remove = current_tag_names - new_tag_names
                        for tag_name in tags_to_remove:
                            brief.remove_tag(tag_name)
                        
                    except Exception as tag_error:
                        current_app.logger.error(f"Error updating tags for brief {id}: {str(tag_error)}")
                        flash('Brief updated but there was an error updating tags. Please try editing again.', 'warning')
                    
                    flash('Research brief updated successfully!', 'success')
                    current_app.logger.info(f"Research brief {id} updated by {current_user.username}")
                    return redirect(url_for('research_view', id=brief.id))
            
            return render_template('research/edit.html', form=form, brief=brief)
            
        except Exception as e:
            current_app.logger.error(f"Error editing research brief {id}: {str(e)}")
            flash('An error occurred while updating the research brief.', 'danger')
            return render_template('research/edit.html', form=form, brief=brief)
    
    @app.route('/research/<int:id>/delete', methods=['POST'])
    @login_required
    def research_delete(id):
        """Delete a research brief"""
        brief = ResearchBrief.find_by_id_and_user(id, current_user.id)
        
        if not brief:
            flash('Research brief not found or you do not have permission to delete it.', 'danger')
            return redirect(url_for('research_list'))
        
        try:
            success, error = brief.safe_delete()
            
            if error:
                flash(f'Error deleting brief: {error}', 'danger')
            else:
                flash('Research brief deleted successfully!', 'success')
                current_app.logger.info(f"Research brief {id} deleted by {current_user.username}")
            
            return redirect(url_for('research_list'))
            
        except Exception as e:
            current_app.logger.error(f"Error deleting research brief {id}: {str(e)}")
            flash('An error occurred while deleting the research brief.', 'danger')
            return redirect(url_for('research_list'))
    
    @app.route('/research/<int:id>/download')
    @login_required
    def research_download(id):
        """Download the original PDF if available"""
        brief = ResearchBrief.find_by_id_and_user(id, current_user.id)
        
        if not brief:
            flash('Research brief not found or you do not have permission to access it.', 'danger')
            return redirect(url_for('research_list'))
        
        if not brief.pdf_data or brief.source_type != 'pdf':
            flash('No PDF file available for this brief.', 'danger')
            return redirect(url_for('research_view', id=id))
        
        try:
            # Create a file-like object from the binary data
            pdf_file = BytesIO(brief.pdf_data)
            
            # Determine filename
            filename = brief.pdf_filename or f'research_brief_{brief.id}.pdf'
            
            current_app.logger.info(f"PDF downloaded for research brief {id} by {current_user.username}")
            return send_file(
                pdf_file,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
            
        except Exception as e:
            current_app.logger.error(f"Error downloading PDF for research brief {id}: {str(e)}")
            flash('An error occurred while downloading the PDF.', 'danger')
            return redirect(url_for('research_view', id=id))
    
    @app.route('/research/by-tags')
    @login_required
    def research_by_tags():
        """Show all research briefs grouped by tag"""
        try:
            # Get all tags that have at least one brief
            all_tags = Tag.get_all_tags()
            
            # Group briefs by tag for the current user
            tags_with_briefs = []
            for tag in all_tags:
                # Get all briefs for this user that have this tag
                briefs = ResearchBrief.query.filter_by(user_id=current_user.id)\
                    .join(ResearchBrief.tags)\
                    .filter(Tag.id == tag.id)\
                    .order_by(ResearchBrief.created_at.desc())\
                    .all()
                
                if briefs:  # Only include tags that have briefs for this user
                    tags_with_briefs.append((tag, briefs))
            
            # Sort by tag name
            tags_with_briefs.sort(key=lambda x: x[0].name)
            
            # Also get briefs with no tags
            # Get all brief IDs that have tags
            from sqlalchemy import distinct, select
            from flask_app.models.research_brief import research_brief_tags
            
            # Get all brief IDs that have at least one tag
            brief_ids_with_tags = db.session.query(distinct(research_brief_tags.c.research_brief_id)).all()
            brief_ids_with_tags_set = {row[0] for row in brief_ids_with_tags}
            
            # Get all user's briefs
            all_user_briefs = ResearchBrief.query.filter_by(user_id=current_user.id).all()
            
            # Filter to get only those without tags
            briefs_without_tags = [brief for brief in all_user_briefs if brief.id not in brief_ids_with_tags_set]
            briefs_without_tags.sort(key=lambda x: x.created_at, reverse=True)
            
            current_app.logger.info(f"Research briefs by tags viewed by {current_user.username}")
            return render_template('research/by_tags.html', 
                                 tags_with_briefs=tags_with_briefs,
                                 briefs_without_tags=briefs_without_tags)
            
        except Exception as e:
            current_app.logger.error(f"Error in research by tags: {str(e)}")
            import traceback
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            flash('An error occurred while loading briefs by tags.', 'danger')
            return render_template('research/by_tags.html', tags_with_briefs=[], briefs_without_tags=[])
