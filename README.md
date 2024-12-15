# Jeza Ynput Dev Workspace

This workspace provides a streamlined development environment for YNPUT and ZED projects. It combines essential tools and automated tasks in ZED editor, allowing you to manage multiple repositories efficiently while focusing on creation rather than setup. The integrated environment simplifies your development workflow with centralized commands and tools.

## Features and Benefits

This workspace offers several key features to enhance your development experience:

- Built-in commands for cloning essential YNPUT repositories
- Simplified addon packaging and upload process
- Dependency management using UV package installer

## Environment Setup

The workspace uses UV for Python dependency management. To set up your environment:

```bash
pip install uv
```

After installing UV, you should be able just simply run the tasks from the command palette. Dependencies will be installed automatically when needed.

# Features and Usage

## Available Tasks

The workspace includes several pre-configured tasks that can be executed through ZED's command palette. To run any task:

1. Open the command palette (Cmd/Ctrl + Shift + P)
2. Type `tasks: spawn`
3. Select the desired task from the list

### Available Tasks:

#### 1. Git Clone all repositories
**Purpose:** Clones all essential YNPUT repositories to your local workspace.
**Usage:**
- Select "Git Clone all repositories" from the tasks menu
- The task will execute in the current terminal
- Repositories will be cloned to your workspace directory

#### 2. Upload addon to server and restart
**Purpose:** Uploads the current file to the addon folder and restarts the service.
**Usage:**
- Active file must be an addon-related file
- Select "Upload addon to server and restart" from the tasks menu
- Supports debug mode with the `--debug` flag (enabled by default)
- Task will execute in the current terminal
- Terminal will auto-hide on successful completion

#### 3. Update AYON server
**Purpose:** Updates the AYON server using Docker Compose.
**Usage:**
- Select "Update AYON server" from the tasks menu
- Task will:
  1. Change directory to `ayon-docker`
  2. Pull the latest server image
  3. Restart the server container
- Executes in a new terminal window
- Terminal will auto-hide on successful completion

## Task Execution Behavior

All tasks are configured with the following common behaviors:
- Concurrent runs are not allowed (tasks will wait for previous instances to complete)
- Task output is visible in the terminal
- Summary and command output are shown by default
- Tasks use the system's default shell configuration

> [!TIP]
> Tasks with `hide: "on_success"` will automatically hide the terminal tab when completed successfully, keeping your workspace clean and organized.

> [!NOTE]
> Some features may require initial setup and configuration of your development environment.
