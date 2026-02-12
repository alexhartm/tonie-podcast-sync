# Docker Usage

A Docker container wrapper for tonie-podcast-sync is available, thanks to [@goldbricklemon](https://github.com/goldbricklemon).

## Repository

[docker-tonie-podcast-sync](https://github.com/goldbricklemon/docker-tonie-podcast-sync)

## Quick Start with Docker

The Docker container allows you to run tonie-podcast-sync without installing Python or managing dependencies on your host system.

### Pull and Run

```bash
docker run -v ~/.toniepodcastsync:/config goldbricklemon/tonie-podcast-sync update-tonies
```

### Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3'
services:
  tonie-sync:
    image: goldbricklemon/tonie-podcast-sync
    volumes:
      - ~/.toniepodcastsync:/config
    command: update-tonies
```

Run with:

```bash
docker-compose run tonie-sync
```

## Configuration

The Docker container uses the same configuration as the standard installation:

1. Mount your configuration directory to `/config` in the container
2. Create your settings file (see [Configuration Guide](../configuration/settings.md))
3. Run commands as shown above

## Scheduled Syncing

Use Docker with cron or systemd timers to schedule automatic syncing:

### Docker with Cron

```bash
# Add to crontab
0 6 * * * docker run -v ~/.toniepodcastsync:/config goldbricklemon/tonie-podcast-sync update-tonies
```

### Docker Compose with Scheduling

For more advanced scheduling, consider using tools like:

- [Ofelia](https://github.com/mcuadros/ofelia) - Docker job scheduler
- System cron with docker-compose
- Kubernetes CronJobs (for cluster deployments)

## Environment Variables

The Docker container supports the following environment variables:

### `TPS_SOFT_WRAP`

Controls console output soft-wrapping behavior. In container environments, soft-wrap is automatically disabled for better log readability.

**Values:**
- `true` - Enable soft-wrap (long lines wrap to next line)
- `false` - Disable soft-wrap (long lines are truncated)

**Default:** `false` when running in containers, `true` otherwise

```bash
# Explicitly enable soft-wrap
docker run -e TPS_SOFT_WRAP=true -v ~/.toniepodcastsync:/config goldbricklemon/tonie-podcast-sync update-tonies

# Explicitly disable soft-wrap
docker run -e TPS_SOFT_WRAP=false -v ~/.toniepodcastsync:/config goldbricklemon/tonie-podcast-sync update-tonies
```

!!! tip "Container Auto-Detection"
    The application automatically detects if it's running inside Docker, Podman, Kubernetes, or other container environments and adjusts settings accordingly.

## Benefits of Docker Approach

- ✅ No Python installation required on host
- ✅ Consistent environment across systems
- ✅ Easy to schedule and automate
- ✅ Isolated from system dependencies
- ✅ Simple updates via image pulls

## More Information

For detailed Docker-specific documentation and advanced usage, please visit the [docker-tonie-podcast-sync repository](https://github.com/goldbricklemon/docker-tonie-podcast-sync).
