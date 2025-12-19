# flask_app/routes/todo.py

from flask import flash, redirect, render_template, url_for, request, current_app, jsonify
from flask_login import login_required, current_user
from flask_app.models import Todo, SubTask, Event, Goal, db
from flask_app.forms import TodoForm, EventForm

def register_todo_routes(app):
    """Register todo routes"""
    
    @app.route('/todos', methods=['GET', 'POST'])
    @login_required
    def todo_list():
        """Display todo list page with form (single-page view)"""
        form = TodoForm()
        
        # Populate goal choices
        goals = Goal.find_by_user(current_user.id)
        form.goal_id.choices = [(0, 'No goal')] + [(g.id, g.title) for g in goals]
        
        try:
            # Handle form submission
            if form.validate_on_submit():
                goal_id = None
                if hasattr(form, 'goal_id') and form.goal_id.data and form.goal_id.data != 0:
                    goal_id = form.goal_id.data
                
                new_todo, error = Todo.safe_create(
                    user_id=current_user.id,
                    description=form.description.data.strip(),
                    due_date=form.due_date.data,
                    goal_id=goal_id
                )
                
                if error:
                    flash(f'Error creating todo: {error}', 'danger')
                else:
                    flash('Todo added successfully!', 'success')
                    current_app.logger.info(f"Todo {new_todo.id} created by {current_user.username}")
                    return redirect(url_for('todo_list'))
            
            # Get all todos for the current user with their subtasks
            todos = Todo.find_by_user(current_user.id)
            # Load subtasks for each todo
            for todo in todos:
                todo.subtasks_list = SubTask.find_by_todo(todo.id)
            
            # Get goals for dropdown
            goals = Goal.find_by_user(current_user.id)
            
            # Get events split by status
            upcoming_events = Event.find_upcoming_by_user(current_user.id)
            past_unprocessed_events = Event.find_past_unprocessed_by_user(current_user.id)
            processed_events = Event.find_processed_by_user(current_user.id, limit=20)
            
            current_app.logger.info(f"Todo list accessed by {current_user.username}")
            return render_template('todo/list.html', 
                                 form=form, 
                                 todos=todos,
                                 goals=goals,
                                 upcoming_events=upcoming_events,
                                 past_unprocessed_events=past_unprocessed_events,
                                 processed_events=processed_events)
            
        except Exception as e:
            current_app.logger.error(f"Error in todo list: {str(e)}")
            flash('An error occurred while loading your todos.', 'danger')
            todos = Todo.find_by_user(current_user.id) if current_user.is_authenticated else []
            # Load subtasks for each todo
            for todo in todos:
                todo.subtasks_list = SubTask.find_by_todo(todo.id)
            goals = Goal.find_by_user(current_user.id) if current_user.is_authenticated else []
            upcoming_events = Event.find_upcoming_by_user(current_user.id) if current_user.is_authenticated else []
            past_unprocessed_events = Event.find_past_unprocessed_by_user(current_user.id) if current_user.is_authenticated else []
            processed_events = Event.find_processed_by_user(current_user.id, limit=20) if current_user.is_authenticated else []
            return render_template('todo/list.html', 
                                 form=form, 
                                 todos=todos,
                                 goals=goals,
                                 upcoming_events=upcoming_events,
                                 past_unprocessed_events=past_unprocessed_events,
                                 processed_events=processed_events)
    
    @app.route('/todos/<int:id>/toggle', methods=['POST'])
    @login_required
    def todo_toggle(id):
        """Toggle completion status (returns JSON for AJAX)"""
        todo = Todo.find_by_id_and_user(id, current_user.id)
        
        if not todo:
            return jsonify({'success': False, 'error': 'Todo not found'}), 404
        
        try:
            # Toggle completed status
            new_status = not todo.completed
            success, error = todo.safe_update(completed=new_status)
            
            if error:
                current_app.logger.error(f"Error toggling todo {id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Todo {id} toggled to {new_status} by {current_user.username}")
            return jsonify({
                'success': True,
                'completed': new_status
            })
            
        except Exception as e:
            current_app.logger.error(f"Error toggling todo {id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/todos/<int:id>/delete', methods=['POST'])
    @login_required
    def todo_delete(id):
        """Delete todo (returns JSON for AJAX)"""
        todo = Todo.find_by_id_and_user(id, current_user.id)
        
        if not todo:
            return jsonify({'success': False, 'error': 'Todo not found'}), 404
        
        try:
            success, error = todo.safe_delete()
            
            if error:
                current_app.logger.error(f"Error deleting todo {id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Todo {id} deleted by {current_user.username}")
            return jsonify({'success': True})
            
        except Exception as e:
            current_app.logger.error(f"Error deleting todo {id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/todos/<int:todo_id>/subtasks/create', methods=['POST'])
    @login_required
    def subtask_create(todo_id):
        """Create a new subtask (returns JSON for AJAX)"""
        # Verify todo belongs to user
        todo = Todo.find_by_id_and_user(todo_id, current_user.id)
        if not todo:
            return jsonify({'success': False, 'error': 'Todo not found'}), 404
        
        try:
            data = request.get_json()
            description = data.get('description', '').strip()
            
            if not description:
                return jsonify({'success': False, 'error': 'Description is required'}), 400
            
            # Get max order for subtasks in this todo
            from sqlalchemy import func
            max_order = db.session.query(func.max(SubTask.order)).filter_by(todo_id=todo_id).scalar() or 0
            
            new_subtask, error = SubTask.safe_create(
                todo_id=todo_id,
                description=description,
                order=max_order + 1
            )
            
            if error:
                current_app.logger.error(f"Error creating subtask for todo {todo_id}: {error}")
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
            current_app.logger.error(f"Error creating subtask for todo {todo_id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/todos/<int:todo_id>/subtasks/<int:subtask_id>/toggle', methods=['POST'])
    @login_required
    def subtask_toggle(todo_id, subtask_id):
        """Toggle subtask completion status (returns JSON for AJAX)"""
        # Verify todo belongs to user
        todo = Todo.find_by_id_and_user(todo_id, current_user.id)
        if not todo:
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
    
    @app.route('/todos/<int:todo_id>/subtasks/<int:subtask_id>/delete', methods=['POST'])
    @login_required
    def subtask_delete(todo_id, subtask_id):
        """Delete subtask (returns JSON for AJAX)"""
        # Verify todo belongs to user
        todo = Todo.find_by_id_and_user(todo_id, current_user.id)
        if not todo:
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
    
    @app.route('/events/create', methods=['POST'])
    @login_required
    def event_create():
        """Create a new event (returns JSON for AJAX)"""
        try:
            data = request.get_json()
            description = data.get('description', '').strip()
            event_date_str = data.get('event_date', '')
            notes = data.get('notes', '').strip() if data.get('notes') else None
            
            if not description:
                return jsonify({'success': False, 'error': 'Description is required'}), 400
            
            if not event_date_str:
                return jsonify({'success': False, 'error': 'Date is required'}), 400
            
            # Parse date string (expecting YYYY-MM-DD format)
            from datetime import datetime
            try:
                event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid date format'}), 400
            
            new_event, error = Event.safe_create(
                user_id=current_user.id,
                description=description,
                event_date=event_date,
                notes=notes,
                processed=False  # Explicitly set to ensure events are not auto-processed
            )
            
            if error:
                current_app.logger.error(f"Error creating event: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Event {new_event.id} created by {current_user.username}")
            return jsonify({
                'success': True,
                'event': {
                    'id': new_event.id,
                    'description': new_event.description,
                    'event_date': new_event.event_date.strftime('%Y-%m-%d'),
                    'notes': new_event.notes or ''
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"Error creating event: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/events/<int:id>/update', methods=['POST'])
    @login_required
    def event_update(id):
        """Update an event (returns JSON for AJAX)"""
        event = Event.find_by_id_and_user(id, current_user.id)
        
        if not event:
            return jsonify({'success': False, 'error': 'Event not found'}), 404
        
        try:
            data = request.get_json()
            description = data.get('description', '').strip()
            event_date_str = data.get('event_date', '')
            notes = data.get('notes', '').strip() if data.get('notes') else None
            
            if not description:
                return jsonify({'success': False, 'error': 'Description is required'}), 400
            
            if not event_date_str:
                return jsonify({'success': False, 'error': 'Date is required'}), 400
            
            # Parse date string
            from datetime import datetime
            try:
                event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid date format'}), 400
            
            success, error = event.safe_update(
                description=description,
                event_date=event_date,
                notes=notes
            )
            
            if error:
                current_app.logger.error(f"Error updating event {id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Event {id} updated by {current_user.username}")
            
            # Return full event data including processed state
            event_data = {
                'id': event.id,
                'description': event.description,
                'event_date': event.event_date.strftime('%Y-%m-%d'),
                'notes': event.notes or '',
                'processed': event.processed,
                'outcome': event.outcome,
                'outcome_reason': event.outcome_reason or '',
                'outcome_notes': event.outcome_notes or '',
                'processed_at': event.processed_at.strftime('%Y-%m-%d %H:%M') if event.processed_at else None
            }
            
            return jsonify({
                'success': True,
                'event': event_data
            })
            
        except Exception as e:
            current_app.logger.error(f"Error updating event {id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/events/<int:id>/delete', methods=['POST'])
    @login_required
    def event_delete(id):
        """Delete event (returns JSON for AJAX)"""
        event = Event.find_by_id_and_user(id, current_user.id)
        
        if not event:
            return jsonify({'success': False, 'error': 'Event not found'}), 404
        
        try:
            success, error = event.safe_delete()
            
            if error:
                current_app.logger.error(f"Error deleting event {id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            current_app.logger.info(f"Event {id} deleted by {current_user.username}")
            return jsonify({'success': True})
            
        except Exception as e:
            current_app.logger.error(f"Error deleting event {id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/events/<int:id>/process', methods=['POST'])
    @login_required
    def event_process(id):
        """Process a past event (returns JSON for AJAX)"""
        event = Event.find_by_id_and_user(id, current_user.id)
        
        if not event:
            return jsonify({'success': False, 'error': 'Event not found'}), 404
        
        if event.processed:
            return jsonify({'success': False, 'error': 'Event already processed'}), 400
        
        try:
            data = request.get_json()
            outcome = data.get('outcome', '').strip()
            
            if outcome not in ['did_not_happen', 'happened', 'happened_with_notes']:
                return jsonify({'success': False, 'error': 'Invalid outcome'}), 400
            
            from datetime import datetime, timezone
            
            # Prepare update fields
            update_fields = {
                'processed': True,
                'processed_at': datetime.now(timezone.utc),
                'outcome': outcome
            }
            
            # Add outcome-specific fields
            if outcome == 'did_not_happen':
                update_fields['outcome_reason'] = data.get('reason', '').strip() or None
            elif outcome == 'happened_with_notes':
                notes_html = data.get('notes', '').strip() or None
                if notes_html:
                    # Sanitize HTML notes
                    from flask_app.utils.html_sanitizer import sanitize_html
                    notes_html = sanitize_html(notes_html)
                    if not notes_html or notes_html.strip() in ['<p><br></p>', '<p></p>']:
                        notes_html = None
                update_fields['outcome_notes'] = notes_html
            
            # Update event
            success, error = event.safe_update(**update_fields)
            
            if error:
                current_app.logger.error(f"Error processing event {id}: {error}")
                return jsonify({'success': False, 'error': error}), 500
            
            # Handle follow-up todos if provided
            follow_ups_created = 0
            follow_ups_text = data.get('follow_ups', '').strip()
            
            if outcome == 'happened_with_notes' and follow_ups_text:
                # Split by newlines and create todos
                follow_up_lines = [line.strip() for line in follow_ups_text.split('\n') if line.strip()]
                
                for follow_up_desc in follow_up_lines:
                    if follow_up_desc:
                        new_todo, todo_error = Todo.safe_create(
                            user_id=current_user.id,
                            description=follow_up_desc,
                            due_date=None
                        )
                        if not todo_error:
                            follow_ups_created += 1
                        else:
                            current_app.logger.warning(f"Error creating follow-up todo: {todo_error}")
            
            current_app.logger.info(f"Event {id} processed by {current_user.username} with outcome {outcome}, {follow_ups_created} follow-ups created")
            
            return jsonify({
                'success': True,
                'event': {
                    'id': event.id,
                    'description': event.description,
                    'event_date': event.event_date.strftime('%Y-%m-%d'),
                    'processed': event.processed,
                    'outcome': event.outcome,
                    'outcome_reason': event.outcome_reason,
                    'outcome_notes': event.outcome_notes,
                    'processed_at': event.processed_at.strftime('%Y-%m-%d %H:%M:%S') if event.processed_at else None
                },
                'follow_ups_created': follow_ups_created
            })
            
        except Exception as e:
            current_app.logger.error(f"Error processing event {id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

