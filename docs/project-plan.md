# Simplified Flowstate Prototype

It needs to be an MVP, nothing more. FastAPI with SQLite, utilizing the built-in module, is sufficient. I need to have Google Calendar integration for demo purposes, along with SMTP support (which should be possible using Python's built-in functions). It'll also need to integrate with Grok's AI API's using Pydantic AI.

## Login

Login requests an email address and sends an access link to the specified email. The first time they log in, it creates an account for them. Auth links should be HMAC signatures with the email address to which they are being sent, which are then base64-encoded.

## Pages

### Home Page

The home page is just an email input with a "Login" button. Clicking it directs the user to a page that explains a login link has been sent to their email.

Once logged in, the home page shows all projects on the left, the next task that needs to be done in the center of the page, and at the bottom, the action text input.

The action text input and project list are always present once logged in. The action input is contextual to the current page, allowing actions based on what the user is seeing.

### Project Page

The project page will show all milestones with the highest priority task in the active milestone. If there's only the default milestone, the milestone page should be used.

### Milestone Page

The milestone page will show all tasks in the milestone.

## Features

- Projects
  - Project Milestones
    - Milestone due dates
    - Tasks
      - Task due dates
      - Task groups (for grouping dynamic tasks)
      - Task types
        - Create calendar event
        - Create email
        - Create task (for getting clarification from a user)
- Auto priority escalation
  - Milestone due dates impact task priority
- Automation
  - Reads emails in the background to create tasks
  - Monitors the users calendar to create tasks
  - Dynamically created tasks (calendar events/emails) should be grouped the user should be able to reject them as a whole
  - Send emails on a schedule/when tasks are completed
  - Create calendar events when tasks are completed
- Action input
  - Create a task
  - Search emails/calendar
  - Search tasks
  - Go to task/milestone/project
  - Delete tasks/milestones/projects
  - Complete task
  - Modify task/milestone/project
- User Settings
  - Email settings
  - Calendar authentication