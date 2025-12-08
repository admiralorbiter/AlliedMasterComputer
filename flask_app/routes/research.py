# flask_app/routes/research.py

from flask import flash, redirect, render_template, url_for, request, current_app, send_file, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask_app.models import ResearchBrief, db
from flask_app.forms import ResearchBriefForm, EditBriefForm
from flask_app.utils.openai_service import process_research_brief
from io import BytesIO
import os

def register_research_routes(app):
    """Register research brief routes"""
    
    @app.route('/research')
    @login_required
    def research_list():
        """List all research briefs for the current user"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 20
            
            briefs = ResearchBrief.find_by_user(current_user.id, page=page, per_page=per_page)
            
            if briefs is None:
                flash('An error occurred while loading your research briefs.', 'danger')
                briefs = ResearchBrief.query.filter_by(user_id=current_user.id).paginate(
                    page=page, per_page=per_page, error_out=False
                )
            
            current_app.logger.info(f"Research briefs list accessed by {current_user.username}")
            return render_template('research/list.html', briefs=briefs)
            
        except Exception as e:
            current_app.logger.error(f"Error in research list: {str(e)}")
            flash('An error occurred while loading your research briefs.', 'danger')
            return render_template('research/list.html', briefs=None)
    
    @app.route('/research/create', methods=['GET', 'POST'])
    @login_required
    def research_create():
        """Create a new research brief"""
        form = ResearchBriefForm()
        
        try:
            if form.validate_on_submit():
                source_text = None
                pdf_data = None
                pdf_filename = None
                
                # Handle PDF upload
                if form.source_type.data == 'pdf' and form.pdf_file.data:
                    pdf_file = form.pdf_file.data
                    pdf_filename = secure_filename(pdf_file.filename)
                    pdf_data = pdf_file.read()
                    
                    if len(pdf_data) == 0:
                        flash('The uploaded PDF file is empty.', 'danger')
                        return render_template('research/create.html', form=form)
                
                # Handle text input
                elif form.source_type.data == 'text' and form.source_text.data:
                    source_text = form.source_text.data.strip()
                
                # Process the brief
                brief_data, error = process_research_brief(
                    source_text=source_text,
                    pdf_data=pdf_data,
                    pdf_filename=pdf_filename
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
                    pdf_filename=pdf_filename,
                    pdf_data=pdf_data,
                    source_type=form.source_type.data,
                    model_name=brief_data.get('model_name')  # Store the model used
                )
                
                if db_error:
                    flash(f'Error saving brief: {db_error}', 'danger')
                    return render_template('research/create.html', form=form)
                
                flash('Research brief created successfully!', 'success')
                current_app.logger.info(f"Research brief {new_brief.id} created by {current_user.username}")
                return redirect(url_for('research_view', id=new_brief.id))
            
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
        
        try:
            if form.validate_on_submit():
                success, error = brief.safe_update(
                    title=form.title.data.strip(),
                    citation=form.citation.data.strip(),
                    summary=form.summary.data.strip()
                )
                
                if error:
                    flash(f'Error updating brief: {error}', 'danger')
                else:
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
