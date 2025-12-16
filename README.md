# FastBGPQ4

FastAPI service exposing bgpq4 as an API.

## Features

- Auto sync-to-async execution (timeout-based)
- Redis caching with configurable TTL
- Support for AS-SETs, ASNs, and route-sets
- Prefix aggregation and filtering
- Multiple output formats (JSON, Cisco, Juniper, etc.)
- Prometheus metrics

## Quick Start with Docker

```bash
cd docker
docker-compose up -d
```

Visit http://localhost:8000/docs for API documentation.

## API Examples

### Expand AS-SET (JSON)
```bash
curl "http://localhost:8000/api/v1/as-set/expand?target=AS-HURRICANE"
```

### Get AS Prefixes with Filtering
```bash
curl "http://localhost:8000/api/v1/autonomous-system/prefixes?target=AS15169&min_masklen=24&max_masklen=32"
```

### Cisco Format Output
```bash
curl "http://localhost:8000/api/v1/as-set/expand?target=AS-HURRICANE&format=cisco"
```

### With Aggregation
```bash
curl "http://localhost:8000/api/v1/as-set/expand?target=AS-HURRICANE&aggregate=true"
```

### Custom Cache TTL
```bash
curl "http://localhost:8000/api/v1/as-set/expand?target=AS-HURRICANE&cache_ttl=600"
```

### Skip Cache
```bash
curl "http://localhost:8000/api/v1/as-set/expand?target=AS-HURRICANE&skip_cache=true"
```

### Async Job Polling
If a query exceeds the timeout threshold (default 1000ms), you'll receive a job ID:

```json
{
  "status": "processing",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "poll_url": "/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000"
}
```

Poll for results:
```bash
curl "http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000"
```

## Configuration

Environment variables (see `.env.example`):

- `BGPQ4_BINARY` - Path to bgpq4 binary (default: /usr/bin/bgpq4)
- `IRR_SOURCES` - Comma-separated IRR sources (default: RIPE,RADB,ARIN)
- `SYNC_TIMEOUT_MS` - Sync timeout in milliseconds (default: 1000)
- `MAX_RETRIES` - Max retry attempts (default: 3)
- `DEFAULT_CACHE_TTL` - Default cache TTL in seconds (default: 300)
- `REDIS_URL` - Redis connection URL

## Development Setup

```bash
# Create virtual environment with uv
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Copy environment file
cp .env.example .env

# Run tests
pytest

# Run with auto-reload
uvicorn app.main:app --reload

# Format code
ruff format .

# Lint code
ruff check .
```

## Monitoring

- Health: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics
- API Docs: http://localhost:8000/docs

## Architecture

- **FastAPI** - Web framework
- **Taskiq** - Background task queue
- **Redis** - Caching and task queue backend
- **bgpq4** - IRR query tool (BSD-2-Clause licensed, binary included in Docker image)
- **Pydantic** - Configuration and validation
- **Prometheus** - Metrics export

## Performance Tuning

When expanding large AS-SETs, bgpq4 performance can be improved by adjusting OS-level TCP buffer settings. See the [bgpq4 performance documentation](https://github.com/bgp/bgpq4/tree/main#performance) for details.

### Linux

```bash
sysctl -w net.ipv4.tcp_window_scaling=1
sysctl -w net.core.rmem_max=2097152
sysctl -w net.core.wmem_max=2097152
sysctl -w net.ipv4.tcp_rmem="4096 87380 2097152"
sysctl -w net.ipv4.tcp_wmem="4096 65536 2097152"
```

### FreeBSD

```bash
sysctl -w net.inet.tcp.sendbuf_max=2097152
```

### Docker

For Docker deployments, apply these settings on the host system or use `--sysctl` flags:

```bash
docker run --sysctl net.core.rmem_max=2097152 --sysctl net.core.wmem_max=2097152 ...
```

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE).

Note: The Docker image includes the bgpq4 binary which is licensed under BSD-2-Clause.
