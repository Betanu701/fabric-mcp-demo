# Quick Start Guide

Get the Enterprise MCP Server running locally in under 5 minutes.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git
- Optional: Docker and Docker Compose for containerized deployment

## Local Development Setup

### 1. Clone and Navigate
```bash
git clone https://github.com/your-org/fabric-mcp-demo.git
cd fabric-mcp-demo
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Install core dependencies
pip install --upgrade pip
pip install fastapi uvicorn pydantic pydantic-settings python-dotenv pyyaml \
            azure-identity azure-keyvault-secrets azure-storage-blob redis httpx

# Install optional test dependencies
pip install pytest pytest-asyncio pytest-cov httpx
```

### 4. Configure Environment
The `.env` file is already configured for local development:
```bash
LOCAL_DEV_MODE=true
LOCAL_MOCK_SERVICES=true
ALLOW_ALL_TENANTS=true
```

No Azure resources required!

### 5. Start the Server
```bash
uvicorn src.app.main:app --host 127.0.0.1 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

### 6. Test the API

**Health Check:**
```bash
curl http://127.0.0.1:8000/health
```

**List Available Agents:**
```bash
curl -H "X-Tenant-ID: default" http://127.0.0.1:8000/api/agents
```

**Send a Chat Message:**
```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "X-Tenant-ID: default" \
  -H "Content-Type: application/json" \
  -d '{"message": "What sales data do you have?", "agent_id": "sales-agent"}'
```

**View API Documentation:**
Open http://127.0.0.1:8000/docs in your browser for interactive Swagger UI.

## Using Docker (Alternative)

### 1. Start All Services
```bash
docker-compose up -d
```

This starts:
- **Redis** (port 6379)
- **API Backend** (port 8000)
- **Frontend** (port 5173)

### 2. Check Logs
```bash
docker-compose logs -f api
```

### 3. Stop Services
```bash
docker-compose down
```

## Available Endpoints

| Endpoint | Method | Description | Requires Tenant Header |
|----------|--------|-------------|------------------------|
| `/health` | GET | Health check | No |
| `/` | GET | API information | No |
| `/docs` | GET | Swagger UI | No |
| `/api/agents` | GET | List agents | Yes |
| `/api/agents/{id}` | GET | Get specific agent | Yes |
| `/api/chat` | POST | Send chat message | Yes |
| `/api/admin/tenants` | GET | List tenants | No (admin) |
| `/api/admin/sources` | POST | Discover sources | Yes (admin) |

## Testing

### Run Automated Tests
```bash
pytest tests/ -v --no-cov
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

View coverage report at `htmlcov/index.html`.

## Configuration

### Tenant Configuration
Edit `config/tenants.yaml` to add/modify tenants:

```yaml
allow_all: true  # Allow any tenant ID (dev mode)

tenants:
  - id: default
    name: Default Organization
    foundry_endpoint: https://foundry.example.com/api
    rate_limit_rpm: 100
    rate_limit_rpd: 10000
    budget_threshold: 90
    budget_enforcement: block
    notification_channels:
      - in-app
    branding:
      inherit_global: true
```

### Agent Configuration
Agents are loaded from the tenant configuration. Mock agents include:
- **sales-agent**: Sales and revenue data
- **inventory-agent**: Inventory and stock data
- **general-agent**: General queries and routing

## Development Workflow

### 1. Make Changes
Edit code in `src/app/` directory.

### 2. Auto-Reload
Uvicorn watches for file changes and reloads automatically with `--reload` flag.

### 3. Test Changes
```bash
pytest tests/test_api.py -v
```

### 4. Check Logs
Watch terminal output for INFO/WARNING/ERROR messages.

## Troubleshooting

### Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install missing dependencies
pip install -r requirements.txt
```

### Tenant Not Found
Ensure you're sending the `X-Tenant-ID` header:
```bash
curl -H "X-Tenant-ID: default" http://127.0.0.1:8000/api/agents
```

### Port Already in Use
Change the port in the uvicorn command:
```bash
uvicorn src.app.main:app --port 8001
```

### Redis Connection Failed
In local mode with `LOCAL_MOCK_SERVICES=true`, Redis is optional. To use Redis:
```bash
# Start Redis with Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install locally
# Ubuntu/Debian: sudo apt-get install redis-server
# macOS: brew install redis
```

## Next Steps

### Complete Frontend Setup
```bash
cd web
npm install
npm run dev
```

Frontend runs on http://localhost:5173

### Enable Azure Services
1. Create Azure resources (Key Vault, Redis Cache, Container Apps)
2. Update `.env` with Azure URLs
3. Set `LOCAL_MOCK_SERVICES=false`
4. Authenticate with Azure CLI: `az login`

### Deploy to Azure
```bash
# Build Docker image
docker build -t enterprise-mcp:latest .

# Push to Azure Container Registry
az acr login --name <your-acr-name>
docker tag enterprise-mcp:latest <your-acr-name>.azurecr.io/enterprise-mcp:latest
docker push <your-acr-name>.azurecr.io/enterprise-mcp:latest

# Deploy to Container Apps
# (Use Bicep templates in infrastructure/ directory)
```

## Additional Resources

- **API Documentation**: http://127.0.0.1:8000/docs
- **Testing Results**: See `TESTING.md`
- **Project README**: See `README.md`
- **Architecture**: See `README.md` → Architecture section

## Support

For issues or questions:
1. Check the logs: `tail -f /tmp/uvicorn.log`
2. Review the testing documentation: `TESTING.md`
3. Inspect the configuration: `config/tenants.yaml`
4. Check environment variables: `cat .env`

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_DEV_MODE` | `true` | Enable local development mode |
| `LOCAL_MOCK_SERVICES` | `true` | Mock Azure services |
| `APP_NAME` | `Enterprise MCP` | Application name |
| `APP_VERSION` | `1.0.0` | Application version |
| `ENVIRONMENT` | `development` | Environment (development/staging/production) |
| `API_HOST` | `0.0.0.0` | API host binding |
| `API_PORT` | `8000` | API port |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `FEATURE_TELEMETRY` | `false` | Enable OpenTelemetry |
| `ALLOW_ALL_TENANTS` | `true` | Allow any tenant ID |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |

## Quick Command Reference

```bash
# Start server
uvicorn src.app.main:app --reload

# Run tests
pytest tests/ -v

# Check health
curl http://127.0.0.1:8000/health

# List agents
curl -H "X-Tenant-ID: default" http://127.0.0.1:8000/api/agents

# Send chat message
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "X-Tenant-ID: default" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "agent_id": "sales-agent"}'

# View logs
tail -f /tmp/uvicorn.log  # If using nohup
# Or just watch terminal output

# Stop server
# Press Ctrl+C in terminal running uvicorn
```
