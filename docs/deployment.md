# Deployment Guide - Enterprise MCP Server

## Overview

This guide walks through deploying the Enterprise MCP Server to Azure Container Apps with all required infrastructure.

## Prerequisites

### Required Tools
- **Azure CLI** 2.50+ ([Install](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
- **Docker** 20.10+ ([Install](https://docs.docker.com/get-docker/))
- **Git** 2.30+ ([Install](https://git-scm.com/downloads))
- **jq** 1.6+ (JSON processor)

### Azure Requirements
- Azure subscription with **Owner** or **Contributor** access
- Permissions to create:
  - Resource Groups
  - Container Apps
  - Container Registry
  - Redis Cache
  - Key Vault
  - Storage Accounts
  - Application Insights
  - Managed Identities
  - Role Assignments

### Local Development
- **Python** 3.12+ ([Install](https://www.python.org/downloads/))
- **Node.js** 18+ ([Install](https://nodejs.org/))
- **npm** 9+

## Quick Start (Automated)

### 1. Clone Repository
```bash
git clone https://github.com/your-org/fabric-mcp-demo.git
cd fabric-mcp-demo
```

### 2. Login to Azure
```bash
az login
az account set --subscription "Your Subscription Name"
```

### 3. Run Provisioning Script
```bash
# Development environment
./scripts/provision_azure.sh -e dev -l eastus

# Production environment
./scripts/provision_azure.sh -e prod -l eastus -g mcp-production
```

The script will:
- ✅ Create resource group
- ✅ Create Azure Container Registry
- ✅ Build and push Docker images
- ✅ Deploy all infrastructure (Bicep)
- ✅ Configure RBAC permissions
- ✅ Display deployment URLs

### 4. Access Your Application
After deployment completes, you'll see output like:
```
Application URLs:
  Frontend:          https://mcp-server-dev-frontend.nicebeach-123.eastus.azurecontainerapps.io
  Backend API:       https://mcp-server-dev-backend.nicebeach-123.eastus.azurecontainerapps.io
  API Docs:          https://mcp-server-dev-backend.nicebeach-123.eastus.azurecontainerapps.io/docs
```

## Manual Deployment (Step-by-Step)

### Step 1: Create Resource Group
```bash
ENVIRONMENT="dev"
LOCATION="eastus"
RESOURCE_GROUP="mcp-server-${ENVIRONMENT}"

az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --tags "Environment=$ENVIRONMENT"
```

### Step 2: Create Container Registry
```bash
REGISTRY_NAME="mcpserver${ENVIRONMENT}"

az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $REGISTRY_NAME \
  --sku Standard \
  --admin-enabled true
```

### Step 3: Build and Push Images
```bash
# Backend
az acr build \
  --registry $REGISTRY_NAME \
  --image mcp-server-backend:latest \
  --file Dockerfile \
  --target backend \
  .

# Frontend
az acr build \
  --registry $REGISTRY_NAME \
  --image mcp-server-frontend:latest \
  --file Dockerfile \
  --target frontend \
  .
```

### Step 4: Deploy Infrastructure
```bash
az deployment group create \
  --name mcp-deployment \
  --resource-group $RESOURCE_GROUP \
  --template-file infra/main.bicep \
  --parameters @infra/parameters.${ENVIRONMENT}.json
```

### Step 5: Get Deployment Outputs
```bash
# Backend URL
az deployment group show \
  --name mcp-deployment \
  --resource-group $RESOURCE_GROUP \
  --query properties.outputs.backendAppUrl.value \
  --output tsv

# Frontend URL
az deployment group show \
  --name mcp-deployment \
  --resource-group $RESOURCE_GROUP \
  --query properties.outputs.frontendAppUrl.value \
  --output tsv

# Key Vault Name
az deployment group show \
  --name mcp-deployment \
  --resource-group $RESOURCE_GROUP \
  --query properties.outputs.keyVaultName.value \
  --output tsv
```

## Post-Deployment Configuration

### 1. Configure Tenants

#### Option A: Using Azure CLI
```bash
KEY_VAULT_NAME=$(az deployment group show \
  --name mcp-deployment \
  --resource-group $RESOURCE_GROUP \
  --query properties.outputs.keyVaultName.value \
  --output tsv)

# Create tenant configuration
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "tenant-default-config" \
  --value '{
    "id": "default",
    "name": "Default Tenant",
    "enabled": true,
    "foundry_endpoint": "https://foundry.azure.com/your-endpoint",
    "rate_limit_rpm": 100,
    "rate_limit_rpd": 10000,
    "quota_monthly_requests": 100000,
    "budget_threshold": 90,
    "budget_enforcement": "block"
  }'
```

#### Option B: Using Azure Portal
1. Navigate to Key Vault in Azure Portal
2. Go to **Secrets** → **Generate/Import**
3. Create secret: `tenant-{tenant-id}-config`
4. Paste tenant configuration JSON

### 2. Configure Global Branding
```bash
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "branding-global" \
  --value '{
    "primary_color": "#0078D4",
    "secondary_color": "#50E6FF",
    "accent_color": "#FFB900",
    "font_family": "Segoe UI, sans-serif",
    "app_name": "Enterprise MCP"
  }'
```

### 3. Upload Branding Assets
```bash
STORAGE_ACCOUNT=$(az deployment group show \
  --name mcp-deployment \
  --resource-group $RESOURCE_GROUP \
  --query properties.outputs.storageAccountName.value \
  --output tsv)

# Upload logo
az storage blob upload \
  --account-name $STORAGE_ACCOUNT \
  --container-name branding \
  --name global-logo.png \
  --file ./assets/logo.png \
  --content-type image/png
```

### 4. Configure FoundryIQ Endpoints
Update tenant configuration with your actual FoundryIQ endpoints:
```bash
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "tenant-default-config" \
  --value "$(az keyvault secret show \
    --vault-name $KEY_VAULT_NAME \
    --name tenant-default-config \
    --query value -o tsv | \
    jq '.foundry_endpoint = "https://your-actual-foundry-endpoint.com"')"
```

## Environment Variables

### Required Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `KEY_VAULT_URL` | Azure Key Vault URL | `https://mcp-dev-kv.vault.azure.net/` |
| `REDIS_URL` | Redis connection string | `mcp-redis.redis.cache.windows.net:6380,...` |
| `STORAGE_ACCOUNT_URL` | Blob Storage URL | `https://mcpstdev.blob.core.windows.net/` |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | App Insights | `InstrumentationKey=...` |

### Optional Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_ENTRA_AUTH` | Enable Entra ID auth | `false` |
| `LOCAL_DEV_MODE` | Enable mock services | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

## CI/CD Setup (GitHub Actions)

### 1. Create Azure Service Principal
```bash
az ad sp create-for-rbac \
  --name "github-actions-mcp-server" \
  --role Contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth
```

Copy the JSON output.

### 2. Configure GitHub Secrets

Navigate to: **Repository → Settings → Secrets and variables → Actions**

Add these secrets:
- `AZURE_CREDENTIALS`: JSON from step 1
- `AZURE_SUBSCRIPTION_ID`: Your subscription ID
- `ACR_LOGIN_SERVER`: `{registry}.azurecr.io`
- `ACR_USERNAME`: Registry admin username
- `ACR_PASSWORD`: Registry admin password

### 3. Trigger Deployment
```bash
# Push to main branch (prod deployment)
git push origin main

# Push to develop branch (dev deployment)
git push origin develop

# Manual deployment
gh workflow run deploy.yml -f environment=dev
```

## Monitoring and Operations

### View Logs
```bash
# Backend logs
az containerapp logs show \
  --name mcp-server-${ENVIRONMENT}-backend \
  --resource-group $RESOURCE_GROUP \
  --follow

# Frontend logs
az containerapp logs show \
  --name mcp-server-${ENVIRONMENT}-frontend \
  --resource-group $RESOURCE_GROUP \
  --follow
```

### View Application Insights
```bash
# Get App Insights portal link
az monitor app-insights component show \
  --app mcp-server-${ENVIRONMENT}-ai \
  --resource-group $RESOURCE_GROUP \
  --query appId -o tsv
```

Visit: `https://portal.azure.com/#@{tenant}/resource/{app-insights-id}/overview`

### Scale Container Apps
```bash
# Scale backend
az containerapp update \
  --name mcp-server-${ENVIRONMENT}-backend \
  --resource-group $RESOURCE_GROUP \
  --min-replicas 2 \
  --max-replicas 20

# Scale frontend
az containerapp update \
  --name mcp-server-${ENVIRONMENT}-frontend \
  --resource-group $RESOURCE_GROUP \
  --min-replicas 2 \
  --max-replicas 10
```

### Update Application
```bash
# Rebuild and deploy new version
az acr build \
  --registry $REGISTRY_NAME \
  --image mcp-server-backend:v2.0 \
  --file Dockerfile \
  --target backend \
  .

az containerapp update \
  --name mcp-server-${ENVIRONMENT}-backend \
  --resource-group $RESOURCE_GROUP \
  --image ${REGISTRY_NAME}.azurecr.io/mcp-server-backend:v2.0
```

## Cost Optimization

### Development Environment
- **Redis**: Standard C1 (~$55/month)
- **Container Apps**: 1-3 replicas, 0.5 CPU (~$40/month)
- **Storage**: LRS (~$5/month)
- **Key Vault**: Standard (~$5/month)
- **Total**: ~$105/month

### Production Environment
- **Redis**: Premium P1 (~$250/month)
- **Container Apps**: 2-10 replicas, 1.0 CPU (~$150/month)
- **Storage**: ZRS with CDN (~$20/month)
- **Key Vault**: Standard (~$5/month)
- **Total**: ~$425/month

### Cost Reduction Tips
1. **Use Azure Reserved Instances** for Container Apps (save 30-50%)
2. **Enable auto-shutdown** for dev environments during off-hours
3. **Use Standard Redis** instead of Premium for non-critical workloads
4. **Implement aggressive caching** to reduce compute costs
5. **Monitor and set budgets** with Azure Cost Management

## Troubleshooting

### Issue: Container App not starting
```bash
# Check deployment status
az containerapp revision list \
  --name mcp-server-${ENVIRONMENT}-backend \
  --resource-group $RESOURCE_GROUP \
  --output table

# View logs
az containerapp logs show \
  --name mcp-server-${ENVIRONMENT}-backend \
  --resource-group $RESOURCE_GROUP \
  --tail 100
```

### Issue: Cannot connect to Redis
```bash
# Check Redis status
az redis show \
  --name mcp-server-${ENVIRONMENT}-redis-{suffix} \
  --resource-group $RESOURCE_GROUP \
  --query provisioningState

# Test Redis connection
redis-cli -h {hostname} -p 6380 --tls -a {access-key} PING
```

### Issue: Key Vault access denied
```bash
# Check RBAC assignments
az role assignment list \
  --scope /subscriptions/{sub-id}/resourceGroups/$RESOURCE_GROUP \
  --assignee {managed-identity-principal-id}

# Grant missing permissions
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee {managed-identity-principal-id} \
  --scope {key-vault-resource-id}
```

### Issue: High costs
```bash
# View cost analysis
az consumption usage list \
  --start-date $(date -d '30 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --query "[?contains(instanceName, 'mcp-server')].{Name:instanceName, Cost:pretaxCost}" \
  --output table
```

## Next Steps

1. ✅ **Configure Tenants**: Add tenant configurations to Key Vault
2. ✅ **Set Up FoundryIQ**: Configure actual FoundryIQ endpoints
3. ✅ **Upload Branding**: Add logos and brand assets
4. ✅ **Configure Budgets**: Set cost limits and alerts
5. ✅ **Enable Monitoring**: Set up Application Insights dashboards
6. ✅ **Test End-to-End**: Verify all functionality works
7. ✅ **Document Operations**: Create runbooks for common tasks

## Additional Resources

- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Bicep Language Reference](https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Application Insights](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)
- [Redis Cache Best Practices](https://docs.microsoft.com/en-us/azure/azure-cache-for-redis/cache-best-practices)
- [Disaster Recovery Guide](./disaster-recovery.md)
- [API Specification](./api-spec.yaml)
