# flask_app/routes/projects.py

from flask import flash, redirect, url_for, request, current_app, jsonify
from flask_login import login_required, current_user
from flask_app.models import Project, db
from flask_app.forms import ProjectForm

def register_projects_routes(app):
    """Register project routes"""
    
    @app.route('/projects', methods=['GET'])
    @login_required
    def projects_list():
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

