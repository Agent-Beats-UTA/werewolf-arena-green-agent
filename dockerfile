FROM ghcr.io/astral-sh/uv:python3.13-bookworm

RUN adduser agent
USER agent
WORKDIR /home/agent

COPY pyproject.toml uv.lock README.md __main__.py ./
COPY src src

RUN \
    --mount=type=cache,target=/home/agent/.cache/uv,uid=1000 \
    uv sync --locked

# Ensure the working directory is on PYTHONPATH so `import src...` works
ENV PYTHONPATH=/home/agent

# Run the project's __main__.py (which starts uvicorn on port 9009)
ENTRYPOINT ["uv", "run", "__main__.py"]
CMD ["--host", "0.0.0.0"]
EXPOSE 9009