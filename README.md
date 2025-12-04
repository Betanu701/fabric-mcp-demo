# Enterprise Multi-Tenant MCP Server

A production-ready Model Context Protocol (MCP) server for Microsoft Azure, featuring multi-tenant orchestration, FoundryIQ integration, hierarchical white-labeling, cost management, and comprehensive monitoring.

## Features

- **Multi-Tenant Architecture**: Header-based tenant isolation with configurable quotas and policies
- **FoundryIQ Integration**: Multi-agent orchestration via Microsoft Agent Framework
- **DataAgent Support**: Direct integration with Fabric Data Agents, SharePoint, OneLake, and web sources
- **White-Label UI**: Hierarchical theming (global + per-tenant overrides) with brand guide upload
- **Cost Management**: Real-time Azure cost tracking with configurable budget enforcement
- **Rate Limiting**: Redis-backed per-tenant quotas (RPM, RPD, monthly limits)
- **Monitoring**: Application Insights with pre-built workbooks for usage, costs, and performance
- **Security**: Optional Entra ID authentication, Azure Key Vault secrets, Managed Identity RBAC
- **First-Run Wizard**: Guided setup for required/optional configuration
- **Disaster Recovery**: Multi-region failover documentation and backup policies

## Architecture

### Backend
- **FastAPI** (Python 3.11+) - Async REST API
- **Azure SDK** - Key Vault, Blob Storage, Cost Management, Communication Services
- **Microsoft Agent Framework** - FoundryIQ orchestration
- **Redis** - Rate limiting and caching
- **OpenTelemetry** - Distributed tracing and metrics

### Frontend
- **React 18 + TypeScript** - UI framework
- **Vite** - Build tool
- **Dynamic Theming** - CSS variables with runtime updates
- **Recharts** - Usage and cost visualization

### Infrastructure
- **Azure Container Apps** - Serverless container hosting
- **Azure Cache for Redis** - Managed Redis with persistence
- **Azure Key Vault** - Secrets management
- **Azure Blob Storage + CDN** - Brand assets
- **Application Insights** - Monitoring and analytics
- **Azure Cost Management** - Billing and budgets

## Quick Start

### Prerequisites
- Azure subscription with Owner or Contributor access
- Azure CLI installed and authenticated
- Docker and Docker Compose (for local development)
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/your-org/fabric-mcp-demo.git
cd fabric-mcp-demo
```

2. **Set up local environment**
```bash
./scripts/init_local.sh
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your Azure resource URLs
```

4. **Start services**
```bash
docker-compose up -d
```

5. **Access the application**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Azure Deployment

1. **Provision infrastructure**
```bash
./scripts/provision_azure.sh -g <resource-group> -l <location>
```

2. **Deploy application**
```bash
az acr build --registry <acr-name> --image mcp-server:latest .
az containerapp update --name mcp-server --resource-group <rg> --image <acr>.azurecr.io/mcp-server:latest
```

3. **Complete setup wizard**
- Navigate to your Container App URL
- Follow the first-run wizard to configure tenants, sources, and branding

## Configuration

### Tenant Configuration (`config/tenants.yaml`)
```yaml
allow_all: true  # Accept any X-Tenant-ID (disable for production)

tenants:
  - id: default
    name: Default Tenant
    enabled: true
    foundry_endpoint: https://foundry.azure.com/default
    rate_limit_rpm: 100
    budget_threshold: 90
    budget_enforcement: block
```

### Global Settings (`config/default.yaml`)
```yaml
app_name: Enterprise MCP
allow_all_tenants: true
default_budget_enforcement: block
redis_url: redis://localhost:6379
key_vault_url: https://your-keyvault.vault.azure.net/
entra_enabled: false
```

## API Usage

### Chat with Agent
```bash
curl -X POST https://your-mcp.azurecontainerapps.io/api/chat \
  -H "X-Tenant-ID: tenant-001" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is our Q4 revenue?",
    "agent_id": "finance-agent"
  }'
```

### List Available Agents
```bash
curl -X GET https://your-mcp.azurecontainerapps.io/api/agents \
  -H "X-Tenant-ID: tenant-001"
```

### Tenant Management (Admin)
```bash
curl -X POST https://your-mcp.azurecontainerapps.io/api/admin/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "id": "tenant-002",
    "name": "Contoso Corp",
    "foundry_endpoint": "https://foundry.azure.com/contoso"
  }'
```

## Documentation

- [API Specification](docs/api-spec.yaml) - OpenAPI 3.0 schema
- [Deployment Guide](docs/deployment.md) - Step-by-step Azure deployment
- [Disaster Recovery](docs/disaster-recovery.md) - Multi-region failover procedures
- [Branding Guide](docs/branding-guide.md) - Customization and white-labeling

## Project Structure

```
fabric-mcp-demo/
├── src/app/                    # FastAPI backend
│   ├── main.py                 # Application entry point
│   ├── routers/                # API endpoints
│   ├── services/               # Business logic
│   ├── middleware/             # Request processing
│   ├── models/                 # Pydantic schemas
│   ├── security/               # Auth and validation
│   └── startup/                # Initialization scripts
├── web/                        # React frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── context/            # React Context providers
│   │   └── api/                # API client
│   └── public/                 # Static assets
├── infra/                      # Infrastructure-as-code
│   ├── main.bicep              # Single-region deployment
│   ├── dr.bicep                # Multi-region DR
│   ├── modules/                # Reusable Bicep modules
│   └── workbooks/              # Application Insights workbooks
├── config/                     # Configuration files
│   ├── tenants.yaml            # Initial tenant definitions
│   └── default.yaml            # Global settings
├── scripts/                    # Automation scripts
│   ├── init_local.sh           # Local dev setup
│   └── provision_azure.sh      # Azure provisioning
├── docs/                       # Documentation
├── .github/workflows/          # CI/CD pipelines
├── Dockerfile                  # Container build
├── docker-compose.yml          # Local dev stack
└── README.md                   # This file
```

## Security

- **Secrets**: All credentials stored in Azure Key Vault
- **Authentication**: Optional Entra ID integration (disabled by default)
- **Authorization**: Tenant-scoped access via `X-Tenant-ID` header
- **Network**: Private endpoints and VNET integration supported
- **Compliance**: Audit logs via Application Insights, soft-delete enabled

## Monitoring

Pre-built Application Insights workbooks:
- **Tenant Usage**: Request counts, latency, errors by tenant
- **Rate Limits**: Throttle events, quota usage
- **Agent Performance**: FoundryIQ agent call metrics
- **Cost Analysis**: Per-tenant cost breakdown and trends
- **Budget Tracking**: Budget status and alert history

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: https://github.com/your-org/fabric-mcp-demo/issues
- **Documentation**: https://github.com/your-org/fabric-mcp-demo/wiki
- **Email**: support@your-org.com
