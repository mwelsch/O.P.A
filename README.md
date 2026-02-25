# Human? head over to [HUMANS.md](HUMANS.md)
# Remote Debug Tool

## Quick Start

### 1. Build the client builder image (one-time)

```bash
docker build -t remote-debug-builder ./builder
```

### 2. Build client executable

**Linux (run on Linux):**
```bash
docker run --rm -v $(pwd)/output:/output -v $(pwd)/client:/src remote-debug-builder
```

**Windows (run on Windows):**
```cmd
docker run --rm -v %CD%\output:/output -v %CD%\client:/src remote-debug-builder
```

Output: `output/client-linux` or `output/client.exe`

### 3. Run the server

```bash
docker-compose up -d
```

Server: http://localhost:8000

Default credentials: `admin` / `admin123`

### 4. Run the client

Set environment variables and run:
```bash
export SERVER_URL=http://localhost:8000
export CLIENT_ID=my-client
./output/client-linux
```

Or on Windows:
```cmd
set SERVER_URL=http://localhost:8000
set CLIENT_ID=my-client
client.exe
```

## Environment Variables

### Server
| Variable | Default | Description |
|----------|---------|-------------|
| ADMIN_USER | admin | Basic auth username |
| ADMIN_PASS | admin123 | Basic auth password |
| SECRET_KEY | dev-secret-key | Flask secret key |
| PORT | 8000 | Server port |

### Client
| Variable | Default | Description |
|----------|---------|-------------|
| SERVER_URL | http://localhost:8000 | Server URL |
| CLIENT_ID | hostname-pid | Unique client ID |
| RECONNECT_INTERVAL | 1 | Reconnect interval in minutes |
| ROOT_DIR | ~/ | Root directory for file access |
