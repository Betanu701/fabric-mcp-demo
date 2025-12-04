# Infrastructure - Azure Deployment

This directory contains all Infrastructure as Code (IaC) for deploying the Enterprise MCP Server to Azure.

## Files

### Main Templates
- **`main.bicep`** - Complete single-region deployment template
- **`parameters.dev.json`** - Development environment parameters
- **`parameters.prod.json`** - Production environment parameters

### Directories
- **`modules/`** - Reusable Bicep modules (future expansion)
- **`workbooks/`** - Application Insights workbooks (future)

## Quick Deploy

### Prerequisites
- Azure CLI 2.50+
- Active Azure subscription
- Contributor/Owner access to subscription

### Deploy Development Environment
```bash
# From repository root
./scripts/provision_azure.sh -e dev -l eastus
```

### Deploy Production Environment
```bash
./scripts/provision_azure.sh -e prod -l eastus
```

## Resources Provisioned

### Compute
- **Azure Container Apps Environment** - Serverless container platform
- **Backend Container App** - FastAPI application (1-10 replicas)
- **Frontend Container App** - React SPA (1-5 replicas)

### Data & Caching
- **Azure Cache for Redis** - Rate limiting and caching
  - Dev: Standard C1 (~$55/month)
  - Prod: Premium P1 (~$250/month)

### Storage
- **Azure Blob Storage** - Brand assets (logos, CSS)
- **CDN Profile + Endpoint** - Global content delivery

### Security & Identity
- **Azure Key Vault** - Secrets management
  - Soft-delete enabled (90 days)
  - Purge protection (production)
  - RBAC authorization
- **Managed Identity** - Service authentication
  - Key Vault Secrets User role
  - Storage Blob Data Contributor role
  - Redis Cache Contributor role

### Monitoring
- **Log Analytics Workspace** - Centralized logging
- **Application Insights** - APM and telemetry
  - 90-day retention
  - OpenTelemetry integration

### Optional (Disabled by Default)
- **Azure Communication Services** - Email/SMS notifications
  - Enable with: `"enableCommunicationServices": true`

## Parameters Reference

### Required Parameters
```json
{
  "containerRegistryName": {
    "value": "mcpserverdev"  // Your ACR name
  }
}
```

### Common Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `environmentName` | string | `dev` | Environment identifier |
| `location` | string | `resourceGroup().location` | Azure region |
| `containerRegistryName` | string | *required* | ACR name |
| `imageTag` | string | `latest` | Container image tag |

### Compute Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `containerAppCpu` | string | `1.0` | CPU cores per container |
| `containerAppMemory` | string | `2Gi` | Memory per container |
| `minReplicas` | int | `1` | Minimum replica count |
| `maxReplicas` | int | `10` | Maximum replica count |

### Redis Parameters
| Parameter | Type | Options | Default |
|-----------|------|---------|---------|
| `redisSku` | string | `Basic`, `Standard`, `Premium` | `Standard` |
| `redisCapacity` | int | `0-6` | `1` |

### Feature Flags
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enableEntraAuth` | bool | `false` | Enable Entra ID authentication |
| `enableCommunicationServices` | bool | `false` | Enable email/SMS notifications |

## Deployment Outputs

After deployment, the following outputs are available:

### URLs
```bash
# Get backend URL
az deployment group show \
  --name mcp-deployment \
  --resource-group mcp-server-dev \
  --query properties.outputs.backendAppUrl.value

# Get frontend URL
az deployment group show \
  --name mcp-deployment \
  --resource-group mcp-server-dev \
  --query properties.outputs.frontendAppUrl.value
```

### Resource Names
```bash
# Get all outputs as JSON
az deployment group show \
  --name mcp-deployment \
  --resource-group mcp-server-dev \
  --query properties.outputs
