FROM python:3.12

WORKDIR /app

RUN pip install uv

RUN curl -sSfL "https://release.ariga.io/atlas/atlas-linux-amd64-latest" \
      -o /usr/local/bin/atlas && chmod +x /usr/local/bin/atlas

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --no-dev

COPY . .

RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
