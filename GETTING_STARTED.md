# 🚀 Getting Started Guide

Complete guide to deploying the Enterprise MCP Server from scratch, including GitHub and Azure setup.

## Prerequisites

Before you begin, ensure you have:
- ✅ Active Azure subscription ([Get free account](https://azure.microsoft.com/free/))
- ✅ GitHub account ([Sign up free](https://github.com/join))
- ✅ Local machine with admin access

**Time to complete**: 30-45 minutes

---

## Step 1: Install Required Tools (10 minutes)

### Windows
```powershell
# Install Chocolatey (package manager)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Install tools
choco install git azure-cli docker-desktop python nodejs -y

# Restart terminal, then verify
git --version
az --version
docker --version
python --version
node --version
```

### macOS
```bash
# Install Homebrew (package manager)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install tools
brew install git azure-cli docker python@3.12 node

# Verify installations
git --version
az --version
docker --version
python3 --version
node --version
```

### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install Python and Node
sudo apt install -y python3.12 python3-pip nodejs npm

# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Git (if not already installed)
sudo apt install -y git

# Verify installations
git --version
az --version
docker --version
python3 --version
node --version
```

---

## Step 2: Clone and Setup Repository (5 minutes)

```bash
# Clone the repository
git clone https://github.com/your-org/fabric-mcp-demo.git
cd fabric-mcp-demo

# Run local setup script
chmod +x scripts/init_local.sh
./scripts/init_local.sh

# This script will:
# - Create Python virtual environment
# - Install backend dependencies
# - Install frontend dependencies
# - Create .env file from template
# - Start local services with Docker Compose
```

### Verify Local Setup
```bash
# Check if services are running
docker ps

# Test backend (should return health status)
curl http://localhost:8000/health

# Visit API docs
open http://localhost:8000/docs  # macOS
start http://localhost:8000/docs # Windows
xdg-open http://localhost:8000/docs # Linux
```

---

## Step 3: Azure Setup (10 minutes)

### 3.1 Login to Azure
```bash
# Login with browser
az login

# List your subscriptions
az account list --output table

# Set the subscription you want to use
az account set --subscription "Your Subscription Name"

# Verify current subscription
az account show --query "{Name:name, SubscriptionId:id}" --output table
```

### 3.2 Check Your Permissions
```bash
# Check if you have Contributor/Owner role
az role assignment list --assignee $(az account show --query user.name -o tsv) \
  --query "[?roleDefinitionName=='Owner' || roleDefinitionName=='Contributor'].{Role:roleDefinitionName, Scope:scope}" \
  --output table
```

**If you don't have permissions**, ask your Azure administrator to grant you:
- **Contributor** role (minimum)
- **Owner** role (recommended for full automation)

### 3.3 Choose Resource Names
```bash
# Set environment variables (customize these)
export ENVIRONMENT="dev"                    # or "prod"
export LOCATION="eastus"                    # or "westus", "northeurope", etc.
export RESOURCE_GROUP="mcp-server-${ENVIRONMENT}"
export CONTAINER_REGISTRY="mcpserver${ENVIRONMENT}$(date +%s | tail -c 5)"  # Must be globally unique

# Verify names are available
echo "Resource Group: $RESOURCE_GROUP"
echo "Registry: $CONTAINER_REGISTRY"
echo "Location: $LOCATION"
```

---

## Step 4: GitHub + Azure Integration (15 minutes)

You have two options: **Federated Credentials (Recommended)** or **Service Principal with Secrets**.

### Option A: Federated Credentials (Recommended - More Secure)

This method doesn't require storing secrets in GitHub.

#### 4.1 Create Azure AD App Registration
```bash
# Create app registration
APP_NAME="github-actions-mcp-server"
APP_ID=$(az ad app create \
  --display-name "$APP_NAME" \
  --query appId -o tsv)

echo "App ID: $APP_ID"

# Create service principal
SP_ID=$(az ad sp create --id $APP_ID --query id -o tsv)
echo "Service Principal ID: $SP_ID"
```

#### 4.2 Grant Azure Permissions
```bash
# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Grant Contributor role to the service principal
az role assignment create \
  --role Contributor \
  --assignee $APP_ID \
  --scope /subscriptions/$SUBSCRIPTION_ID

echo "✓ Permissions granted"
```

#### 4.3 Configure Federated Credentials
```bash
# Get your GitHub details
read -p "Enter your GitHub username: " GITHUB_USER
read -p "Enter your repository name: " GITHUB_REPO

# Create federated credential for main branch
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-deploy-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:'"$GITHUB_USER"'/'"$GITHUB_REPO"':ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# Create federated credential for develop branch
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-deploy-develop",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:'"$GITHUB_USER"'/'"$GITHUB_REPO"':ref:refs/heads/develop",
    "audiences": ["api://AzureADTokenExchange"]
  }'

echo "✓ Federated credentials configured"
```

#### 4.4 Add GitHub Secrets
```bash
# Print values to add to GitHub
echo ""
echo "================================================"
echo "Add these secrets to GitHub:"
echo "================================================"
echo "AZURE_CLIENT_ID: $APP_ID"
echo "AZURE_TENANT_ID: $(az account show --query tenantId -o tsv)"
echo "AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
echo ""
echo "Go to: https://github.com/$GITHUB_USER/$GITHUB_REPO/settings/secrets/actions"
echo "================================================"
```

**In GitHub**:
1. Go to your repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret:
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`

#### 4.5 Update GitHub Workflow for Federated Auth

Create `.github/workflows/deploy.yml` with federated auth:

```yaml
# Add this to the deploy job
- name: Azure Login (Federated)
  uses: azure/login@v1
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

### Option B: Service Principal with Secrets (Legacy Method)

If federated credentials don't work, use this method:

```bash
# Create service principal with password
SP_CREDS=$(az ad sp create-for-rbac \
  --name "github-actions-mcp-server" \
  --role Contributor \
  --scopes /subscriptions/$(az account show --query id -o tsv) \
  --sdk-auth)

# Print credentials
echo ""
echo "================================================"
echo "Add this as GitHub secret 'AZURE_CREDENTIALS':"
echo "================================================"
echo "$SP_CREDS"
echo "================================================"
```

**In GitHub**:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add secret `AZURE_CREDENTIALS` with the entire JSON output

### 4.6 Configure Container Registry Access

```bash
# The registry will be created during deployment, but we need to set up GitHub secrets

# After deployment, get ACR credentials
ACR_USERNAME=$(az acr credential show \
  --name $CONTAINER_REGISTRY \
  --query username -o tsv)

ACR_PASSWORD=$(az acr credential show \
  --name $CONTAINER_REGISTRY \
  --query passwords[0].value -o tsv)

echo ""
echo "================================================"
echo "Add these secrets to GitHub (after first deploy):"
echo "================================================"
echo "ACR_LOGIN_SERVER: ${CONTAINER_REGISTRY}.azurecr.io"
echo "ACR_USERNAME: $ACR_USERNAME"
echo "ACR_PASSWORD: $ACR_PASSWORD"
echo "================================================"
```

---

## Step 5: Deploy to Azure (10 minutes)

### 5.1 Deploy Infrastructure

```bash
# Deploy using the provisioning script
./scripts/provision_azure.sh \
  -e $ENVIRONMENT \
  -l $LOCATION \
  -g $RESOURCE_GROUP \
  -r $CONTAINER_REGISTRY

# This will:
# ✓ Create resource group
# ✓ Create container registry
# ✓ Build Docker images
# ✓ Deploy all Azure resources
# ✓ Configure RBAC permissions
# ✓ Display deployment URLs
```

### 5.2 Save Deployment Information

The script will output important URLs. **Save these**:

```
Application URLs:
  Frontend:          https://mcp-server-dev-frontend.xxx.eastus.azurecontainerapps.io
  Backend API:       https://mcp-server-dev-backend.xxx.eastus.azurecontainerapps.io
  API Docs:          https://mcp-server-dev-backend.xxx.eastus.azurecontainerapps.io/docs

Azure Resources:
  Key Vault:         mcp-server-dev-kv-xxxxx
  Redis:             mcp-server-dev-redis-xxxxx.redis.cache.windows.net
  Registry:          mcpserverdevXXXXX.azurecr.io
```

### 5.3 Verify Deployment

```bash
# Get backend URL from deployment
BACKEND_URL=$(az deployment group show \
  --name $(az deployment group list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv) \
  --resource-group $RESOURCE_GROUP \
  --query properties.outputs.backendAppUrl.value -o tsv)

# Test health endpoint
curl "$BACKEND_URL/health"

# Test API
curl -H "X-Tenant-ID: default" "$BACKEND_URL/api/agents"

# Open API docs in browser
open "${BACKEND_URL}/docs"  # macOS
start "${BACKEND_URL}/docs" # Windows
xdg-open "${BACKEND_URL}/docs" # Linux
```

---

## Step 6: Configure Your First Tenant (5 minutes)

### 6.1 Get Key Vault Name

```bash
KEY_VAULT_NAME=$(az deployment group show \
  --name $(az deployment group list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv) \
  --resource-group $RESOURCE_GROUP \
  --query properties.outputs.keyVaultName.value -o tsv)

echo "Key Vault: $KEY_VAULT_NAME"
```

### 6.2 Create Tenant Configuration

```bash
# Create your first tenant
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "tenant-customer1-config" \
  --value '{
    "id": "customer1",
    "name": "Customer One",
    "enabled": true,
    "foundry_endpoint": "https://foundry.azure.com/your-endpoint",
    "rate_limit_rpm": 100,
    "rate_limit_rpd": 10000,
    "quota_monthly_requests": 100000,
    "budget_limit": 1000.00,
    "budget_threshold": 90,
    "budget_enforcement": "warn",
    "notification_channels": ["in-app"]
  }'

echo "✓ Tenant configured"
```

### 6.3 Test Your Tenant

```bash
# Test with your new tenant
curl -H "X-Tenant-ID: customer1" "$BACKEND_URL/api/agents"

# Test chat
curl -X POST "$BACKEND_URL/api/chat" \
  -H "X-Tenant-ID: customer1" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, what can you help me with?",
    "agent_id": "sales-001"
  }'
```

---

## Step 7: Configure CI/CD (5 minutes)

### 7.1 Update GitHub Secrets

After deployment, add ACR credentials to GitHub:

```bash
# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $CONTAINER_REGISTRY --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $CONTAINER_REGISTRY --query passwords[0].value -o tsv)

echo "Add these to GitHub Secrets:"
echo "ACR_LOGIN_SERVER: ${CONTAINER_REGISTRY}.azurecr.io"
echo "ACR_USERNAME: $ACR_USERNAME"
echo "ACR_PASSWORD: $ACR_PASSWORD"
```

### 7.2 Test CI/CD Pipeline

```bash
# Make a small change
echo "# Test deployment" >> README.md

# Commit and push
git add README.md
git commit -m "test: trigger deployment pipeline"
git push origin develop  # or main for prod

# Watch GitHub Actions
open "https://github.com/$GITHUB_USER/$GITHUB_REPO/actions"
```

---

## Step 8: Customize Branding (Optional)

```bash
# Set global branding
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "branding-global" \
  --value '{
    "primary_color": "#0078D4",
    "secondary_color": "#50E6FF",
    "accent_color": "#FFB900",
    "font_family": "Segoe UI, sans-serif",
    "app_name": "My MCP Server",
    "logo_url": "https://yourcdn.com/logo.png"
  }'

