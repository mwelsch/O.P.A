# Human? head over to [HUMANS.md](HUMANS.md)
# Remote Debug Tool

## Quick Start

### 1. Build the client

**Using the build script (recommended):**
```bash
./build.sh
```

This script will:
- Ask if you want to update the version
- Build the Docker builder image (one-time)
- Build the client executable
- Copy the binary to `output/` and `server/updates/`

**Manual build:**
```bash
# Build client builder image (one-time)
docker build -t remote-debug-builder ./builder

# Build Linux client
docker run --rm -v $(pwd)/output:/output -v $(pwd)/client:/src remote-debug-builder
```

Output: `output/client-linux`

### 2. Run the server

```bash
docker-compose up -d
```

Server: http://localhost:8000

Default credentials: `admin` / `admin123`

### 3. Run the client

```bash
export SERVER_URL=http://localhost:8000
export CLIENT_ID=my-client
./output/client-linux
```

## Versioning & Self-Updating

### How it works

1. **Version file**: `server/version.json` contains the current version for each platform
2. **Client registration**: When a client connects, it sends its version to the server
3. **Version check**: Server compares client version vs. expected version in `version.json`
4. **Update trigger**: If versions don't match, server sends update URL to client
5. **Self-update**: Client downloads new binary, executes it, and replaces itself

### Version file format

```json
{
    "linux": "1.2.0",
    "windows": "1.2.0"
}
```

### Updating versions

**Option 1: Using build.sh**
```bash
./build.sh
# Answer 'y' when prompted, enter new version (e.g., 1.2.0)
```

**Option 2: Manual edit**
```bash
vim server/version.json
docker-compose restart
```

The server checks the version file every 60 seconds (configurable via `VERSION_CHECK_INTERVAL`) and will push updates to connected clients.

### Deploying new versions

1. Build new client binary with incremented version
2. Copy to server's updates folder:
   ```bash
   cp output/client-linux server/updates/
   ```
3. Update version.json (via build.sh or manually)
4. Connected clients will automatically update on next version check

## Environment Variables

### Server
| Variable | Default | Description |
|----------|---------|-------------|
| ADMIN_USER | admin | Basic auth username |
| ADMIN_PASS | admin123 | Basic auth password |
| SECRET_KEY | dev-secret-key | Flask secret key |
| PORT | 8000 | Server port |
| VERSION_CHECK_INTERVAL | 60 | Version file check interval (seconds) |
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
| SELF_UPDATE_KILL | true | Whether to kill old process after update |

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
