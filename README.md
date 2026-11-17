# SmartSpend

Expense tracker with a next-month spending forecast and budget alerts.
Flask + SQLAlchemy, linear-regression forecast (scikit-learn), Docker, GitHub Actions CI/CD.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt
python wsgi.py                  # http://127.0.0.1:5000
```

## Test and lint

```bash
flake8 .
pytest -q
```

## Run with Docker

```bash
docker compose up --build       # http://localhost:5000
```

Data lives in the `smartspend-data` volume. Set `SECRET_KEY` in a `.env` file (see `.env.example`).

## CI/CD (GitHub Actions)

`.github/workflows/ci-cd.yml` runs on every push and pull request to `main`:

1. **test**: flake8, then pytest
2. **docker**: builds the image; on push to `main` it also pushes to Docker Hub
3. **deploy**: on push to `main`, calls the Render deploy hook

Add these in GitHub: Settings > Secrets and variables > Actions

| Secret | Value |
|---|---|
| `DOCKERHUB_USERNAME` | your Docker Hub username |
| `DOCKERHUB_TOKEN` | a Docker Hub access token |
| `RENDER_DEPLOY_HOOK_URL` | Render service > Settings > Deploy Hook |

## Deploy on Render

Create a Web Service from the Docker Hub image (or this repo with the Dockerfile).
Set `SECRET_KEY`, and optionally `DATABASE_URL` for PostgreSQL.

## Project layout

```
app/            Flask app (models, routes, forecast, insights, templates, static)
tests/          pytest tests
Dockerfile, docker-compose.yml
.github/workflows/ci-cd.yml
```