# Upload logo via API
curl -X POST "$BACKEND_URL/api/branding/logo" \
  -H "X-Tenant-ID: customer1" \
  -F "file=@./path/to/logo.png"
```

---

## Step 9: Set Up Monitoring (Optional)

### 9.1 Import Workbooks

```bash
# Get Application Insights resource ID
APP_INSIGHTS_ID=$(az monitor app-insights component show \
  --app mcp-server-${ENVIRONMENT}-ai \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

# Import tenant usage workbook
az monitor app-insights workbook create \
  --resource-group $RESOURCE_GROUP \
  --name "tenant-usage" \
  --display-name "Tenant Usage Dashboard" \
  --source-id $APP_INSIGHTS_ID \
  --template-data @infra/workbooks/tenant-usage.json

echo "✓ Workbooks imported"
```

### 9.2 Configure Alerts

```bash
# Create alert for high error rate
az monitor metrics alert create \
  --name "high-error-rate" \
  --resource-group $RESOURCE_GROUP \
  --scopes $APP_INSIGHTS_ID \
  --condition "avg requests/failed > 10" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action email your-email@company.com

echo "✓ Alerts configured"
```

---

## 🎉 Success!

You now have a fully deployed Enterprise MCP Server!

### What You Can Do Now:

1. **Access your application**:
   - Frontend: Visit your frontend URL
   - API Docs: Visit `{backend-url}/docs`

2. **Add more tenants**: Use Key Vault or the API

3. **Configure FoundryIQ**: Update tenant configs with real endpoints

4. **Upload branding**: Customize look and feel per tenant

5. **Monitor**: Check Application Insights dashboards

---

## Common Issues & Solutions

### Issue: "az: command not found"
```bash
# Reinstall Azure CLI
# Windows: choco install azure-cli -y
# macOS: brew install azure-cli
# Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### Issue: "Permission denied" on scripts
```bash
chmod +x scripts/*.sh
```

### Issue: "Container registry name not available"
```bash
# Try a different registry name (must be globally unique)
export CONTAINER_REGISTRY="mcpserver${ENVIRONMENT}$(date +%s | tail -c 5)"
```

### Issue: "GitHub Actions not running"
```bash
# Verify GitHub secrets are set
# Go to: Settings → Secrets and variables → Actions
# Ensure all required secrets are present
```

### Issue: "Can't connect to backend"
```bash
# Check if container apps are running
az containerapp list \
  --resource-group $RESOURCE_GROUP \
  --output table

# View logs
az containerapp logs show \
  --name mcp-server-${ENVIRONMENT}-backend \
  --resource-group $RESOURCE_GROUP \
  --tail 100
```

---

## Next Steps

After completing this guide:

1. ✅ **[Set Up Security & Authentication](docs/SECURITY_SETUP.md)** - Configure Entra ID and admin access
2. ✅ **[Configure Real FoundryIQ](docs/deployment.md#post-deployment-configuration)** - Connect to actual endpoints
3. ✅ **[Review Security Hardening](docs/deployment.md#security-hardening)** - Network rules and compliance
4. ✅ **[Set Up Monitoring](docs/deployment.md#monitoring-and-operations)** - Configure alerts and dashboards
5. ✅ **[Review Costs](docs/deployment.md#cost-optimization)** - Optimize resource allocation
5. ✅ **[Disaster Recovery](docs/disaster-recovery.md)** - Test backup and restore procedures

## Additional Resources

- 📖 [Full Deployment Guide](docs/deployment.md)
- 🚨 [Disaster Recovery](docs/disaster-recovery.md)
- 📊 [API Documentation](docs/api-spec.yaml)
- 🎨 [Branding Customization](docs/branding-guide.md)
- ✅ [Deployment Checklist](DEPLOYMENT_CHECKLIST.md)

---

**Need Help?**
- Review the [Troubleshooting Guide](docs/deployment.md#troubleshooting)
- Check [Common Issues](#common-issues--solutions) above
- Open a GitHub issue with deployment logs
