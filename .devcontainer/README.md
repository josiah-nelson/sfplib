# Development Container Setup

This directory contains the configuration for developing SFPLiberate in a containerized environment, supporting both local VS Code development and GitHub Codespaces.

## Quick Start

### GitHub Codespaces

1. Click the "Code" button on GitHub
2. Select "Codespaces" tab
3. Click "Create codespace on main"
4. Wait for the environment to build (first time takes ~5 minutes, subsequent starts are faster with prebuilds)
5. Run the "Start Home Assistant" task (Terminal → Run Task)
6. Access Home Assistant at the forwarded port (check PORTS tab)

### Local Development with VS Code

#### Prerequisites

- Docker Desktop installed and running
- VS Code with "Dev Containers" extension installed

#### Setup

1. Open this repository in VS Code
2. When prompted, click "Reopen in Container"
   - Or use Command Palette: "Dev Containers: Reopen in Container"
3. Wait for the container to build and start
4. The setup script will automatically install dependencies
5. Run the "Start Home Assistant" task to launch the supervisor

## What's Included

### Home Assistant Environment

- Full Home Assistant Supervisor environment
- Automatic add-on discovery from the `/sfplib` directory
- Access to Home Assistant at `http://localhost:7123`

### Development Tools

- **Python 3.12** with Poetry package manager
- **Linting & Formatting:**
  - Ruff (fast Python linter)
  - Mypy (type checking)
  - Black (code formatting)
  - Prettier (YAML/JSON/Markdown formatting)
  - ShellCheck (shell script linting)
  - yamllint (YAML linting)
  - markdownlint (Markdown linting)

### VS Code Extensions

Pre-installed extensions for optimal development experience:
- Python language support with Pylance
- Black formatter
- Ruff linter
- YAML support
- Markdown linting
- Docker support
- ShellCheck

### Debugging Support

Launch configurations included for:
- FastAPI backend debugging
- Pytest test debugging
- Current file debugging

## Available Tasks

Access tasks via: **Terminal → Run Task**

- **Start Home Assistant**: Launch the HA Supervisor for add-on testing
- **Install Python Dependencies**: Reinstall backend dependencies
- **Run Python Tests**: Execute pytest test suite
- **Run Python Linters**: Run ruff, mypy, and black checks
- **Format Python Code**: Auto-format backend code with black
- **Build Add-on (amd64)**: Build Docker image locally
- **Validate Add-on Config**: Check config.yaml syntax

## Directory Structure

```
.devcontainer/
├── devcontainer.json    # Container configuration
├── setup.sh             # Post-create setup script
└── README.md            # This file

.vscode/
├── tasks.json           # VS Code tasks
├── launch.json          # Debug configurations
├── settings.json        # Workspace settings
└── extensions.json      # Recommended extensions
```

## Development Workflow

### 1. Making Changes to the Add-on

1. Edit files in `/sfplib` directory
2. Changes are automatically mounted to the HA Supervisor
3. Restart the add-on to apply changes

### 2. Backend Development

```bash
cd backend

# Install dependencies
poetry install

# Run tests
poetry run pytest -v

# Lint code
poetry run ruff check .
poetry run mypy .

# Format code
poetry run black .
```

### 3. Testing the Add-on

1. Start Home Assistant (Run Task → Start Home Assistant)
2. Open http://localhost:7123
3. Complete onboarding
4. Go to Settings → Add-ons → Add-on Store
5. Find "SFPLiberate" under "Local Add-ons"
6. Install and start the add-on

### 4. Debugging

- Use the debug configurations in the Run panel (Ctrl+Shift+D)
- Set breakpoints in Python files
- Launch "Python: FastAPI Backend" to debug the backend server

## Port Forwarding

| Port | Service | Access |
|------|---------|--------|
| 7123 | Home Assistant UI | http://localhost:7123 |
| 7357 | HA Supervisor API | http://localhost:7357 |
| 80   | Add-on (when running) | Proxied through HA |

In Codespaces, these ports are automatically forwarded and accessible via the PORTS tab.

## Troubleshooting

### Container won't start

- Ensure Docker Desktop is running (local only)
- Check Docker has enough resources (4GB+ RAM recommended)
- Try rebuilding: Command Palette → "Dev Containers: Rebuild Container"

### Poetry install fails

- Clear cache: `poetry cache clear pypi --all`
- Try manual install: `cd backend && poetry install`

### Home Assistant won't start

- Check Docker-in-Docker is working: `docker ps`
- View supervisor logs: Check the task output
- Restart the container

### Add-on not visible in HA

- Verify `/sfplib` directory exists and is mounted
- Check add-on config.yaml is valid
- Refresh the add-on store page

### Port already in use

- Stop any local HA instances
- Check for conflicting Docker containers: `docker ps`
- Change port mapping in devcontainer.json if needed

## Performance Tips

### Local Development

- Use Docker Desktop with at least 4GB RAM
- Enable file sharing for the workspace directory
- Consider using WSL2 on Windows for better performance

### Codespaces

- Choose at least 4-core machine type for better performance
- Prebuilds significantly speed up startup time
- Stop codespaces when not in use to conserve minutes

## Additional Resources

- [Home Assistant Add-on Development](https://developers.home-assistant.io/docs/add-ons/)
- [Home Assistant Devcontainer Guide](https://developers.home-assistant.io/docs/add-ons/testing/)
- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [GitHub Codespaces](https://docs.github.com/en/codespaces)

## Getting Help

- Check the main [README.md](../README.md) for project-specific documentation
- Review [DOCS.md](../sfplib/DOCS.md) for add-on configuration details
- Open an issue on GitHub for bugs or feature requests
