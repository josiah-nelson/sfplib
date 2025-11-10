# GitHub Workflows

This directory contains GitHub Actions workflows for building, testing, and releasing the SFPLiberate Home Assistant add-on.

## Workflows

### CI (`ci.yaml`)

**Trigger:** Pull requests and pushes to `main` and `develop` branches

Runs continuous integration checks including:

- **YAML Linting:** Validates YAML files using yamllint
- **Markdown Linting:** Validates markdown files using markdownlint
- **Python Linting:** Runs ruff, mypy, and black on the backend code
- **Python Tests:** Runs pytest test suite
- **Add-on Validation:** Validates Home Assistant add-on configuration

### Builder (`builder.yaml`)

**Trigger:** Pull requests and pushes to `main` branch (when add-on files change), manual dispatch

Builds multi-architecture Docker images for the add-on:

- **Architectures:** aarch64, amd64, armhf, armv7
- **Build System:** Docker Buildx with QEMU emulation
- **Build Context:** Repository root (allows access to backend code)
- **Registry:** GitHub Container Registry (ghcr.io)
- **Caching:** GitHub Actions cache for faster builds
- **Behavior:**
  - PRs: Builds images but doesn't push
  - Main branch: Builds and pushes images
  - Manual: Can be triggered via workflow_dispatch

**Technical Details:**
- Uses matrix strategy to build all architectures in parallel
- Extracts version from `sfplib/config.yaml`
- Maps architectures to Docker platforms (e.g., aarch64 → linux/arm64)
- Tags images as both `:version` and `:latest`
- Builds from repo root to access both `backend/` and `sfplib/` directories

### Release (`release.yaml`)

**Trigger:** GitHub releases (published), manual dispatch

Builds and publishes release versions of the add-on:

- **Architectures:** All supported architectures (aarch64, amd64, armhf, armv7)
- **Versioning:** Uses release tag (strips 'v' prefix) or manual input
- **Registry:** Pushes to GitHub Container Registry
- **Summary:** Creates a comprehensive release summary with image details
- **Always Pushes:** Unlike builder workflow, always pushes images to registry

## Setup Requirements

### Secrets

No additional secrets are required. The workflows use the built-in `GITHUB_TOKEN` for:
- Pushing images to GitHub Container Registry
- Creating releases

### Permissions

Ensure the repository has the following permissions configured:

1. **Actions:** Read and write permissions
2. **Packages:** Read and write permissions (for GHCR)

Configure these in: Repository Settings → Actions → General → Workflow permissions

### Container Registry

Images are pushed to: `ghcr.io/<username>/sfplib-<arch>:<version>`

Make sure container images are set to public or accessible to Home Assistant users.

## Usage

### Running CI Checks Locally

Before pushing, you can run checks locally:

```bash
# YAML linting
yamllint -c sfplib/.yamllint sfplib/

# Markdown linting
markdownlint -c sfplib/.mdlrc '**/*.md'

# Python linting
cd backend
poetry run ruff check .
poetry run mypy .
poetry run black --check .

# Python tests
poetry run pytest -v
```

### Creating a Release

1. Update version in `sfplib/config.yaml`
2. Update `sfplib/CHANGELOG.md`
3. Commit changes
4. Create a GitHub release with tag matching the version (e.g., `v0.1.0`)
5. The release workflow will automatically build and push images

### Manual Build

You can manually trigger the builder workflow:

1. Go to Actions → Builder
2. Click "Run workflow"
3. Select branch and run

## Multi-Architecture Builds

The workflows use Docker Buildx with QEMU emulation to build images for multiple architectures:

- **aarch64:** ARM 64-bit (Raspberry Pi 4, etc.)
- **amd64:** Intel/AMD 64-bit
- **armhf:** ARM 32-bit hard float (older Raspberry Pi)
- **armv7:** ARM 32-bit v7 (Raspberry Pi 3, etc.)

Each architecture is built in parallel as a matrix job for faster execution.

## Troubleshooting

### Build Failures

- Check Docker build logs in the Actions tab
- Verify Dockerfile syntax
- Ensure all dependencies are correctly specified
- Test local builds: `docker buildx build --platform linux/amd64 -f sfplib/Dockerfile .`

### Linting Failures

- Run linters locally before pushing
- Check configuration files (.yamllint, .mdlrc, pyproject.toml)
- Fix issues and commit

### Permission Errors

- Verify workflow permissions in repository settings
- Ensure GITHUB_TOKEN has package write permissions
- Check GHCR access and visibility settings

## Dependencies

These workflows use:

- `actions/checkout@v4`
- `actions/setup-python@v5`
- `docker/setup-qemu-action@v3`
- `docker/setup-buildx-action@v3`
- `docker/login-action@v3`
- `home-assistant/builder@master`
- `home-assistant/actions/helpers/info@master`
- `snok/install-poetry@v1`

Dependabot is configured to keep these actions up to date.
