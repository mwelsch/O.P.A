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
| RPYC_PORT | 28946 | RPyC server port for reverse connections |
| RPYC_SECRET | ChangeThisSecret | Shared secret for RPyC authentication |

### Client
| Variable | Default | Description |
|----------|---------|-------------|
| SERVER_URL | http://localhost:8000 | Server URL |
| CLIENT_ID | hostname-pid | Unique client ID |
| RECONNECT_INTERVAL | 1 | Reconnect interval in minutes |
| ROOT_DIR | ~/ | Root directory for file access |
| RPYC_SERVER | | Server IP/hostname for RPyC reverse connection |
| RPYC_PORT | 28946 | RPyC server port (must match server) |
| RPYC_SECRET | ChangeThisSecret | Shared secret (must match server) |

## Remote Code Execution (RPyC)

The tool supports remote Python code execution via RPyC using a reverse connection architecture. This works even when clients are behind NAT/firewalls because the client initiates the connection to the server.

### How it works
1. Server exposes port `28946` (configurable) for RPyC connections
2. Client connects OUT to the server's RPyC port (outbound connections work from behind NAT)
3. Client authenticates with a shared secret
4. Server can now execute Python code on any connected client via the web UI

### Setup

**Server:**
```bash
docker-compose up -d
```
The RPyC port (28946) is automatically exposed.

**Client:**
```bash
export SERVER_URL=http://localhost:8000
export CLIENT_ID=my-client
export RPYC_SERVER=192.168.1.100  # Server's reachable IP address
./output/client-linux
```

### Security Note
- Change `RPYC_SECRET` from the default in production!
- The RPyC port (28946) should not be exposed to untrusted networks
- Code execution has full access to the client's Python environment
