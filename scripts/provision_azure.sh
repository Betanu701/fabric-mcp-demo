#!/bin/bash
# Azure resource provisioning script for Enterprise MCP Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
LOCATION="eastus"
RESOURCE_GROUP=""
SUBSCRIPTION_ID=""
CONTAINER_REGISTRY=""
SKIP_BUILD=false

# Help function
show_help() {
    echo -e "${BLUE}Azure MCP Server Provisioning Script${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV      Environment name (dev, staging, prod). Default: dev"
    echo "  -l, --location LOCATION    Azure region. Default: eastus"
    echo "  -g, --resource-group RG    Resource group name. Default: mcp-server-ENV"
    echo "  -s, --subscription ID      Azure subscription ID. Default: current subscription"
    echo "  -r, --registry NAME        Container registry name. Default: mcpserverENV"
    echo "  --skip-build               Skip Docker image build"
    echo "  -h, --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -e dev -l eastus"
    echo "  $0 -e prod -g mcp-production -r mcpprod"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -s|--subscription)
            SUBSCRIPTION_ID="$2"
            shift 2
            ;;
        -r|--registry)
            CONTAINER_REGISTRY="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Set defaults if not provided
RESOURCE_GROUP=${RESOURCE_GROUP:-"mcp-server-${ENVIRONMENT}"}
CONTAINER_REGISTRY=${CONTAINER_REGISTRY:-"mcpserver${ENVIRONMENT}"}

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Enterprise MCP Server - Azure Provisioning${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  Environment:      $ENVIRONMENT"
echo "  Location:         $LOCATION"
echo "  Resource Group:   $RESOURCE_GROUP"
echo "  Registry:         $CONTAINER_REGISTRY"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed${NC}"
    echo "Please install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in
echo -e "${YELLOW}→ Checking Azure login status...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${RED}Error: Not logged in to Azure${NC}"
    echo "Please run: az login"
    exit 1
fi

# Set subscription if provided
if [ -n "$SUBSCRIPTION_ID" ]; then
    echo -e "${YELLOW}→ Setting subscription to $SUBSCRIPTION_ID...${NC}"
    az account set --subscription "$SUBSCRIPTION_ID"
fi

CURRENT_SUB=$(az account show --query name -o tsv)
echo -e "${GREEN}✓ Using subscription: $CURRENT_SUB${NC}"
echo ""

# Create resource group
echo -e "${YELLOW}→ Creating resource group: $RESOURCE_GROUP...${NC}"
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --tags "Environment=$ENVIRONMENT" "Application=Enterprise-MCP-Server" \
    --output none

echo -e "${GREEN}✓ Resource group created${NC}"
echo ""

# Create Container Registry
echo -e "${YELLOW}→ Creating Container Registry: $CONTAINER_REGISTRY...${NC}"
if ! az acr show --name "$CONTAINER_REGISTRY" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    az acr create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$CONTAINER_REGISTRY" \
        --sku Standard \
        --admin-enabled true \
        --location "$LOCATION" \
        --output none
    
    echo -e "${GREEN}✓ Container Registry created${NC}"
else
    echo -e "${GREEN}✓ Container Registry already exists${NC}"
fi
echo ""

# Build and push Docker images
if [ "$SKIP_BUILD" = false ]; then
    echo -e "${YELLOW}→ Building and pushing Docker images...${NC}"
    
    # Backend image
    echo -e "  ${BLUE}Building backend image...${NC}"
    az acr build \
        --registry "$CONTAINER_REGISTRY" \
        --image "mcp-server-backend:latest" \
        --image "mcp-server-backend:${ENVIRONMENT}" \
        --file Dockerfile \
        --target backend \
        .
    
    # Frontend image
    echo -e "  ${BLUE}Building frontend image...${NC}"
    az acr build \
        --registry "$CONTAINER_REGISTRY" \
        --image "mcp-server-frontend:latest" \
        --image "mcp-server-frontend:${ENVIRONMENT}" \
        --file Dockerfile \
        --target frontend \
        .
    
    echo -e "${GREEN}✓ Docker images built and pushed${NC}"
    echo ""
else
    echo -e "${YELLOW}⊘ Skipping Docker build (--skip-build)${NC}"
    echo ""
fi

# Deploy infrastructure with Bicep
echo -e "${YELLOW}→ Deploying Azure infrastructure with Bicep...${NC}"
DEPLOYMENT_NAME="mcp-deployment-$(date +%Y%m%d-%H%M%S)"
PARAMS_FILE="infra/parameters.${ENVIRONMENT}.json"

if [ ! -f "$PARAMS_FILE" ]; then
    echo -e "${RED}Error: Parameters file not found: $PARAMS_FILE${NC}"
    exit 1
fi

# Update parameters file with actual container registry name
TEMP_PARAMS=$(mktemp)
jq --arg registry "$CONTAINER_REGISTRY" \
   '.parameters.containerRegistryName.value = $registry' \
   "$PARAMS_FILE" > "$TEMP_PARAMS"

az deployment group create \
    --name "$DEPLOYMENT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --template-file infra/main.bicep \
    --parameters "@${TEMP_PARAMS}" \
    --output table

rm "$TEMP_PARAMS"

echo -e "${GREEN}✓ Infrastructure deployed${NC}"
echo ""

# Get outputs
echo -e "${YELLOW}→ Retrieving deployment outputs...${NC}"
BACKEND_URL=$(az deployment group show \
    --name "$DEPLOYMENT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query properties.outputs.backendAppUrl.value \
    --output tsv)

FRONTEND_URL=$(az deployment group show \
    --name "$DEPLOYMENT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query properties.outputs.frontendAppUrl.value \
    --output tsv)

KEY_VAULT_NAME=$(az deployment group show \
    --name "$DEPLOYMENT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query properties.outputs.keyVaultName.value \
    --output tsv)

REDIS_HOSTNAME=$(az deployment group show \
    --name "$DEPLOYMENT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query properties.outputs.redisHostName.value \
    --output tsv)

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Deployment Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Deployment Information:${NC}"
echo "  Resource Group:    $RESOURCE_GROUP"
echo "  Environment:       $ENVIRONMENT"
echo "  Location:          $LOCATION"
echo ""
echo -e "${GREEN}Application URLs:${NC}"
echo "  Frontend:          $FRONTEND_URL"
echo "  Backend API:       $BACKEND_URL"
echo "  API Docs:          ${BACKEND_URL}/docs"
echo ""
echo -e "${GREEN}Azure Resources:${NC}"
echo "  Key Vault:         $KEY_VAULT_NAME"
echo "  Redis:             $REDIS_HOSTNAME"
echo "  Registry:          ${CONTAINER_REGISTRY}.azurecr.io"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Configure tenants in Key Vault"
echo "  2. Set up FoundryIQ endpoints"
echo "  3. Upload branding assets to Blob Storage"
echo "  4. Configure budgets and alerts"
echo "  5. Visit frontend URL to complete setup wizard"
echo ""
echo -e "${GREEN}To view resources:${NC}"
echo "  az resource list --resource-group $RESOURCE_GROUP --output table"
echo ""
echo -e "${GREEN}To view logs:${NC}"
echo "  az containerapp logs show --name mcp-server-${ENVIRONMENT}-backend --resource-group $RESOURCE_GROUP --follow"
echo ""
