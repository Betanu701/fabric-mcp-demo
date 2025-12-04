# ⚡ Quick Reference Card

## Essential Commands

### Local Development
```bash
# Start local environment
docker-compose up -d

# Check services
docker ps

# View backend logs
docker-compose logs -f backend

# Stop all services
docker-compose down
```

### Azure Deployment
```bash
# Login to Azure
az login

# Deploy to dev
./scripts/provision_azure.sh -e dev -l eastus

# Deploy to prod
./scripts/provision_azure.sh -e prod -l eastus

# Check deployment status
az deployment group list --resource-group mcp-server-dev --output table
```

### Testing APIs
```bash
# Health check
curl http://localhost:8000/health

# List agents
curl -H "X-Tenant-ID: default" http://localhost:8000/api/agents

# Send chat message
curl -X POST http://localhost:8000/api/chat \
  -H "X-Tenant-ID: default" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "agent_id": "sales-001"}'

# Get costs
curl -H "X-Tenant-ID: default" http://localhost:8000/api/costs

# Get branding
curl -H "X-Tenant-ID: default" http://localhost:8000/api/branding
```

### Container Apps
```bash
# List apps
az containerapp list --resource-group mcp-server-dev --output table

# View logs
az containerapp logs show \
  --name mcp-server-dev-backend \
  --resource-group mcp-server-dev \
  --follow

# Restart app
az containerapp revision restart \
  --name mcp-server-dev-backend \
  --resource-group mcp-server-dev

# Scale app
az containerapp update \
  --name mcp-server-dev-backend \
  --resource-group mcp-server-dev \
  --min-replicas 2 \
  --max-replicas 10
```

### Key Vault
```bash
# List secrets
az keyvault secret list --vault-name mcp-server-dev-kv --output table

# Get secret
az keyvault secret show \
  --vault-name mcp-server-dev-kv \
  --name tenant-default-config

# Set secret
az keyvault secret set \
  --vault-name mcp-server-dev-kv \
  --name tenant-customer1-config \
  --value '{...json...}'
```

### Redis
```bash
# Get Redis info
az redis show \
  --name mcp-server-dev-redis-xxxxx \
  --resource-group mcp-server-dev

# Get access keys
az redis list-keys \
  --name mcp-server-dev-redis-xxxxx \
  --resource-group mcp-server-dev

# Test connection
redis-cli -h xxx.redis.cache.windows.net -p 6380 --tls -a KEY PING
```

### Application Insights
```bash
# Query requests
az monitor app-insights query \
  --app mcp-server-dev-ai \
  --analytics-query "requests | where timestamp > ago(1h) | summarize count()" \
  --output table

# View exceptions
az monitor app-insights query \
  --app mcp-server-dev-ai \
  --analytics-query "exceptions | where timestamp > ago(1h)" \
  --output table
```

## Important URLs

### Local
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:5173
- Redis: localhost:6379

### Azure (after deployment)
```bash
# Get URLs
az deployment group show \
  --name YOUR-DEPLOYMENT-NAME \
  --resource-group mcp-server-dev \
  --query 'properties.outputs.{Backend:backendAppUrl.value, Frontend:frontendAppUrl.value}'
```

## Environment Variables

### Required
```bash
KEY_VAULT_URL=https://xxx.vault.azure.net/
REDIS_URL=xxx.redis.cache.windows.net:6380,...
STORAGE_ACCOUNT_URL=https://xxx.blob.core.windows.net/
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
```

### Optional
```bash
ENABLE_ENTRA_AUTH=false
LOCAL_DEV_MODE=true
LOG_LEVEL=INFO
```

## Tenant Configuration Template

```json
{
  "id": "tenant-id",
  "name": "Tenant Name",
  "enabled": true,
  "foundry_endpoint": "https://foundry.azure.com/...",
  "rate_limit_rpm": 100,
  "rate_limit_rpd": 10000,
  "quota_monthly_requests": 100000,
  "budget_limit": 1000.00,
  "budget_threshold": 90,
  "budget_enforcement": "warn",
  "notification_channels": ["in-app"],
  "branding": {
    "inherit_global": true,
    "primary_color": "#0078D4"
  }
}
```

## GitHub Secrets Required

### Option A: Federated Credentials (Recommended)
```
AZURE_CLIENT_ID
AZURE_TENANT_ID
AZURE_SUBSCRIPTION_ID
ACR_LOGIN_SERVER
ACR_USERNAME
ACR_PASSWORD
```

### Option B: Service Principal (Legacy)
```
AZURE_CREDENTIALS (JSON)
AZURE_SUBSCRIPTION_ID
ACR_LOGIN_SERVER
ACR_USERNAME
ACR_PASSWORD
```

## Common KQL Queries

### Request Count by Tenant
```kusto
requests
| where timestamp > ago(1h)
| extend tenant_id = tostring(customDimensions.tenant_id)
| summarize count() by tenant_id
```

### Average Response Time
```kusto
requests
| where timestamp > ago(1h)
| summarize avg(duration), percentile(duration, 95)
```

### Error Rate
```kusto
requests
| where timestamp > ago(1h)
| summarize ErrorRate = 100.0 * countif(success == false) / count()
```

### Cost by Tenant
```kusto
customEvents
| where name == "cost_tracked"
| extend tenant_id = tostring(customDimensions.tenant_id)
| extend cost = todouble(customDimensions.cost)
| summarize sum(cost) by tenant_id
```

## Troubleshooting Quick Fixes

### Backend Not Starting
```bash
# Check logs
az containerapp logs show --name mcp-server-dev-backend --resource-group mcp-server-dev --tail 50

# Restart
az containerapp revision restart --name mcp-server-dev-backend --resource-group mcp-server-dev
```

### Rate Limiting Not Working
```bash
# Check Redis connection
az redis show --name mcp-server-dev-redis-xxxxx --resource-group mcp-server-dev --query provisioningState

# View Redis logs (Container Apps)
az containerapp logs show --name mcp-server-dev-backend --resource-group mcp-server-dev | grep -i redis
```

### Can't Access Key Vault
```bash
# Check RBAC permissions
az role assignment list --scope /subscriptions/xxx/resourceGroups/mcp-server-dev

# Grant access
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee YOUR-PRINCIPAL-ID \
  --scope /subscriptions/xxx/resourceGroups/mcp-server-dev/providers/Microsoft.KeyVault/vaults/xxx
```

### High Costs
```bash
# View costs
az consumption usage list \
  --start-date $(date -d '7 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  | jq '[.[] | select(.instanceName | contains("mcp"))]'

# Reduce replicas
az containerapp update --name mcp-server-dev-backend --resource-group mcp-server-dev --min-replicas 1
```

## Resource Cleanup

```bash
# Delete everything (WARNING: Irreversible!)
az group delete --name mcp-server-dev --yes --no-wait

# Delete specific app
az containerapp delete --name mcp-server-dev-backend --resource-group mcp-server-dev --yes

# Stop (but don't delete) app
az containerapp update --name mcp-server-dev-backend --resource-group mcp-server-dev --min-replicas 0 --max-replicas 0
```

## Useful Links

- [Getting Started](GETTING_STARTED.md)
- [Deployment Guide](docs/deployment.md)
- [API Docs](http://localhost:8000/docs) (local)
- [Azure Portal](https://portal.azure.com)
- [GitHub Actions](https://github.com/YOUR-ORG/fabric-mcp-demo/actions)
