# Goals

Complete guide to the Goals feature for tracking personal and professional objectives.

## Overview

Goals is a personal objective tracking system that helps you define, organize, and complete your goals. Goals can be categorized by type and optionally linked to projects for better organization.

---

## Features

### Goal Types

Track three categories of goals:

| Type | Description | Project Required |
|------|-------------|------------------|
| **Professional** | Career and work-related goals | No |
| **Personal** | Personal development and life goals | No |
| **Project** | Goals tied to a specific project | Yes |

### Core Features

| Feature | Description |
|---------|-------------|
| **Create Goals** | Title, description, type, optional project link |
| **Toggle Completion** | Mark goals complete/incomplete |
| **Filter by Type** | View all goals or filter by type |
| **Project Linking** | Link "project" type goals to projects |
| **Todo Integration** | Link todos to goals for task breakdown |
| **AJAX Interface** | Smooth interactions without page reloads |

---

## Getting Started

### Creating Your First Goal

1. Navigate to `/goals`
2. Fill in the goal form:
   - **Title**: What you want to achieve (required)
   - **Description**: Optional details
   - **Goal Type**: Professional, Personal, or Project
   - **Project**: Select if goal type is "Project"
3. Click "Add Goal"

### Goal Workflow

```
Define Goal → Break into Todos → Track Progress → Mark Complete
```

---

## Usage Guide

### Managing Goals

**View All Goals**:
1. Navigate to `/goals`
2. See all goals with status and type
3. Use filter tabs to view by type (All, Professional, Personal, Project)

**Create a Goal**:
1. Fill in the form at the top of the goals page
2. Select the appropriate type
3. Link to a project if it's a project goal
4. Click "Add Goal"

**Toggle Completion**:
- Click the checkbox to mark a goal complete or incomplete
- Completed goals show visual feedback

**Edit a Goal**:
1. Click the edit button on a goal
2. Update title, description, type, or project
3. Save changes

**Delete a Goal**:
1. Click delete on the goal
2. Confirm deletion
3. **Note**: Linked todos are not deleted (goal_id is set to null)

### Filtering Goals

Use the filter tabs to view:
- **All**: Every goal regardless of type
- **Professional**: Work and career goals only
- **Personal**: Personal development goals only
- **Project**: Project-linked goals only

### Linking to Projects

For project-type goals:
1. Create a project first (in `/projects`)
2. Create a goal with type "Project"
3. Select the target project from the dropdown
4. The goal will appear in project context

### Connecting Todos

Break goals into actionable tasks:
1. Create todos in `/todo`
2. When creating a todo, select a goal to link to
3. View linked todo count on each goal
4. Complete todos to make progress on goals

---

## Technical Details

### Database Model

**Goal** (`goals` table):

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `user_id` | Integer | Foreign key to users |
| `title` | String(200) | Goal title (required) |
| `description` | Text | Optional description |
| `goal_type` | String(20) | 'professional', 'personal', or 'project' |
| `project_id` | Integer | Optional foreign key to projects |
| `completed` | Boolean | Completion status (default: false) |
| `created_at` | DateTime | Auto-set on creation |
| `updated_at` | DateTime | Auto-updated on changes |

**Indexes**:
- `user_id` - Fast user queries
- `goal_type` - Fast type filtering
- `project_id` - Fast project lookups
- `completed` - Fast status filtering

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/goals` | GET | Goals list page (HTML) |
| `/goals` | POST | Create goal (form submit) |
| `/goals/list` | GET | Get goals (JSON) |
| `/goals/<id>/toggle` | POST | Toggle completion (JSON) |
| `/goals/<id>/update` | POST | Update goal (JSON) |
| `/goals/<id>/delete` | POST | Delete goal (JSON) |

### Relationships

```
Goal
├── User (owner)
├── Project (optional, for project-type goals)
└── Todos (one-to-many, reverse link)
```

### Data Integrity

- **User Isolation**: Users only see their own goals
- **Project Deletion**: When a project is deleted, goal's `project_id` becomes null (SET NULL)
- **Goal Deletion**: Linked todos have `goal_id` set to null (not deleted)

---

## Best Practices

1. **Use Clear Titles**: Make goals specific and measurable
2. **Add Descriptions**: Context helps when reviewing goals later
3. **Choose the Right Type**: Categorize properly for better filtering
4. **Link Projects**: Use project goals for project-related objectives
5. **Break Down with Todos**: Large goals should have actionable tasks
6. **Review Regularly**: Check your goals page to track progress

---

## Form Validation

| Field | Rules |
|-------|-------|
| Title | Required, max 200 characters |
| Description | Optional, max 2000 characters |
| Goal Type | Required (professional/personal/project) |
| Project | Required if goal type is "project" |

---

## Integration with Other Features

### Projects

- Project-type goals link to a specific project
- View related goals from project context
- Project deletion unlinks goals (doesn't delete them)

### Todos

- Todos can be linked to goals via `goal_id`
- Goals show count of linked todos
- Completing todos contributes to goal progress
- Create todos from `/todo` page with goal selection

---

## Troubleshooting

### Goal not saving

- Ensure title is provided (required)
- For project goals, make sure a project is selected

### Project dropdown empty

- Create projects first in `/projects`
- Ensure you have at least one project

### Can't link todo to goal

- Create the goal first
- Create todos from the `/todo` page
- Goals dropdown on todo form shows available goals

---

## Related Documentation

- [Projects](projects.md) - Creating projects for project-type goals
- [Features Overview](FEATURES.md) - All features
- [Architecture Overview](ARCHITECTURE.md) - System architecture
