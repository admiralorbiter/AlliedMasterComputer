# Projects

Complete guide to the Projects feature, including project management, notes, links, research brief integration, and project-scoped todos.

## Overview

Projects is a comprehensive project management system that serves as a central hub for organizing your work. Each project can contain:

- **Notes**: Rich text notes for documentation and ideas
- **Links**: URL bookmarks to external resources
- **Research Briefs**: Link AI-generated research to projects
- **Todos & Subtasks**: Task lists with nested task support

---

## Features

### Core Project Management

| Feature | Description |
|---------|-------------|
| **Create Projects** | Name and optional description |
| **View Projects** | List all projects with details |
| **Update Projects** | Edit name and description |
| **Delete Projects** | Remove with all associated data |
| **Detail View** | Single-page view with all project content |

### Project Notes

Attach rich text notes to document ideas, meeting notes, decisions, or any project-related information.

- Create, edit, and delete notes
- Notes ordered by creation date (newest first)
- Timestamps track creation and updates

### Project Links

Save and organize URLs related to your project:

- Add titled links with URLs
- Edit link titles and URLs
- Quick access to all project resources

### Research Brief Integration

Link your AI-generated research briefs to relevant projects:

- Link existing research briefs to a project
- Unlink when no longer relevant
- Cross-reference research from project view
- Browse available briefs to link from project detail page

### Project Todos

Create task lists within each project:

- **Todos**: Tasks with optional due dates
- **Subtasks**: Break complex tasks into steps
- **Toggle Completion**: Mark items done/undone
- **Full CRUD**: Create, update, delete tasks

---

## Getting Started

### Creating Your First Project

1. Navigate to `/projects`
2. Fill in the "Create Project" form:
   - **Name**: Required project title
   - **Description**: Optional longer description
3. Click "Create"
4. Your project appears in the list

### Project Workflow

```
Create Project → Add Notes/Links → Link Research → Create Todos → Track Progress
```

---

## Usage Guide

### Managing Projects

**View All Projects**:
1. Navigate to `/projects`
2. See all projects with names and descriptions
3. Click any project to view details

**View Project Details**:
1. Click a project from the list
2. See all notes, links, research briefs, and todos
3. Manage all project content from this page

**Edit a Project**:
1. Open the project detail view
2. Click the edit button
3. Update name or description
4. Save changes

**Delete a Project**:
1. Open the project detail view
2. Click delete
3. Confirm deletion
4. **Warning**: All notes, links, and todos are also deleted

### Working with Notes

**Add a Note**:
1. Open project detail view
2. Find the Notes section
3. Enter note content
4. Click "Add Note"

**Edit a Note**:
1. Click the edit icon on the note
2. Modify content
3. Save changes

**Delete a Note**:
1. Click the delete icon on the note
2. Confirm deletion

### Managing Links

**Add a Link**:
1. Open project detail view
2. Find the Links section
3. Enter:
   - **Title**: Descriptive name
   - **URL**: Full URL (including `https://`)
4. Click "Add Link"

**Edit a Link**:
1. Click edit on the link
2. Update title or URL
3. Save changes

### Linking Research Briefs

**Link a Research Brief**:
1. Open project detail view
2. Find the Research Briefs section
3. Select a brief from the dropdown
4. Click "Link"

**Unlink a Research Brief**:
1. Find the linked brief
2. Click "Unlink"
3. Brief remains in your library, just unlinked from this project

### Project Todos

**Create a Todo**:
1. Open project detail view
2. Find the Todos section
3. Enter description
4. Optionally set due date
5. Click "Add Todo"

**Toggle Completion**:
- Click the checkbox to mark done/undone

**Add Subtasks**:
1. Within a todo, click "Add Subtask"
2. Enter subtask description
3. Save

**Subtask Management**:
- Toggle subtask completion independently
- Edit or delete subtasks
- Subtasks ordered automatically

---

## Technical Details

### Database Models

**Project** (`projects` table):
| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `user_id` | Integer | Foreign key to users |
| `name` | String(200) | Project name (required) |
| `description` | Text | Optional description |
| `created_at` | DateTime | Auto-set on creation |
| `updated_at` | DateTime | Auto-updated on changes |

