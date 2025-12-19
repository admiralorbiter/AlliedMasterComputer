# flask_app/routes/goals.py

from flask import flash, redirect, render_template, url_for, request, current_app, jsonify
from flask_login import login_required, current_user
from flask_app.models import Goal, Project, Todo, db
from flask_app.forms import GoalForm

def register_goals_routes(app):
    """Register goal routes"""
    
    @app.route('/goals', methods=['GET', 'POST'])
    @login_required
    def goals_list():
        """Display goals list page with form"""
        form = GoalForm()
        
        # Populate project choices
        projects = Project.find_by_user(current_user.id)
        form.project_id.choices = [(0, 'Select a project...')] + [(p.id, p.name) for p in projects]
        
        try:
            # Handle form submission
            if form.validate_on_submit():
                project_id = form.project_id.data if form.project_id.data and form.project_id.data != 0 else None
                
                # Validate project_id for project goals
                if form.goal_type.data == 'project' and not project_id:
                    flash('Project is required for project goals.', 'danger')
                else:
                    new_goal, error = Goal.safe_create(
                        user_id=current_user.id,
                        title=form.title.data.strip(),
                        description=form.description.data.strip() if form.description.data else None,
                        goal_type=form.goal_type.data,
                        project_id=project_id,
                        completed=False
                    )
                    
                    if error:
                        flash(f'Error creating goal: {error}', 'danger')
                    else:
                        flash('Goal added successfully!', 'success')
                        current_app.logger.info(f"Goal {new_goal.id} created by {current_user.username}")
                        return redirect(url_for('goals_list'))
            
            # Get filter type from query parameter
            filter_type = request.args.get('type', 'all')
            goal_type = None if filter_type == 'all' else filter_type
            
            # Get all goals for the current user
            goals = Goal.find_by_user(current_user.id, goal_type)
            
            # Load related data for each goal
            for goal in goals:
                # Count linked todos
                goal.todos_count = Todo.query.filter_by(goal_id=goal.id).count()
                # Get project name if applicable
                if goal.project_id and goal.project:
                    goal.project_name = goal.project.name
                else:
                    goal.project_name = None
            
            # Get all projects for the form
            all_projects = Project.find_by_user(current_user.id)
            
            current_app.logger.info(f"Goals list accessed by {current_user.username}")
            return render_template('goals/list.html', 
                                 form=form, 
                                 goals=goals,
                                 projects=all_projects,
                                 filter_type=filter_type)
            
        except Exception as e:
            current_app.logger.error(f"Error in goals list: {str(e)}")
            flash('An error occurred while loading your goals.', 'danger')
            goals = Goal.find_by_user(current_user.id) if current_user.is_authenticated else []
            all_projects = Project.find_by_user(current_user.id) if current_user.is_authenticated else []
            return render_template('goals/list.html', 
                                 form=form, 
                                 goals=goals,
                                 projects=all_projects,
                                 filter_type='all')
    
    @app.route('/goals/list', methods=['GET'])
    @login_required
    def goals_list_json():
        """Get list of goals (returns JSON for AJAX)"""
        try:
            goals = Goal.find_by_user(current_user.id)
            return jsonify({
                'success': True,
                'goals': [
                    {
                        'id': g.id,
                        'title': g.title,
                        'goal_type': g.goal_type
                    }
                    for g in goals
                ]
            })
        except Exception as e:
            current_app.logger.error(f"Error getting goals list: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/goals/<int:id>/toggle', methods=['POST'])
    @login_required
    def goal_toggle(id):
        """Toggle goal completion status (returns JSON for AJAX)"""
        goal = Goal.find_by_id_and_user(id, current_user.id)
        
        if not goal:
            return jsonify({'success': False, 'error': 'Goal not found'}), 404
        
        try:
            new_status = not goal.completed
            success, error = goal.safe_update(completed=new_status)
            
            if error:
                current_app.logger.error(f"Error toggling goal {id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Goal {id} toggled to {new_status} by {current_user.username}")
            return jsonify({
                'success': True,
                'completed': new_status
            })
            
        except Exception as e:
            current_app.logger.error(f"Error toggling goal {id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/goals/<int:id>/update', methods=['POST'])
    @login_required
    def goal_update(id):
        """Update a goal (returns JSON for AJAX)"""
        goal = Goal.find_by_id_and_user(id, current_user.id)
        
        if not goal:
            return jsonify({'success': False, 'error': 'Goal not found'}), 404
        
        try:
            data = request.get_json()
            title = data.get('title', '').strip()
            description = data.get('description', '').strip() if data.get('description') else None
            goal_type = data.get('goal_type', '').strip()
            project_id = data.get('project_id')
            
            if not title:
                return jsonify({'success': False, 'error': 'Title is required'}), 400
            
            if goal_type not in ['professional', 'personal', 'project']:
                return jsonify({'success': False, 'error': 'Invalid goal type'}), 400
            
            # Validate project_id for project goals
            if goal_type == 'project' and not project_id:
                return jsonify({'success': False, 'error': 'Project is required for project goals'}), 400
            
            # Set project_id to None if not a project goal
            if goal_type != 'project':
                project_id = None
            elif project_id == 0:
                project_id = None
            
            success, error = goal.safe_update(
                title=title,
                description=description,
                goal_type=goal_type,
                project_id=project_id
            )
            
            if error:
                current_app.logger.error(f"Error updating goal {id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Goal {id} updated by {current_user.username}")
            return jsonify({
                'success': True,
                'goal': {
                    'id': goal.id,
                    'title': goal.title,
                    'description': goal.description or '',
                    'goal_type': goal.goal_type,
                    'project_id': goal.project_id,
                    'completed': goal.completed
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"Error updating goal {id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/goals/<int:id>/delete', methods=['POST'])
    @login_required
    def goal_delete(id):
        """Delete a goal (returns JSON for AJAX)"""
        goal = Goal.find_by_id_and_user(id, current_user.id)
        
        if not goal:
            return jsonify({'success': False, 'error': 'Goal not found'}), 404
        
        try:
            success, error = goal.safe_delete()
            
            if error:
                current_app.logger.error(f"Error deleting goal {id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Goal {id} deleted by {current_user.username}")
            return jsonify({'success': True})
            
        except Exception as e:
            current_app.logger.error(f"Error deleting goal {id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

