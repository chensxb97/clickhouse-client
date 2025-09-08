# Clickhouse Client Error Handling

This project explores the clickhouse-connect Python library and how it handles errors when communicating with Clickhouse.

A short report on HTTP 5XX error handling is documented in [error_handling.md](https://github.com/chensxb97/clickhouse-client-error-handling/blob/main/error_handling.md).

## Prerequisites
- Docker
- Python 3.11
- uv

## Setup Instructions
### 1. Run ClickHouse Server
- Ensure Docker Desktop is running

- Start the server using Docker
   ```bash
   docker-compose up -d
   ```

- Verify the server at `http://localhost:8123`

### 2. Run main.py (clickhouse-connect)
- Setup virtualenv
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

- Install dependencies using uv
   ```bash
   uv pip install clickhouse-connect==0.8.18
   ```

- Run the Python script to connect to the ClickHouse instance
   ```bash
   python3 main.py
   ```