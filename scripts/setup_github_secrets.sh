#!/bin/bash
# Automated GitHub Secrets Setup for Azure Deployment
# This script will configure all required GitHub secrets for CI/CD deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    GitHub Secrets Setup for Azure Deployment     ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) not found.${NC}"
    echo -e "${YELLOW}Install it with:${NC}"
    echo "  - macOS: brew install gh"
    echo "  - Windows: choco install gh"
    echo "  - Linux: https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
    exit 1
fi

# Check if logged into Azure
echo -e "${YELLOW}Checking Azure login...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${RED}Not logged into Azure. Running 'az login'...${NC}"
    az login
fi

# Check if logged into GitHub
echo -e "${YELLOW}Checking GitHub login...${NC}"
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Not logged into GitHub. Running 'gh auth login'...${NC}"
    gh auth login
fi

# Get current Azure context
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)

echo ""
echo -e "${GREEN}✓ Prerequisites met${NC}"
echo -e "${BLUE}Azure Subscription:${NC} $SUBSCRIPTION_NAME"
echo -e "${BLUE}Subscription ID:${NC} $SUBSCRIPTION_ID"
echo -e "${BLUE}Tenant ID:${NC} $TENANT_ID"
echo ""

# Get GitHub repository info
echo -e "${YELLOW}Detecting GitHub repository...${NC}"
REPO_FULL=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")

if [ -z "$REPO_FULL" ]; then
    echo -e "${RED}Could not detect GitHub repository from current directory.${NC}"
    echo -e "${YELLOW}Please enter your GitHub repository (format: owner/repo):${NC}"
    read -p "Repository: " REPO_FULL
fi

REPO_OWNER=$(echo $REPO_FULL | cut -d'/' -f1)
REPO_NAME=$(echo $REPO_FULL | cut -d'/' -f2)

echo -e "${GREEN}✓ Repository detected:${NC} $REPO_FULL"
echo ""