```

Available outputs:
- `backendAppUrl` - Backend API endpoint
- `frontendAppUrl` - Frontend application URL
- `keyVaultName` - Key Vault resource name
- `keyVaultUrl` - Key Vault URL
- `redisHostName` - Redis cache hostname
- `storageAccountName` - Storage account name
- `cdnEndpointUrl` - CDN endpoint URL
- `appInsightsName` - App Insights resource name
- `managedIdentityClientId` - Managed identity client ID

## Manual Deployment

### Step 1: Create Resource Group
```bash
RESOURCE_GROUP="mcp-server-dev"
LOCATION="eastus"

az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

### Step 2: Validate Template
```bash
az deployment group validate \
  --resource-group $RESOURCE_GROUP \
  --template-file main.bicep \
  --parameters @parameters.dev.json
```

### Step 3: Deploy
```bash
az deployment group create \
  --name mcp-deployment \
  --resource-group $RESOURCE_GROUP \
  --template-file main.bicep \
  --parameters @parameters.dev.json \
  --verbose
```

### Step 4: View Status
```bash
# Watch deployment progress
az deployment group show \
  --name mcp-deployment \
  --resource-group $RESOURCE_GROUP \
  --query properties.provisioningState

# View operation details
az deployment operation group list \
  --name mcp-deployment \
  --resource-group $RESOURCE_GROUP \
  --output table
```

## Cost Estimation

### Development Environment (~$105/month)
- Container Apps: $40
- Redis Standard C1: $55
- Storage LRS: $5
- Key Vault: $5
- Log Analytics: minimal

### Production Environment (~$425/month)
- Container Apps: $150
- Redis Premium P1: $250
- Storage ZRS + CDN: $20
- Key Vault: $5
- Log Analytics: minimal
- Communication Services: pay-per-use

## Scaling

### Manual Scaling
```bash
# Scale backend
az containerapp update \
  --name mcp-server-dev-backend \
  --resource-group mcp-server-dev \
  --min-replicas 2 \
  --max-replicas 20

# Scale frontend
az containerapp update \
  --name mcp-server-dev-frontend \
  --resource-group mcp-server-dev \
  --min-replicas 2 \
  --max-replicas 10
```

### Auto-Scaling
Auto-scaling is configured in the Bicep template:
- **Backend**: Scales on concurrent requests (50 per replica)
- **Frontend**: Scales on concurrent requests (100 per replica)
- **Min**: 1 replica (dev), 2 replicas (prod)
- **Max**: 10 replicas (dev), 20 replicas (prod)

## Update Deployment

### Update Container Images
```bash
# Build new images
az acr build \
  --registry mcpserverdev \
  --image mcp-server-backend:v2.0 \
  --file Dockerfile \
  --target backend \
  .

# Update deployment
az deployment group create \
  --name mcp-deployment-update \
  --resource-group mcp-server-dev \
  --template-file main.bicep \
  --parameters @parameters.dev.json imageTag=v2.0
```

### Update Configuration
```bash
# Update environment variables
az containerapp update \
  --name mcp-server-dev-backend \
  --resource-group mcp-server-dev \
  --set-env-vars NEW_SETTING=value

# Update secrets
az containerapp secret set \
  --name mcp-server-dev-backend \
  --resource-group mcp-server-dev \
  --secrets api-key=newvalue
```

## Monitoring

### View Logs
```bash
# Backend logs (real-time)
az containerapp logs show \
  --name mcp-server-dev-backend \
  --resource-group mcp-server-dev \
  --follow

# Frontend logs
az containerapp logs show \
  --name mcp-server-dev-frontend \
  --resource-group mcp-server-dev \
  --tail 100
```

### View Metrics
```bash
# Request count
az monitor metrics list \
  --resource /subscriptions/{id}/resourceGroups/mcp-server-dev/providers/Microsoft.App/containerApps/mcp-server-dev-backend \
  --metric Requests \
  --interval PT1M

# CPU usage
az monitor metrics list \
  --resource /subscriptions/{id}/resourceGroups/mcp-server-dev/providers/Microsoft.App/containerApps/mcp-server-dev-backend \
  --metric CpuUsage \
  --interval PT1M
```

