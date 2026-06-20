# Deployment

This repository ships with a `Dockerfile` and `docker-compose.yml` for local and production deployment. For Streamlit Cloud compatibility, ensure the `streamlit` service is started with the `streamlit run` command and the `PORT` env var is configured by the platform.

See `Dockerfile` and `docker-compose.yml` for example deployments. The recommended production flow is:

1. Build multi-stage Docker image.
2. Push image to container registry.
3. Deploy to Kubernetes or a container service with secrets injected via platform-managed secrets.
# Deployment

## Docker Compose

This repository includes a production-ready `Dockerfile` and `docker-compose.yml`.

Build and start the service:

```bash
docker compose up --build
```

The service exposes an API and health endpoint as defined in the compose file.

## Docker image

Build the image directly:

```bash
docker build -t customer_support_agent:latest .
```

Run the container:

```bash
docker run --rm -p 8080:8080 --env-file .env customer_support_agent:latest
```

## Health checks

The service provides a health endpoint for platform readiness checks. Configure your orchestrator to use this endpoint for liveness and readiness.

## Environment variables

The service supports configuration through environment variables with the `SUPPORT_AGENT_` prefix. Key deployment variables include:

- `SUPPORT_AGENT_OPENAI_API_KEY`
- `SUPPORT_AGENT_DEFAULT_PERSONA`
- `SUPPORT_AGENT_RETRIEVAL_CONFIDENCE_THRESHOLD`
- `SUPPORT_AGENT_CACHE_TTL_SECONDS`
- `SUPPORT_AGENT_MAX_REQUESTS_PER_MINUTE`
- `SUPPORT_AGENT_LOG_LEVEL`

## Production recommendations

- Store secrets securely and do not commit `.env` files.
- Use a robust vector database and separate storage for large document collections.
- Secure network access to the model provider and data stores.
- Enable monitoring for uptime, latency, and rate-limit events.
