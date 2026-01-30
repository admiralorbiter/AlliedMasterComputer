# Todo & Events

Complete guide to the Todo and Events system for managing tasks, subtasks, and scheduled events.

## Overview

The Todo & Events system provides a unified interface for managing:

- **Todos**: Action items with optional due dates and goal linking
- **Subtasks**: Break down todos into smaller steps
- **Events**: Scheduled occurrences that require post-event processing

All features are accessible from a single-page interface at `/todos`.

---

## Features

### Todos

| Feature | Description |
|---------|-------------|
| **Create Todos** | Description, optional due date, optional goal link |
| **Toggle Completion** | Mark todos done/undone |
| **Delete Todos** | Remove with all subtasks |
| **Goal Linking** | Associate with goals for progress tracking |
| **Project Linking** | Create from project context |

### Subtasks

| Feature | Description |
|---------|-------------|
| **Create Subtasks** | Break todos into steps |
| **Toggle Completion** | Mark subtasks done independently |
| **Delete Subtasks** | Remove individual subtasks |
| **Auto-Ordering** | Subtasks maintain order |

### Events

| Feature | Description |
|---------|-------------|
| **Create Events** | Description, date, optional notes |
| **Update Events** | Edit details before processing |
| **Delete Events** | Remove events |
| **Event Processing** | Handle past events with outcomes |
| **Follow-up Todos** | Create todos from event outcomes |

### Event Processing Outcomes

When an event date passes, you must process it with one of three outcomes:

| Outcome | Description |
|---------|-------------|
| **Didn't Happen** | Record why it didn't occur |
| **Happened** | Simply mark as complete |
| **Happened with Notes** | Record notes and create follow-up todos |

---

## Getting Started

### Creating Your First Todo

1. Navigate to `/todos`
2. Fill in the form:
   - **Description**: What needs to be done (required)
   - **Due Date**: Optional deadline
   - **Goal**: Optional goal to link to
3. Click "Add Todo"

### Creating Your First Event

1. Navigate to `/todos`
2. Find the Events section
3. Fill in:
   - **Description**: Event name (required)
   - **Date**: When it occurs (required)
   - **Notes**: Optional additional info
4. Click "Add Event"

---

## Usage Guide

### Managing Todos

**View All Todos**:
- Navigate to `/todos`
- See all todos with completion status
- Subtasks are shown under each todo

**Toggle Completion**:
- Click the checkbox to mark done/undone
- Visual feedback shows completed status

**Add Subtasks**:
1. Find the todo
2. Click "Add Subtask"
3. Enter subtask description
4. Subtask appears under the todo

**Link to Goals**:
- When creating a todo, select a goal from the dropdown
- Todo contributes to goal progress
- Create goals first in `/goals`

### Managing Events

**View Events**:
Events are split into three sections:
1. **Upcoming**: Future events (not yet occurred)
2. **Past Unprocessed**: Events that happened but need processing
3. **Processed**: Recently processed events (limit 20)

**Edit an Event**:
1. Click edit on the event
2. Update description, date, or notes
3. Save changes

**Process Past Events**:
When an event date passes:
1. Find it in "Past Unprocessed"
2. Click "Process"
3. Choose outcome:
   - **Didn't Happen**: Enter reason
   - **Happened**: Mark as complete
   - **Happened with Notes**: Add notes and follow-up todos
4. Follow-up todos are created automatically

### Single-Page Interface

The `/todos` page combines everything:
- Todo creation form at top
- Todo list with subtasks
- Events section with all three categories
- AJAX-powered for smooth interaction (no page reloads)

---

## Technical Details

### Database Models

**Todo** (`todos` table):

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `user_id` | Integer | Foreign key to users |
| `description` | Text | Todo description (required) |
| `due_date` | Date | Optional deadline |
| `completed` | Boolean | Completion status |
| `goal_id` | Integer | Optional foreign key to goals |
| `project_id` | Integer | Optional foreign key to projects |

**SubTask** (`subtasks` table):

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `todo_id` | Integer | Foreign key to todos |
| `description` | String(500) | Subtask description (required) |
| `completed` | Boolean | Completion status |
| `order` | Integer | Display order |

