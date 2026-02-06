# Docker Development Environment

This Docker environment provides a consistent development and testing environment for ngfw_pkgtools.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

### 1. Build the Docker image

```bash
make build
```

Or manually:
```bash
docker-compose -f docker-compose.dev.yml build
```

### 2. Start the development environment

```bash
make up
```

Or manually:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Access the container shell

```bash
make shell
```

Or manually:
```bash
docker-compose -f docker-compose.dev.yml exec ngfw-pkgtools-dev /bin/bash
```

## Running Scripts

Once inside the container shell, you can run any script:

```bash
# Example: Run create-branch.py
./create-branch.py --help

# Example: Run with specific parameters
./create-branch.py --branch ngfw-1.0 --product ngfw --simulate
```

## Running Tests

Run unit tests with coverage:

```bash
make test
```

Or manually:
```bash
docker-compose -f docker-compose.dev.yml exec ngfw-pkgtools-dev pytest -v --cov=lib --cov-report=term-missing
```

Run specific tests:
```bash
# Run specific test file
docker-compose -f docker-compose.dev.yml exec ngfw-pkgtools-dev pytest tests/test_repoinfo.py -v

# Run specific test
docker-compose -f docker-compose.dev.yml exec ngfw-pkgtools-dev pytest tests/test_repoinfo.py::TestRepositoryInfo -v
```

See [`tests/README.md`](tests/README.md) for more details on testing.

## Code Quality

### Format code

```bash
make format
```

### Run linter

```bash
make lint
```

## Git Configuration

If your scripts need to push to remote repositories, you may need to mount your git credentials:

1. Uncomment the volume mounts in `docker-compose.dev.yml`:
   ```yaml
   - ~/.gitconfig:/root/.gitconfig:ro
   - ~/.ssh:/root/.ssh:ro
   ```

2. Rebuild and restart:
   ```bash
   make down
   make build
   make up
   ```

## Installed Dependencies

The Docker image includes:

- **Python 3.7+** (from Debian Buster)
- **Git** - Version control
- **GitPython** - Python Git library
- **PyYAML** - YAML parsing
- **requests** - HTTP library
- **pytest** - Testing framework
- **pytest-cov** - Code coverage
- **ruff** - Python linter and formatter

## Cleanup

To stop and remove containers:

```bash
make down
```

To remove everything including the image:

```bash
make clean
```

## Directory Structure

- `/opt/untangle/ngfw_pkgtools` - Working directory inside container
- Volume mounted to your local directory for live code changes

## Troubleshooting

### Container won't start
```bash
docker-compose -f docker-compose.dev.yml logs
```

### Permission issues
The container runs as root. If you encounter permission issues with generated files, you may need to adjust ownership after running commands.

### Python import errors
Make sure you're running commands from the `/opt/untangle/ngfw_pkgtools` directory inside the container.
