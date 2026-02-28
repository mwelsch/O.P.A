# AGENTS.md - Agentic Coding Guidelines

## Project Overview

This is a Remote Debug Tool with multiple components:
- **client/**: Python client that connects to the server, captures screenshots, and executes commands
- **server/**: Flask + SocketIO server for managing clients and forwarding requests
- **web-ui/**: HTML/JavaScript web interface
- **builder/**: PyInstaller-based builder for creating client executables

## Build Commands

### Building the Client

```bash
# Build client builder image (one-time)
docker build -t remote-debug-builder ./builder

# Build Linux client
docker run --rm -v $(pwd)/output:/output -v $(pwd)/client:/src remote-debug-builder

# Or use the build script (includes version management)
./build.sh
```

### Running the Server

```bash
# Start server with Docker
docker-compose up -d

# Or run directly (requires dependencies)
cd server && pip install -r requirements.txt
python main.py
```

### Running the Client

```bash
export SERVER_URL=http://localhost:8000
export CLIENT_ID=my-client
./output/client-linux
```

## Testing

**There are currently no tests in this project.** If you add tests:

```bash
# Install pytest
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run a single test file
pytest tests/test_main.py

# Run a single test
pytest tests/test_main.py::test_function_name

# Run with verbose output
pytest -v
```

## Development Dependencies

Install all dependencies:
```bash
pip install flask flask-socketio python-socketio eventlet pillow rpyc
pip install mss python-socketio aiohttp rpyc
pip install pyinstaller  # for building
```

## Code Style Guidelines

### Imports

```python
# Standard library imports first
import os
import sys
import time
import asyncio

# Third-party imports
import socketio
import flask

# Local imports
import screenshot
import files
import terminal
```

### Naming Conventions

- **Functions/variables**: `snake_case` (e.g., `get_client_id`, `is_streaming`)
- **Classes**: `PascalCase` (e.g., `RemoteClient`, `SocketHandler`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `SERVER_URL`, `CLIENT_TIMEOUT`)
- **Files**: `snake_case.py` (e.g., `client.py`, `rpyc_service.py`)

### Type Hints

This project currently uses minimal type hints. Add type hints when practical:

```python
def get_client(client_id: str) -> dict | None:
    return clients.get(client_id)

async def send_screenshot() -> None:
    ...
```

### Error Handling

```python
try:
    result = risky_operation()
except SpecificException as e:
    print(f"Operation failed: {e}")
    # Handle gracefully, return error response
finally:
    cleanup()
```

### Decorators

Use `@wraps` from `functools` to preserve function metadata:

```python
from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_auth():
            return Response('Authentication required', 401)
        return f(*args, **kwargs)
    return decorated
```

### Flask Routes

```python
@app.route('/endpoint')
@require_auth
def handler():
    # Return JSON responses
    return jsonify({'key': 'value'})
```

### SocketIO Events

```python
@sio.event
async def event_name(data):
    # Handle event
    pass

@sio.on('custom_event')
async def handle_custom(data):
    # Handle custom event
    pass
```

### Async/Await

```python
async def main():
    await sio.connect(SERVER_URL)
    while True:
        await process()
        await asyncio.sleep(0.1)

if __name__ == '__main__':
    asyncio.run(main())
```

### Logging

Currently uses `print()` statements. Consider using the `logging` module:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Client connected: %s", client_id)
logger.error("Failed to connect: %s", e)
```

## Project-Specific Patterns

### Client Registration

Clients register via SocketIO with:
```python
await sio.emit('register', {
    'client_id': CLIENT_ID,
    'version': version.VERSION,
    'platform': client_platform
})
```

### RPyC Reverse Connections

The client initiates a reverse connection to the server for remote code execution:
- Server exposes port 28946
- Client connects OUT to the server
- Server can then execute code on the client

### File Paths

Use `os.path` for cross-platform compatibility:
```python
import os
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'file.py')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

## Common Tasks

### Adding a New SocketIO Event Handler

**Server** (`server/main.py`):
```python
@socketio.on('event_name')
def handle_event(data):
    client_id = data.get('client_id')
    # Process and emit response
    emit('response', {'result': 'data'})
```

**Client** (`client/client.py`):
```python
@sio.on('response')
async def on_response(data):
    print(f"Received: {data}")
```

### Adding a New API Route

```python
@app.route('/new_endpoint', methods=['GET', 'POST'])
@require_auth
def new_endpoint():
    return jsonify({'status': 'ok'})
```

## Docker

The project uses Docker for both building and deployment. Key files:
- `server/Dockerfile` - Server container
- `builder/Dockerfile` - Builder container
- `docker-compose.yml` - Local development setup

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| ADMIN_USER | admin | Server basic auth username |
| ADMIN_PASS | admin123 | Server basic auth password |
| SECRET_KEY | dev-secret-key | Flask secret key |
| PORT | 8000 | Server port |
| VERSION_CHECK_INTERVAL | 60 | Version file check interval in seconds |
| SERVER_URL | http://localhost:8000 | Client server URL |
| CLIENT_ID | hostname-pid | Unique client identifier |
| RPYC_PORT | 28946 | RPyC server port |
| RPYC_SECRET | ChangeThisSecret | RPyC authentication secret |
