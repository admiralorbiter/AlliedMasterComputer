# flask_app/routes/projects.py

from flask import flash, redirect, url_for, request, current_app, jsonify, render_template
from flask_login import login_required, current_user
from flask_app.models import Project, ProjectNote, ProjectLink, ResearchBrief, Todo, SubTask, db
from flask_app.forms import ProjectForm, ProjectNoteForm, ProjectLinkForm

def register_projects_routes(app):
    """Register project routes"""
    
    # JSON endpoint for backward compatibility (used by goals sidebar)
    @app.route('/projects/json', methods=['GET'])
    @login_required
    def projects_list_json():
        """Get list of projects (returns JSON for AJAX)"""
        try:
            projects = Project.find_by_user(current_user.id)
            return jsonify({
                'success': True,
                'projects': [
                    {
                        'id': p.id,
                        'name': p.name,
                        'description': p.description or ''
                    }
                    for p in projects
                ]
            })
        except Exception as e:
            current_app.logger.error(f"Error getting projects list: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # Main projects list page
    @app.route('/projects', methods=['GET', 'POST'])
    @login_required
    def projects_list():
        """Display projects list page"""
        form = ProjectForm()
        
        if form.validate_on_submit():
            new_project, error = Project.safe_create(
                user_id=current_user.id,
                name=form.name.data.strip(),
                description=form.description.data.strip() if form.description.data else None
            )
            
            if error:
                flash(f'Error creating project: {error}', 'danger')
            else:
                flash('Project created successfully!', 'success')
                current_app.logger.info(f"Project {new_project.id} created by {current_user.username}")
                return redirect(url_for('projects_list'))
        
        try:
            projects = Project.find_by_user(current_user.id)
            current_app.logger.info(f"Projects list accessed by {current_user.username}")
            return render_template('projects/list.html', form=form, projects=projects)
        except Exception as e:
            current_app.logger.error(f"Error in projects list: {str(e)}")
            flash('An error occurred while loading your projects.', 'danger')
            projects = Project.find_by_user(current_user.id) if current_user.is_authenticated else []
            return render_template('projects/list.html', form=form, projects=projects)
    
    # Project detail view
    @app.route('/projects/<int:id>', methods=['GET'])
    @login_required
    def project_view(id):
        """Display project detail view"""
        project = Project.find_by_id_and_user(id, current_user.id)
        
        if not project:
            flash('Project not found.', 'danger')
            return redirect(url_for('projects_list'))
        
        try:
            # Get related data
            notes = ProjectNote.find_by_project(id)
            links = ProjectLink.find_by_project(id)
            research_briefs = project.research_briefs.all()
            todos = Todo.find_by_project(id, current_user.id)
            
            # Load subtasks for each todo
            for todo in todos:
                todo.subtasks_list = SubTask.find_by_todo(todo.id)
            
            # Get all research briefs for linking (excluding already linked ones)
            all_briefs = ResearchBrief.find_by_user(current_user.id, page=1, per_page=1000)
            available_briefs = []
            if all_briefs:
                linked_brief_ids = {brief.id for brief in research_briefs}
                available_briefs = [brief for brief in all_briefs.items if brief.id not in linked_brief_ids]
            
            current_app.logger.info(f"Project {id} viewed by {current_user.username}")
            return render_template('projects/view.html', 
                                 project=project,
                                 notes=notes,
                                 links=links,
                                 research_briefs=research_briefs,
                                 todos=todos,
                                 available_briefs=available_briefs)
        except Exception as e:
            current_app.logger.error(f"Error viewing project {id}: {str(e)}")
            flash('An error occurred while loading the project.', 'danger')
            return redirect(url_for('projects_list'))
    
    # Create project (JSON endpoint for AJAX)
    @app.route('/projects/create', methods=['POST'])
    @login_required
    def project_create():
        """Create a new project (returns JSON for AJAX)"""
        try:
            data = request.get_json()
            name = data.get('name', '').strip()
            description = data.get('description', '').strip() if data.get('description') else None
            
            if not name:
                return jsonify({'success': False, 'error': 'Name is required'}), 400
            
            new_project, error = Project.safe_create(
                user_id=current_user.id,
                name=name,
                description=description
            )
            
            if error:
                current_app.logger.error(f"Error creating project: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Project {new_project.id} created by {current_user.username}")
            return jsonify({
                'success': True,
                'project': {
                    'id': new_project.id,
                    'name': new_project.name,
                    'description': new_project.description or ''
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"Error creating project: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/projects/<int:id>/update', methods=['POST'])
    @login_required
    def project_update(id):
        """Update a project (returns JSON for AJAX)"""
        project = Project.find_by_id_and_user(id, current_user.id)
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        try:
            data = request.get_json()
            name = data.get('name', '').strip()
            description = data.get('description', '').strip() if data.get('description') else None
            
            if not name:
                return jsonify({'success': False, 'error': 'Name is required'}), 400
            
            success, error = project.safe_update(
                name=name,
                description=description
            )
            
            if error:
                current_app.logger.error(f"Error updating project {id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Project {id} updated by {current_user.username}")
            return jsonify({
                'success': True,
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'description': project.description or ''
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"Error updating project {id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/projects/<int:id>/delete', methods=['POST'])
    @login_required
    def project_delete(id):
        """Delete a project (returns JSON for AJAX)"""
        project = Project.find_by_id_and_user(id, current_user.id)
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        try:
            success, error = project.safe_delete()
            
            if error:
                current_app.logger.error(f"Error deleting project {id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Project {id} deleted by {current_user.username}")
            return jsonify({'success': True})
            
        except Exception as e:
            current_app.logger.error(f"Error deleting project {id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # Notes routes
    @app.route('/projects/<int:id>/notes/create', methods=['POST'])
    @login_required
    def project_note_create(id):
        """Create a note for a project"""
        project = Project.find_by_id_and_user(id, current_user.id)
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        try:
            data = request.get_json()
            content = data.get('content', '').strip()
            
            if not content:
                return jsonify({'success': False, 'error': 'Note content is required'}), 400
            
            new_note, error = ProjectNote.safe_create(
                project_id=id,
                user_id=current_user.id,
                content=content
            )
            
            if error:
                current_app.logger.error(f"Error creating note: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Note {new_note.id} created for project {id} by {current_user.username}")
            return jsonify({
                'success': True,
                'note': {
                    'id': new_note.id,
                    'content': new_note.content,
                    'created_at': new_note.created_at.isoformat()
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"Error creating note: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/projects/<int:id>/notes/<int:note_id>/update', methods=['POST'])
    @login_required
    def project_note_update(id, note_id):
        """Update a project note"""
        project = Project.find_by_id_and_user(id, current_user.id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        note = ProjectNote.find_by_id_and_user(note_id, current_user.id)
        if not note or note.project_id != id:
            return jsonify({'success': False, 'error': 'Note not found'}), 404
        
        try:
            data = request.get_json()
            content = data.get('content', '').strip()
            
            if not content:
                return jsonify({'success': False, 'error': 'Note content is required'}), 400
            
            success, error = note.safe_update(content=content)
            
            if error:
                current_app.logger.error(f"Error updating note {note_id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Note {note_id} updated by {current_user.username}")
            return jsonify({
                'success': True,
                'note': {
                    'id': note.id,
                    'content': note.content,
                    'updated_at': note.updated_at.isoformat()
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"Error updating note {note_id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/projects/<int:id>/notes/<int:note_id>/delete', methods=['POST'])
    @login_required
    def project_note_delete(id, note_id):
        """Delete a project note"""
        project = Project.find_by_id_and_user(id, current_user.id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        note = ProjectNote.find_by_id_and_user(note_id, current_user.id)
        if not note or note.project_id != id:
            return jsonify({'success': False, 'error': 'Note not found'}), 404
        
        try:
            success, error = note.safe_delete()
            
            if error:
                current_app.logger.error(f"Error deleting note {note_id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Note {note_id} deleted by {current_user.username}")
            return jsonify({'success': True})
            
        except Exception as e:
            current_app.logger.error(f"Error deleting note {note_id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # Links routes
    @app.route('/projects/<int:id>/links/create', methods=['POST'])
    @login_required
    def project_link_create(id):
        """Create a link for a project"""
        project = Project.find_by_id_and_user(id, current_user.id)
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        try:
            data = request.get_json()
            title = data.get('title', '').strip()
            url = data.get('url', '').strip()
            
            if not title:
                return jsonify({'success': False, 'error': 'Link title is required'}), 400
            if not url:
                return jsonify({'success': False, 'error': 'URL is required'}), 400
            
            new_link, error = ProjectLink.safe_create(
                project_id=id,
                user_id=current_user.id,
                title=title,
                url=url
            )
            
            if error:
                current_app.logger.error(f"Error creating link: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Link {new_link.id} created for project {id} by {current_user.username}")
            return jsonify({
                'success': True,
                'link': {
                    'id': new_link.id,
                    'title': new_link.title,
                    'url': new_link.url,
                    'created_at': new_link.created_at.isoformat()
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"Error creating link: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/projects/<int:id>/links/<int:link_id>/update', methods=['POST'])
    @login_required
    def project_link_update(id, link_id):
        """Update a project link"""
        project = Project.find_by_id_and_user(id, current_user.id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        link = ProjectLink.find_by_id_and_user(link_id, current_user.id)
        if not link or link.project_id != id:
            return jsonify({'success': False, 'error': 'Link not found'}), 404
        
        try:
            data = request.get_json()
            title = data.get('title', '').strip()
            url = data.get('url', '').strip()
            
            if not title:
                return jsonify({'success': False, 'error': 'Link title is required'}), 400
            if not url:
                return jsonify({'success': False, 'error': 'URL is required'}), 400
            
            success, error = link.safe_update(title=title, url=url)
            
            if error:
                current_app.logger.error(f"Error updating link {link_id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Link {link_id} updated by {current_user.username}")
            return jsonify({
                'success': True,
                'link': {
                    'id': link.id,
                    'title': link.title,
                    'url': link.url,
                    'updated_at': link.updated_at.isoformat()
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"Error updating link {link_id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/projects/<int:id>/links/<int:link_id>/delete', methods=['POST'])
    @login_required
    def project_link_delete(id, link_id):
        """Delete a project link"""
        project = Project.find_by_id_and_user(id, current_user.id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        link = ProjectLink.find_by_id_and_user(link_id, current_user.id)
        if not link or link.project_id != id:
            return jsonify({'success': False, 'error': 'Link not found'}), 404
        
        try:
            success, error = link.safe_delete()
            
            if error:
                current_app.logger.error(f"Error deleting link {link_id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Link {link_id} deleted by {current_user.username}")
            return jsonify({'success': True})
            
        except Exception as e:
            current_app.logger.error(f"Error deleting link {link_id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # Research briefs routes
    @app.route('/projects/<int:id>/research-briefs/link', methods=['POST'])
    @login_required
    def project_research_brief_link(id):
        """Link a research brief to a project"""
        project = Project.find_by_id_and_user(id, current_user.id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        try:
            data = request.get_json()
            brief_id = data.get('brief_id')
            
            if not brief_id:
                return jsonify({'success': False, 'error': 'Brief ID is required'}), 400
            
            brief = ResearchBrief.find_by_id_and_user(brief_id, current_user.id)
            if not brief:
                return jsonify({'success': False, 'error': 'Research brief not found'}), 404
            
            # Check if already linked
            if brief in project.research_briefs.all():
                return jsonify({'success': False, 'error': 'Research brief already linked to this project'}), 400
            
            project.research_briefs.append(brief)
            db.session.commit()
            
            current_app.logger.info(f"Research brief {brief_id} linked to project {id} by {current_user.username}")
            return jsonify({
                'success': True,
                'brief': {
                    'id': brief.id,
                    'title': brief.title
                }
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error linking research brief: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/projects/<int:id>/research-briefs/<int:brief_id>/unlink', methods=['POST'])
    @login_required
    def project_research_brief_unlink(id, brief_id):
        """Unlink a research brief from a project"""
        project = Project.find_by_id_and_user(id, current_user.id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        try:
            brief = ResearchBrief.find_by_id_and_user(brief_id, current_user.id)
            if not brief:
                return jsonify({'success': False, 'error': 'Research brief not found'}), 404
            
            if brief not in project.research_briefs.all():
                return jsonify({'success': False, 'error': 'Research brief not linked to this project'}), 400
            
            project.research_briefs.remove(brief)
            db.session.commit()
            
            current_app.logger.info(f"Research brief {brief_id} unlinked from project {id} by {current_user.username}")
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error unlinking research brief: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # Todos routes
    @app.route('/projects/<int:id>/todos/create', methods=['POST'])
    @login_required
    def project_todo_create(id):
        """Create a todo for a project"""
        project = Project.find_by_id_and_user(id, current_user.id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        try:
            data = request.get_json()
            description = data.get('description', '').strip()
            due_date_str = data.get('due_date', '').strip() if data.get('due_date') else None
            
            if not description:
                return jsonify({'success': False, 'error': 'Description is required'}), 400
            
            due_date = None
            if due_date_str:
                from datetime import datetime
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'success': False, 'error': 'Invalid date format'}), 400
            
            new_todo, error = Todo.safe_create(
                user_id=current_user.id,
                description=description,
                due_date=due_date,
                project_id=id
            )
            
            if error:
                current_app.logger.error(f"Error creating todo: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Todo {new_todo.id} created for project {id} by {current_user.username}")
            return jsonify({
                'success': True,
                'todo': {
                    'id': new_todo.id,
                    'description': new_todo.description,
                    'due_date': new_todo.due_date.strftime('%Y-%m-%d') if new_todo.due_date else None,
                    'completed': new_todo.completed
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"Error creating todo: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/projects/<int:id>/todos/<int:todo_id>/update', methods=['POST'])
    @login_required
    def project_todo_update(id, todo_id):
        """Update a project todo"""
        project = Project.find_by_id_and_user(id, current_user.id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        todo = Todo.find_by_id_and_user(todo_id, current_user.id)
        if not todo or todo.project_id != id:
            return jsonify({'success': False, 'error': 'Todo not found'}), 404
        
        try:
            data = request.get_json()
            description = data.get('description', '').strip()
            due_date_str = data.get('due_date', '').strip() if data.get('due_date') else None
            
            if not description:
                return jsonify({'success': False, 'error': 'Description is required'}), 400
            
            due_date = None
            if due_date_str:
                from datetime import datetime
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'success': False, 'error': 'Invalid date format'}), 400
            
            success, error = todo.safe_update(description=description, due_date=due_date)
            
            if error:
                current_app.logger.error(f"Error updating todo {todo_id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Todo {todo_id} updated by {current_user.username}")
            return jsonify({
                'success': True,
                'todo': {
                    'id': todo.id,
                    'description': todo.description,
                    'due_date': todo.due_date.strftime('%Y-%m-%d') if todo.due_date else None,
                    'completed': todo.completed
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"Error updating todo {todo_id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/projects/<int:id>/todos/<int:todo_id>/delete', methods=['POST'])
    @login_required
    def project_todo_delete(id, todo_id):
        """Delete a project todo"""
        project = Project.find_by_id_and_user(id, current_user.id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        todo = Todo.find_by_id_and_user(todo_id, current_user.id)
        if not todo or todo.project_id != id:
            return jsonify({'success': False, 'error': 'Todo not found'}), 404
        
        try:
            success, error = todo.safe_delete()
            
            if error:
                current_app.logger.error(f"Error deleting todo {todo_id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Todo {todo_id} deleted by {current_user.username}")
            return jsonify({'success': True})
            
        except Exception as e:
            current_app.logger.error(f"Error deleting todo {todo_id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/projects/<int:id>/todos/<int:todo_id>/toggle', methods=['POST'])
    @login_required
    def project_todo_toggle(id, todo_id):
        """Toggle todo completion status"""
        project = Project.find_by_id_and_user(id, current_user.id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        todo = Todo.find_by_id_and_user(todo_id, current_user.id)
        if not todo or todo.project_id != id:
            return jsonify({'success': False, 'error': 'Todo not found'}), 404
        
        try:
            new_status = not todo.completed
            success, error = todo.safe_update(completed=new_status)
            
            if error:
                current_app.logger.error(f"Error toggling todo {todo_id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Todo {todo_id} toggled to {new_status} by {current_user.username}")
            return jsonify({
                'success': True,
                'completed': new_status
            })
            
        except Exception as e:
            current_app.logger.error(f"Error toggling todo {todo_id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/projects/<int:id>/todos/<int:todo_id>/subtasks/create', methods=['POST'])
    @login_required
    def project_subtask_create(id, todo_id):
        """Create a subtask for a project todo"""
        project = Project.find_by_id_and_user(id, current_user.id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        todo = Todo.find_by_id_and_user(todo_id, current_user.id)
        if not todo or todo.project_id != id:
            return jsonify({'success': False, 'error': 'Todo not found'}), 404
        
        try:
            data = request.get_json()
            description = data.get('description', '').strip()
            
            if not description:
                return jsonify({'success': False, 'error': 'Description is required'}), 400
            
            from sqlalchemy import func
            max_order = db.session.query(func.max(SubTask.order)).filter_by(todo_id=todo_id).scalar() or 0
            
            new_subtask, error = SubTask.safe_create(
                todo_id=todo_id,
                description=description,
                order=max_order + 1
            )
            
            if error:
                current_app.logger.error(f"Error creating subtask: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Subtask {new_subtask.id} created for todo {todo_id} by {current_user.username}")
            return jsonify({
                'success': True,
                'subtask': {
                    'id': new_subtask.id,
                    'description': new_subtask.description,
                    'completed': new_subtask.completed,
                    'order': new_subtask.order
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"Error creating subtask: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/projects/<int:id>/todos/<int:todo_id>/subtasks/<int:subtask_id>/update', methods=['POST'])
    @login_required
    def project_subtask_update(id, todo_id, subtask_id):
        """Update a subtask"""
        project = Project.find_by_id_and_user(id, current_user.id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        todo = Todo.find_by_id_and_user(todo_id, current_user.id)
        if not todo or todo.project_id != id:
            return jsonify({'success': False, 'error': 'Todo not found'}), 404
        
        subtask = SubTask.query.filter_by(id=subtask_id, todo_id=todo_id).first()
        if not subtask:
            return jsonify({'success': False, 'error': 'Subtask not found'}), 404
        
        try:
            data = request.get_json()
            description = data.get('description', '').strip()
            
            if not description:
                return jsonify({'success': False, 'error': 'Description is required'}), 400
            
            success, error = subtask.safe_update(description=description)
            
            if error:
                current_app.logger.error(f"Error updating subtask {subtask_id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Subtask {subtask_id} updated by {current_user.username}")
            return jsonify({
                'success': True,
                'subtask': {
                    'id': subtask.id,
                    'description': subtask.description,
                    'completed': subtask.completed
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"Error updating subtask {subtask_id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/projects/<int:id>/todos/<int:todo_id>/subtasks/<int:subtask_id>/delete', methods=['POST'])
    @login_required
    def project_subtask_delete(id, todo_id, subtask_id):
        """Delete a subtask"""
        project = Project.find_by_id_and_user(id, current_user.id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        todo = Todo.find_by_id_and_user(todo_id, current_user.id)
        if not todo or todo.project_id != id:
            return jsonify({'success': False, 'error': 'Todo not found'}), 404
        
        subtask = SubTask.query.filter_by(id=subtask_id, todo_id=todo_id).first()
        if not subtask:
            return jsonify({'success': False, 'error': 'Subtask not found'}), 404
        
        try:
            success, error = subtask.safe_delete()
            
            if error:
                current_app.logger.error(f"Error deleting subtask {subtask_id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Subtask {subtask_id} deleted by {current_user.username}")
            return jsonify({'success': True})
            
        except Exception as e:
            current_app.logger.error(f"Error deleting subtask {subtask_id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/projects/<int:id>/todos/<int:todo_id>/subtasks/<int:subtask_id>/toggle', methods=['POST'])
    @login_required
    def project_subtask_toggle(id, todo_id, subtask_id):
        """Toggle subtask completion status"""
        project = Project.find_by_id_and_user(id, current_user.id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        todo = Todo.find_by_id_and_user(todo_id, current_user.id)
        if not todo or todo.project_id != id:
            return jsonify({'success': False, 'error': 'Todo not found'}), 404
        
        subtask = SubTask.query.filter_by(id=subtask_id, todo_id=todo_id).first()
        if not subtask:
            return jsonify({'success': False, 'error': 'Subtask not found'}), 404
        
        try:
            new_status = not subtask.completed
            success, error = subtask.safe_update(completed=new_status)
            
            if error:
                current_app.logger.error(f"Error toggling subtask {subtask_id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Subtask {subtask_id} toggled to {new_status} by {current_user.username}")
            return jsonify({
                'success': True,
                'completed': new_status
            })
            
        except Exception as e:
            current_app.logger.error(f"Error toggling subtask {subtask_id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
