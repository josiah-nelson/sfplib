# Contributing to SFPLiberate

Thank you for your interest in contributing to SFPLiberate! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, professional, and constructive in all interactions. We aim to maintain a welcoming community for everyone.

## Getting Started

### Prerequisites

- Git
- Docker Desktop (for local development)
- VS Code with Dev Containers extension (recommended)
- Or access to GitHub Codespaces

### Development Environment

We provide a fully configured development environment using devcontainers:

#### Option 1: GitHub Codespaces (Easiest)

1. Click "Code" → "Codespaces" → "Create codespace"
2. Wait for the environment to build
3. Start coding!

#### Option 2: Local Development

1. Clone the repository
2. Open in VS Code
3. Click "Reopen in Container" when prompted
4. Wait for setup to complete

See [`.devcontainer/README.md`](.devcontainer/README.md) for detailed setup instructions.

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates

### 2. Make Changes

Follow the project structure:
- **Backend code**: `backend/app/`
- **Frontend code**: `sfplib/rootfs/usr/share/sfplib/ui/`
- **Add-on config**: `sfplib/config.yaml`
- **Documentation**: `sfplib/DOCS.md`, `README.md`

### 3. Test Your Changes

#### Run Tests

```bash
cd backend
poetry run pytest -v
```

#### Run Linters

```bash
# Python
poetry run ruff check .
poetry run mypy .
poetry run black --check .

# YAML
yamllint -c sfplib/.yamllint sfplib/

# Markdown
markdownlint '**/*.md'
```

#### Format Code

```bash
cd backend
poetry run black .
```

#### Test in Home Assistant

1. Run task "Start Home Assistant"
2. Open http://localhost:7123
3. Install add-on from Local Add-ons
4. Test functionality

### 4. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git commit -m "Add feature: brief description

Longer description of what changed and why.
Fixes #123"
```

Commit message format:
- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and PRs

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a PR on GitHub:
1. Go to the repository on GitHub
2. Click "Pull requests" → "New pull request"
3. Select your branch
4. Fill out the PR template
5. Submit for review

## Code Style Guidelines

### Python

- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters (Black default)
- Use descriptive variable names
- Add docstrings to functions and classes

Example:
```python
async def get_module_by_id(
    module_id: int,
    db: AsyncSession
) -> Optional[Module]:
    """
    Retrieve a module by its ID.

    Args:
        module_id: The ID of the module to retrieve
        db: Database session

    Returns:
        The module if found, None otherwise
    """
    result = await db.execute(
        select(Module).where(Module.id == module_id)
    )
    return result.scalar_one_or_none()
```

### JavaScript/Alpine.js

- Use camelCase for variables and functions
- Use 2-space indentation
- Add comments for complex logic
- Keep functions small and focused

### YAML

- Use 2-space indentation
- Quote strings when needed
- Follow Home Assistant conventions
- Validate with yamllint

### Markdown

- Use reference-style links for readability
- Add blank lines between sections
- Use headers hierarchically
- Validate with markdownlint

## Testing Requirements

### Unit Tests

Required for:
- New features
- Bug fixes
- API endpoints
- Service functions

Example:
```python
import pytest
from app.services.module_service import ModuleService

@pytest.mark.asyncio
async def test_create_module(db_session):
    """Test module creation."""
    service = ModuleService(db_session)
    module = await service.create_module(
        name="Test Module",
        manufacturer="Test"
    )
    assert module.name == "Test Module"
```

### Integration Tests

Required for:
- Major features
- API integrations
- Database operations
- External service interactions

### Manual Testing

Always test:
- Add-on installation in HA
- Core functionality
- Error handling
- UI responsiveness

## Documentation

Update documentation when:
- Adding new features
- Changing configuration options
- Modifying API endpoints
- Updating dependencies

Files to update:
- `README.md` - Project overview
- `sfplib/DOCS.md` - Add-on documentation
- `sfplib/CHANGELOG.md` - Version history
- Code comments and docstrings

## Pull Request Process

### Before Submitting

- [ ] Code is tested and working
- [ ] All tests pass
- [ ] Code is formatted (Black, Prettier)
- [ ] No linting errors
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (if applicable)
- [ ] PR template is filled out

### Review Process

1. Automated checks run (CI/CD)
2. Code review by maintainers
3. Address feedback
4. Approval and merge

### CI/CD Checks

Your PR must pass:
- **Linting**: Python, YAML, Markdown
- **Tests**: Unit and integration tests
- **Build**: Multi-arch Docker builds
- **Security**: Dependency scanning, secret detection
- **Add-on validation**: Config schema validation

## Issue Reporting

### Bug Reports

Use the bug report template and include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Version information
- Logs (if applicable)

### Feature Requests

Use the feature request template and include:
- Problem statement
- Proposed solution
- Alternatives considered
- Willingness to implement

## Release Process

Maintainers will handle releases:

1. Update version in `sfplib/config.yaml`
2. Update `CHANGELOG.md`
3. Create GitHub release
4. CI/CD builds and publishes images
5. Announce in community

## Getting Help

- **Questions**: Open a discussion on GitHub
- **Bugs**: Open an issue with bug report template
- **Features**: Open an issue with feature request template
- **Security**: Email maintainers directly (see SECURITY.md)

## Recognition

Contributors will be:
- Listed in release notes
- Credited in CHANGELOG.md
- Appreciated in the community!

## Additional Resources

- [Home Assistant Add-on Development](https://developers.home-assistant.io/docs/add-ons/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Alpine.js Documentation](https://alpinejs.dev/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

Thank you for contributing to SFPLiberate! 🎉
