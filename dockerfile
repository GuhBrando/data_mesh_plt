FROM python:3.12

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --no-dev

COPY . .

CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
