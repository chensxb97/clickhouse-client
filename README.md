# ClickHouse Client PoC

This project explores the clickhouse-connect Python library for interacting with Clickhouse.

## Prerequisites
- Docker
- Python 3.8.9

## Setup Instructions
### 1. Run ClickHouse Server
- Ensure Docker Desktop is running.

- Start the server using Docker
   ```bash
   docker-compose up -d
   ```

- Verify the server at `http://localhost:8123`.

### 2. Run main.py (clickhouse-connect)
- Setup virtualenv
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
   
- Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

- Run the Python script to connect to the ClickHouse instance:
   ```bash
   python3 main.py
   ```