# Ask for confirmation
echo -e "${YELLOW}This script will:${NC}"
echo "  1. Create an Azure Service Principal with Contributor access"
echo "  2. Set up GitHub OIDC federation for secure authentication"
echo "  3. Automatically add secrets to your GitHub repository:"
echo "     - AZURE_CLIENT_ID"
echo "     - AZURE_TENANT_ID"
echo "     - AZURE_SUBSCRIPTION_ID"
echo "  4. Create Azure Container Registry credentials"
echo "     - ACR_LOGIN_SERVER"
echo "     - ACR_USERNAME"
echo "     - ACR_PASSWORD"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${RED}Aborted by user${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 1: Creating Azure Service Principal${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"

# Create Service Principal
SP_NAME="github-actions-${REPO_NAME}-$(date +%s)"
echo -e "${YELLOW}Creating Service Principal: $SP_NAME${NC}"

# Create the service principal with Contributor role
SP_OUTPUT=$(az ad sp create-for-rbac \
    --name "$SP_NAME" \
    --role Contributor \
    --scopes "/subscriptions/$SUBSCRIPTION_ID" \
    --sdk-auth)

CLIENT_ID=$(echo $SP_OUTPUT | jq -r '.clientId')
echo -e "${GREEN}✓ Service Principal created${NC}"
echo -e "${BLUE}Client ID:${NC} $CLIENT_ID"

# Wait a moment for Azure AD propagation
sleep 5

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 2: Setting up GitHub OIDC Federation${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"

# Create federated credential for GitHub Actions
echo -e "${YELLOW}Creating federated credential for main branch...${NC}"
az ad app federated-credential create \
    --id $CLIENT_ID \
    --parameters '{
        "name": "github-main-branch",
        "issuer": "https://token.actions.githubusercontent.com",
        "subject": "repo:'"$REPO_FULL"':ref:refs/heads/main",
        "audiences": ["api://AzureADTokenExchange"]
    }' 2>/dev/null || echo -e "${YELLOW}Note: Federated credential may already exist${NC}"

echo -e "${YELLOW}Creating federated credential for pull requests...${NC}"
az ad app federated-credential create \
    --id $CLIENT_ID \
    --parameters '{
        "name": "github-pull-requests",
        "issuer": "https://token.actions.githubusercontent.com",
        "subject": "repo:'"$REPO_FULL"':pull_request",
        "audiences": ["api://AzureADTokenExchange"]
    }' 2>/dev/null || echo -e "${YELLOW}Note: Federated credential may already exist${NC}"

echo -e "${GREEN}✓ OIDC federation configured${NC}"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 3: Adding Secrets to GitHub${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"

# Add Azure secrets to GitHub
echo -e "${YELLOW}Adding AZURE_CLIENT_ID...${NC}"
echo "$CLIENT_ID" | gh secret set AZURE_CLIENT_ID -R "$REPO_FULL"

echo -e "${YELLOW}Adding AZURE_TENANT_ID...${NC}"
echo "$TENANT_ID" | gh secret set AZURE_TENANT_ID -R "$REPO_FULL"

echo -e "${YELLOW}Adding AZURE_SUBSCRIPTION_ID...${NC}"
echo "$SUBSCRIPTION_ID" | gh secret set AZURE_SUBSCRIPTION_ID -R "$REPO_FULL"

echo -e "${GREEN}✓ Azure secrets added to GitHub${NC}"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 4: Azure Container Registry Setup${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"

# Check if ACR exists
echo -e "${YELLOW}Looking for existing Azure Container Registry...${NC}"
ACR_LIST=$(az acr list --query "[].{name:name, resourceGroup:resourceGroup}" -o json)
ACR_COUNT=$(echo $ACR_LIST | jq '. | length')

if [ "$ACR_COUNT" -eq "0" ]; then
    echo -e "${YELLOW}No Azure Container Registry found.${NC}"
    echo -e "${YELLOW}You'll need to create one during deployment.${NC}"
    echo -e "${YELLOW}For now, setting placeholder values...${NC}"
    
    ACR_NAME="mcp-${REPO_NAME}-registry"
    echo -e "${YELLOW}Adding ACR_LOGIN_SERVER (placeholder)...${NC}"
    echo "${ACR_NAME}.azurecr.io" | gh secret set ACR_LOGIN_SERVER -R "$REPO_FULL"
    
    echo -e "${YELLOW}⚠ You'll need to create the ACR and update these secrets after deployment:${NC}"
    echo "  - ACR_USERNAME"
    echo "  - ACR_PASSWORD"
elif [ "$ACR_COUNT" -eq "1" ]; then
    # Single ACR found, use it
    ACR_NAME=$(echo $ACR_LIST | jq -r '.[0].name')
    ACR_RG=$(echo $ACR_LIST | jq -r '.[0].resourceGroup')
    
    echo -e "${GREEN}✓ Found Azure Container Registry: $ACR_NAME${NC}"
    
    # Get ACR credentials
    ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
    ACR_CREDS=$(az acr credential show --name $ACR_NAME --resource-group $ACR_RG)
    ACR_USERNAME=$(echo $ACR_CREDS | jq -r '.username')
    ACR_PASSWORD=$(echo $ACR_CREDS | jq -r '.passwords[0].value')
    
    echo -e "${YELLOW}Adding ACR_LOGIN_SERVER...${NC}"
    echo "$ACR_LOGIN_SERVER" | gh secret set ACR_LOGIN_SERVER -R "$REPO_FULL"
    
    echo -e "${YELLOW}Adding ACR_USERNAME...${NC}"
    echo "$ACR_USERNAME" | gh secret set ACR_USERNAME -R "$REPO_FULL"
    
    echo -e "${YELLOW}Adding ACR_PASSWORD...${NC}"
    echo "$ACR_PASSWORD" | gh secret set ACR_PASSWORD -R "$REPO_FULL"
    
    echo -e "${GREEN}✓ ACR credentials added to GitHub${NC}"
else
    # Multiple ACRs found, ask user to choose
    echo -e "${YELLOW}Multiple Azure Container Registries found:${NC}"
    echo "$ACR_LIST" | jq -r '.[] | "  - \(.name) (Resource Group: \(.resourceGroup))"'
    echo ""
    read -p "Enter the ACR name to use: " ACR_NAME
    
    ACR_RG=$(echo $ACR_LIST | jq -r ".[] | select(.name==\"$ACR_NAME\") | .resourceGroup")
    
    if [ -z "$ACR_RG" ]; then
        echo -e "${RED}Error: ACR '$ACR_NAME' not found${NC}"
        exit 1
    fi
    
    # Get ACR credentials
    ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
    ACR_CREDS=$(az acr credential show --name $ACR_NAME --resource-group $ACR_RG)
    ACR_USERNAME=$(echo $ACR_CREDS | jq -r '.username')
    ACR_PASSWORD=$(echo $ACR_CREDS | jq -r '.passwords[0].value')
    
    echo -e "${YELLOW}Adding ACR_LOGIN_SERVER...${NC}"
    echo "$ACR_LOGIN_SERVER" | gh secret set ACR_LOGIN_SERVER -R "$REPO_FULL"
    
    echo -e "${YELLOW}Adding ACR_USERNAME...${NC}"
    echo "$ACR_USERNAME" | gh secret set ACR_USERNAME -R "$REPO_FULL"
    
    echo -e "${YELLOW}Adding ACR_PASSWORD...${NC}"
    echo "$ACR_PASSWORD" | gh secret set ACR_PASSWORD -R "$REPO_FULL"
    
    echo -e "${GREEN}✓ ACR credentials added to GitHub${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}           ✓ Setup Complete!                       ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo "  Service Principal: $SP_NAME"
echo "  Client ID: $CLIENT_ID"
echo "  Repository: $REPO_FULL"
echo ""
echo -e "${BLUE}GitHub Secrets Configured:${NC}"
echo "  ✓ AZURE_CLIENT_ID"
echo "  ✓ AZURE_TENANT_ID"
echo "  ✓ AZURE_SUBSCRIPTION_ID"
echo "  ✓ ACR_LOGIN_SERVER"
if [ "$ACR_COUNT" -gt "0" ]; then
    echo "  ✓ ACR_USERNAME"
    echo "  ✓ ACR_PASSWORD"
fi
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Run deployment: ./scripts/provision_azure.sh -e dev -l eastus"
echo "  2. Push to GitHub: git push origin main"
echo "  3. GitHub Actions will automatically deploy your changes"
echo ""
echo -e "${GREEN}You're ready to deploy! 🚀${NC}"