### Application Insights
```bash
# Query requests
az monitor app-insights query \
  --app mcp-server-dev-ai \
  --analytics-query "requests | where timestamp > ago(1h) | summarize count() by resultCode" \
  --output table
```

## Troubleshooting

### Issue: Deployment fails with RBAC error
```bash
# Grant yourself Owner role
az role assignment create \
  --role Owner \
  --assignee $(az ad signed-in-user show --query objectId -o tsv) \
  --scope /subscriptions/{subscription-id}/resourceGroups/mcp-server-dev
```

### Issue: Container app not starting
```bash
# Check revision status
az containerapp revision list \
  --name mcp-server-dev-backend \
  --resource-group mcp-server-dev \
  --output table

# View detailed logs
az containerapp logs show \
  --name mcp-server-dev-backend \
  --resource-group mcp-server-dev \
  --tail 200
```

### Issue: Can't connect to Redis
```bash
# Test Redis connectivity
az redis show \
  --name mcp-server-dev-redis-{suffix} \
  --resource-group mcp-server-dev \
  --query "properties.{hostname:hostName,port:sslPort,state:provisioningState}"

# Get Redis key
az redis list-keys \
  --name mcp-server-dev-redis-{suffix} \
  --resource-group mcp-server-dev
```

### Issue: High costs
```bash
# View resource costs
az consumption usage list \
  --start-date $(date -d '7 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --query "[?contains(instanceName, 'mcp-server-dev')].{Name:instanceName, Cost:pretaxCost}" \
  --output table

# Reduce Redis size
az redis update \
  --name mcp-server-dev-redis-{suffix} \
  --resource-group mcp-server-dev \
  --sku Basic \
  --vm-size C0
```

## Cleanup

### Delete All Resources
```bash
# Delete resource group (irreversible!)
az group delete \
  --name mcp-server-dev \
  --yes \
  --no-wait
```

### Delete Specific Resources
```bash
# Delete container apps only
az containerapp delete \
  --name mcp-server-dev-backend \
  --resource-group mcp-server-dev \
  --yes

az containerapp delete \
  --name mcp-server-dev-frontend \
  --resource-group mcp-server-dev \
  --yes
```

## Security Considerations

### Network Security
- Container Apps use private VNet integration (future)
- Redis cache requires TLS 1.2+
- Key Vault uses Azure RBAC (no access policies)
- Storage allows public blob access (for CDN)

### Identity & Access
- Managed Identity for all service-to-service auth
- No connection strings in environment variables
- Secrets stored in Key Vault only
- RBAC assigned at deployment time

### Data Protection
- Key Vault: soft-delete (90 days) + purge protection
- Redis: persistence enabled (Premium tier)
- Storage: versioning and soft-delete enabled
- Logs: 90-day retention in App Insights

## Best Practices

### Development
1. Use `parameters.dev.json` for cost optimization
2. Set `minReplicas: 1` to save costs
3. Use Basic/Standard Redis instead of Premium
4. Enable local dev mode to avoid Azure costs

### Production
1. Use `parameters.prod.json` with redundancy
2. Set `minReplicas: 2` for high availability
3. Use Premium Redis for persistence
4. Enable geo-replication for disaster recovery
5. Configure auto-scaling for peak loads
6. Set up budget alerts

### CI/CD
1. Use GitHub Actions for automated deployment
2. Deploy to dev on `develop` branch
3. Deploy to prod on `main` branch
4. Run smoke tests after deployment
5. Use deployment slots for zero-downtime updates

## Additional Resources

- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Bicep Language Reference](https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Deployment Guide](../docs/deployment.md)
- [Disaster Recovery Guide](../docs/disaster-recovery.md)
- [API Specification](../docs/api-spec.yaml)
