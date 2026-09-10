#!/usr/bin/env bash
cd "$(dirname "$0")"
trap 'kill 0' EXIT
uv run uvicorn cjwlog.logger.main:app --host 127.0.0.1 --port 8000 &
uv run streamlit run src/cjwlog/dashboard/main.py --server.port 8501 --server.address 0.0.0.0 &
wait