**Event** (`events` table):

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `user_id` | Integer | Foreign key to users |
| `description` | String(500) | Event description (required) |
| `event_date` | Date | Event date (required) |
| `notes` | Text | Optional notes |
| `processed` | Boolean | Whether event has been processed |
| `processed_at` | DateTime | When it was processed |
| `outcome` | String(50) | 'did_not_happen', 'happened', 'happened_with_notes' |
| `outcome_reason` | Text | Reason if didn't happen |
| `outcome_notes` | Text | Notes if happened with notes |

### API Endpoints

#### Todos

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/todos` | GET | Todo/Events page (HTML) |
| `/todos` | POST | Create todo (form submit) |
| `/todos/<id>/toggle` | POST | Toggle completion (JSON) |
| `/todos/<id>/delete` | POST | Delete todo (JSON) |

#### Subtasks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/todos/<todo_id>/subtasks/create` | POST | Create subtask (JSON) |
| `/todos/<todo_id>/subtasks/<id>/toggle` | POST | Toggle subtask (JSON) |
| `/todos/<todo_id>/subtasks/<id>/delete` | POST | Delete subtask (JSON) |

#### Events

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/events/create` | POST | Create event (JSON) |
| `/events/<id>/update` | POST | Update event (JSON) |
| `/events/<id>/delete` | POST | Delete event (JSON) |
| `/events/<id>/process` | POST | Process past event (JSON) |

### Relationships

```
Todo
├── User (owner)
├── Goal (optional)
├── Project (optional)
└── SubTasks (one-to-many, cascade delete)

Event
└── User (owner)
```

### Data Integrity

- **Cascade Delete**: Deleting a todo removes all subtasks
- **User Isolation**: Users only see their own data
- **Goal/Project SET NULL**: If goal or project is deleted, todo remains (unlinked)
- **HTML Sanitization**: Event notes are sanitized for security

---

## Event Processing Workflow

```
Create Event → Date Passes → Event Moves to "Past Unprocessed"
                                    ↓
                              Process Event
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
              Didn't Happen    Happened    Happened with Notes
                    ↓               ↓               ↓
              Save Reason    Mark Done    Save Notes + Create Todos
                    ↓               ↓               ↓
                    └───────────────┼───────────────┘
                                    ↓
                        Move to "Processed" Section
```

---

## Form Validation

### Todo Form

| Field | Rules |
|-------|-------|
| Description | Required, max 2000 characters |
| Due Date | Optional, valid date format |
| Goal | Optional, must be valid goal ID |

### Event Form

| Field | Rules |
|-------|-------|
| Description | Required, max 500 characters |
| Event Date | Required, valid date format (YYYY-MM-DD) |
| Notes | Optional, max 2000 characters |

---

## Integration with Other Features

### Goals

- Todos can link to goals for progress tracking
- Create goals first in `/goals`
- Goal links persist if goal is not deleted

### Projects

- Todos can be created from project detail view
- Project-linked todos show in project context
- Links persist if project is not deleted

---

## Best Practices

1. **Break Down Tasks**: Use subtasks for complex todos
2. **Set Due Dates**: Helps prioritize work
3. **Link to Goals**: Connect todos to larger objectives
4. **Process Events Promptly**: Don't let past events pile up
5. **Use Follow-ups**: Create todos from event outcomes for action items
6. **Add Event Notes**: Document meeting outcomes while fresh

---

## Troubleshooting

### Todo not saving

- Ensure description is provided (required)
- Check for any error messages

### Subtask not appearing

- Verify the parent todo exists
- Refresh the page if needed

### Event processing fails

- Ensure you select an outcome
- For "Didn't Happen", reason is optional
- For "Happened with Notes", notes are optional

### Can't link to goal

- Create goals first in `/goals`
- Goals dropdown shows all available goals

---

## Related Documentation

- [Goals](goals.md) - Creating goals to link todos
- [Projects](projects.md) - Project-based todos
- [Features Overview](FEATURES.md) - All features
- [Architecture Overview](ARCHITECTURE.md) - System architecture