**ProjectNote** (`project_notes` table):
| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `project_id` | Integer | Foreign key to projects |
| `user_id` | Integer | Foreign key to users |
| `content` | Text | Note content (required) |

**ProjectLink** (`project_links` table):
| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `project_id` | Integer | Foreign key to projects |
| `user_id` | Integer | Foreign key to users |
| `title` | String(200) | Link title (required) |
| `url` | String(500) | URL (required) |

**project_research_briefs** (association table):
- Many-to-many relationship between projects and research briefs
- Indexed for efficient queries

### API Endpoints

#### Projects

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/projects` | GET | List all projects (HTML) |
| `/projects` | POST | Create project (form submit) |
| `/projects/json` | GET | List projects (JSON) |
| `/projects/create` | POST | Create project (JSON) |
| `/projects/<id>` | GET | View project detail |
| `/projects/<id>/update` | POST | Update project |
| `/projects/<id>/delete` | POST | Delete project |

#### Notes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/projects/<id>/notes/create` | POST | Create note |
| `/projects/<id>/notes/<note_id>/update` | POST | Update note |
| `/projects/<id>/notes/<note_id>/delete` | POST | Delete note |

#### Links

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/projects/<id>/links/create` | POST | Create link |
| `/projects/<id>/links/<link_id>/update` | POST | Update link |
| `/projects/<id>/links/<link_id>/delete` | POST | Delete link |

#### Research Briefs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/projects/<id>/research-briefs/link` | POST | Link brief to project |
| `/projects/<id>/research-briefs/<brief_id>/unlink` | POST | Unlink brief |

#### Todos & Subtasks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/projects/<id>/todos/create` | POST | Create todo |
| `/projects/<id>/todos/<todo_id>/update` | POST | Update todo |
| `/projects/<id>/todos/<todo_id>/delete` | POST | Delete todo |
| `/projects/<id>/todos/<todo_id>/toggle` | POST | Toggle completion |
| `/projects/<id>/todos/<todo_id>/subtasks/create` | POST | Create subtask |
| `/projects/<id>/todos/<todo_id>/subtasks/<sub_id>/update` | POST | Update subtask |
| `/projects/<id>/todos/<todo_id>/subtasks/<sub_id>/delete` | POST | Delete subtask |
| `/projects/<id>/todos/<todo_id>/subtasks/<sub_id>/toggle` | POST | Toggle subtask |

### Relationships

```
Project
├── User (owner)
├── Notes (one-to-many)
├── Links (one-to-many)
├── Research Briefs (many-to-many)
├── Todos (one-to-many)
│   └── Subtasks (one-to-many)
└── Goals (one-to-many, linked from Goals feature)
```

### Data Integrity

- **Cascade Delete**: Deleting a project removes all associated notes, links, and todos
- **User Isolation**: Users can only access their own projects
- **Referential Integrity**: Foreign keys enforce valid relationships

---

## Best Practices

1. **Use Descriptive Names**: Clear project names help with quick identification
2. **Add Descriptions**: Context helps when returning to old projects
3. **Organize with Notes**: Keep important decisions and ideas documented
4. **Link Research Early**: Connect relevant research briefs as you create them
5. **Break Down Work**: Use todos and subtasks for manageable chunks
6. **Save URLs**: Don't lose important resource links

---

## Integration with Other Features

### Goals

- Goals can be linked to projects (from the Goals feature)
- View related goals from project context

### Research Briefs

- Briefs created in `/research` can be linked to multiple projects
- Cross-reference research across project boundaries

### Todos

- Project todos appear in the project detail view
- For non-project todos, use the standalone `/todo` page

---

## Troubleshooting

### Project not appearing in list

- Refresh the page
- Check that you're logged in as the correct user
- Each user only sees their own projects

### Can't link research brief

- Ensure the brief exists and belongs to you
- Check that it's not already linked to the project

### Todos not saving

- Check for required fields (description is required)
- Verify date format if using due dates (YYYY-MM-DD)

---

## Related Documentation

- [Research Brief Generator](research-brief-generator.md) - Creating briefs to link
- [Features Overview](FEATURES.md) - All features
- [Architecture Overview](ARCHITECTURE.md) - System architecture
