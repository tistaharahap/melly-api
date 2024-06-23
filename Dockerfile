FROM python:3.12-slim

WORKDIR /app

RUN --mount=source=dist,target=/dist PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir /dist/*.whl

COPY pyproject.toml /app/pyproject.toml
COPY bin/run.sh /app/bin/run.sh
RUN chmod +x bin/run.sh

CMD ["bin/run.sh"]
