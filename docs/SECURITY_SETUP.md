# 🔒 Security & Authentication Setup

This guide covers Azure permissions, Entra ID authentication, and role-based access control for the admin portal.

## Table of Contents
- [Overview](#overview)
- [Azure Permissions Required](#azure-permissions-required)
- [Entra ID Setup](#entra-id-setup)
- [Admin Portal Access Control](#admin-portal-access-control)
- [Security Best Practices](#security-best-practices)

---

## Overview

The MCP server supports two authentication modes:

1. **Development Mode** (Current Default)
   - No authentication required
   - All admin endpoints accessible
   - Suitable for local development and testing

2. **Production Mode with Entra ID** (Recommended)
   - Azure AD/Entra ID authentication required
   - Role-based access control (RBAC)
   - Secure admin portal access
   - API authentication via Bearer tokens

---

## Azure Permissions Required

### For Deployment & Infrastructure Setup

The person deploying the infrastructure needs these Azure permissions:

#### Minimum Required (Deployment Only)
```
Subscription Level:
├── Contributor
└── User Access Administrator (for role assignments)
```

#### Recommended (Full Control)
```
Subscription Level:
└── Owner
```

### Specific Resource Permissions

If not using Owner/Contributor, grant these specific roles:

```yaml
Resource Groups:
  - Resource Group Contributor

Azure Container Apps:
  - Azure Container Apps Contributor
  
Azure Cache for Redis:
  - Redis Cache Contributor
  
Azure Key Vault:
  - Key Vault Administrator (or)
  - Key Vault Secrets Officer

Azure Storage:
  - Storage Blob Data Contributor
  - Storage Account Contributor

Azure Container Registry:
  - AcrPush (for image uploads)
  - AcrPull (for deployments)

Azure Monitor:
  - Monitoring Metrics Publisher
  - Application Insights Component Contributor

Azure Cost Management:
  - Cost Management Reader
  - Cost Management Contributor (for budget alerts)
```

### Check Your Permissions

```bash
# Check subscription-level roles
az role assignment list \
  --assignee $(az account show --query user.name -o tsv) \
  --scope "/subscriptions/$(az account show --query id -o tsv)" \
  --query "[].{Role:roleDefinitionName, Scope:scope}" \
  --output table

# Check if you can create resources
az group create --name test-permissions-check --location eastus
az group delete --name test-permissions-check --yes --no-wait
```

---

## Entra ID Setup

### Prerequisites

- Azure AD/Entra ID tenant
- Global Administrator or Application Administrator role
- Access to Azure Portal

### Step 1: Register Application in Entra ID

1. **Go to Azure Portal** → **Azure Active Directory** → **App registrations**
2. Click **New registration**
3. Fill in the details:
   ```
   Name: MCP Server Admin Portal
   Supported account types: Single tenant
   Redirect URI: 
     - Type: Web
     - URI: https://your-frontend-url.azurecontainerapps.io/auth/callback
     - URI: http://localhost:5173/auth/callback (for development)
   ```
4. Click **Register**

### Step 2: Configure Authentication

1. Go to **Authentication** section
2. Under **Implicit grant and hybrid flows**, enable:
   - ✅ ID tokens (used for implicit and hybrid flows)
3. Under **Supported account types**: Single tenant
4. Add additional redirect URIs if needed:
   ```
   https://your-backend-url.azurecontainerapps.io/auth/callback
   ```

### Step 3: Create Client Secret

1. Go to **Certificates & secrets** → **Client secrets**
2. Click **New client secret**
3. Add description: "MCP Server Backend"
4. Set expiration: **24 months** (or per your policy)
5. Click **Add**
6. **Copy the secret value immediately** (you won't see it again)

### Step 4: Configure API Permissions

1. Go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Choose **Delegated permissions**
5. Add these permissions:
   ```
   User.Read          - Read user profile
   email              - View users' email address
   openid             - Sign in
   profile            - View users' basic profile
   ```
6. Click **Add permissions**
7. Click **Grant admin consent** (requires admin role)

### Step 5: Define App Roles (Admin Access)

1. Go to **App roles** → **Create app role**
2. Create **Admin** role:
   ```yaml
   Display name: MCP Administrator
   Value: mcp.admin
   Description: Full access to MCP admin portal and all operations
   Allowed member types: Users/Groups
   ```
3. Create **Cost Manager** role:
   ```yaml
   Display name: Cost Manager
   Value: mcp.cost.manager
   Description: Access to cost tracking, budgets, and financial reports
   Allowed member types: Users/Groups
   ```
4. Create **Agent Manager** role:
   ```yaml
   Display name: Agent Manager
   Value: mcp.agent.manager
   Description: Manage agents, discovery, and routing configuration
   Allowed member types: Users/Groups
   ```

### Step 6: Assign Users to Roles

1. Go to **Azure Portal** → **Enterprise applications**
2. Find your application: "MCP Server Admin Portal"
3. Go to **Users and groups**
4. Click **Add user/group**
5. Select user and assign role:
   - For full admin access: Assign **MCP Administrator** role
   - For cost management only: Assign **Cost Manager** role
   - For agent management: Assign **Agent Manager** role

### Step 7: Configure Application Settings

Update your environment variables:

```bash
# In .env or Azure Container App configuration
ENTRA_ENABLED=true
ENTRA_TENANT_ID=your-tenant-id-here
ENTRA_CLIENT_ID=your-client-id-here
ENTRA_CLIENT_SECRET=your-client-secret-here
ENTRA_AUTHORITY=https://login.microsoftonline.com/
```

Get these values:
- **Tenant ID**: Azure Portal → Azure Active Directory → Overview → Tenant ID
- **Client ID**: App registrations → Your app → Overview → Application (client) ID
- **Client Secret**: The value you copied in Step 3

---

## Admin Portal Access Control

### Role Permissions Matrix

| Feature | Admin | Cost Manager | Agent Manager | Regular User |
|---------|-------|--------------|---------------|--------------|
| View Dashboard | ✅ | ✅ | ✅ | ❌ |
| Manage Tenants | ✅ | ❌ | ❌ | ❌ |
| View Costs | ✅ | ✅ | ❌ | ❌ |
| Set Budgets | ✅ | ✅ | ❌ | ❌ |
| Discover Agents | ✅ | ❌ | ✅ | ❌ |
| Configure Agents | ✅ | ❌ | ✅ | ❌ |
| Manage Branding | ✅ | ❌ | ❌ | ❌ |
| View Notifications | ✅ | ✅ | ✅ | ❌ |
| System Settings | ✅ | ❌ | ❌ | ❌ |

### API Endpoint Protection

All admin endpoints require authentication when `ENTRA_ENABLED=true`:

```python
# Protected admin endpoints
/api/admin/*              # Requires: mcp.admin role
/api/tenants/*            # Requires: mcp.admin role
/api/costs/*              # Requires: mcp.admin OR mcp.cost.manager
/api/budgets/*            # Requires: mcp.admin OR mcp.cost.manager
/api/agents/discover      # Requires: mcp.admin OR mcp.agent.manager
/api/branding/*           # Requires: mcp.admin role
```

### Frontend Protection

The React admin portal checks authentication before rendering:

```typescript
// In App.tsx (to be implemented)
const { isAuthenticated, user, roles } = useAuth();

// Redirect to login if not authenticated
if (!isAuthenticated) {
  return <Redirect to="/login" />;
}

// Check admin role
if (!roles.includes('mcp.admin')) {
  return <AccessDenied />;
}
```

---

## Security Best Practices

### 1. Enable Entra ID in Production

```bash
# Never deploy to production with this:
ENTRA_ENABLED=false  # ❌ INSECURE

# Always use:
ENTRA_ENABLED=true   # ✅ SECURE
```

### 2. Use Managed Identities

The infrastructure uses Azure Managed Identity for service-to-service authentication:

```yaml
Services using Managed Identity:
  ✅ Container Apps → Key Vault (no secrets needed)
  ✅ Container Apps → Blob Storage (no connection strings)
  ✅ Container Apps → Redis (credential-free)
  ✅ Container Apps → Cost Management API
```

### 3. Secure Key Vault Access

```bash
# Key Vault should use RBAC, not access policies
az keyvault update --name your-keyvault \
  --enable-rbac-authorization true

# Audit Key Vault access
az monitor diagnostic-settings create \
  --resource /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.KeyVault/vaults/{vault} \
  --name audit-logs \
  --logs '[{"category": "AuditEvent", "enabled": true}]' \
  --workspace /subscriptions/{sub}/resourcegroups/{rg}/providers/microsoft.operationalinsights/workspaces/{workspace}
```

### 4. Network Security

```yaml
Recommended Azure networking:
  - Use Private Endpoints for Redis, Key Vault, Storage
  - Enable Container Apps ingress restrictions
  - Use Azure Firewall or NSGs for outbound filtering
  - Enable DDoS protection for production
```

### 5. Secret Rotation

```bash
# Rotate client secrets every 6-12 months
# Set calendar reminder to rotate before expiration

# Check secret expiration
az ad app credential list --id your-app-id \
  --query "[].{KeyId:keyId, EndDate:endDateTime}" \
  --output table
```

### 6. Monitor Authentication

```kusto
// Application Insights query to monitor auth failures
requests
| where url contains "/api/admin"
| where resultCode >= 401 and resultCode <= 403
| summarize FailureCount = count() by 
    User = tostring(customDimensions.user_id),
    Endpoint = url,
    ResultCode = resultCode
| order by FailureCount desc
```

---

## Quick Setup Script

Save this as `setup-entra-auth.sh`:

```bash
#!/bin/bash
# Quick Entra ID app registration for MCP Server

APP_NAME="MCP-Server-Admin"
FRONTEND_URL="https://your-frontend.azurecontainerapps.io"

echo "Creating Entra ID app registration..."

# Create app registration
APP_ID=$(az ad app create \
  --display-name "$APP_NAME" \
  --sign-in-audience AzureADMyOrg \
  --web-redirect-uris "$FRONTEND_URL/auth/callback" "http://localhost:5173/auth/callback" \
  --enable-id-token-issuance true \
  --query appId -o tsv)

echo "App ID: $APP_ID"

# Create client secret
SECRET=$(az ad app credential reset \
  --id $APP_ID \
  --append \
  --display-name "Backend Secret" \
  --query password -o tsv)

echo "Client Secret: $SECRET"

# Get tenant ID
TENANT_ID=$(az account show --query tenantId -o tsv)

echo "Tenant ID: $TENANT_ID"

# Add Microsoft Graph permissions
az ad app permission add \
  --id $APP_ID \
  --api 00000003-0000-0000-c000-000000000000 \
  --api-permissions \
    e1fe6dd8-ba31-4d61-89e7-88639da4683d=Scope \
    64a6cdd6-aab1-4aaf-94b8-3cc8405e90d0=Scope \
    14dad69e-099b-42c9-810b-d002981feec1=Scope \
    37f7f235-527c-4136-accd-4a02d197296e=Scope

echo ""
echo "✅ App registration complete!"
echo ""
echo "Add these to your .env file:"
echo "ENTRA_ENABLED=true"
echo "ENTRA_TENANT_ID=$TENANT_ID"
echo "ENTRA_CLIENT_ID=$APP_ID"
echo "ENTRA_CLIENT_SECRET=$SECRET"
echo ""
echo "⚠️  Don't forget to:"
echo "1. Grant admin consent in Azure Portal → App registrations → API permissions"
echo "2. Create app roles (Admin, Cost Manager, Agent Manager)"
echo "3. Assign users to roles in Enterprise applications"
```

---

## Testing Authentication

### Test 1: Verify Entra ID Configuration

```bash
# Test token acquisition
curl -X POST "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "scope=https://graph.microsoft.com/.default" \
  -d "grant_type=client_credentials"
```

### Test 2: Verify Admin Endpoint Protection

```bash
# Should return 401 Unauthorized when Entra ID is enabled
curl -X GET "https://your-backend.azurecontainerapps.io/api/admin/tenants"

# Should return 200 OK with valid token
curl -X GET "https://your-backend.azurecontainerapps.io/api/admin/tenants" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Test 3: Verify Role-Based Access

```bash
# User with mcp.cost.manager role should access costs
curl -X GET "https://your-backend.azurecontainerapps.io/api/costs" \
  -H "Authorization: Bearer COST_MANAGER_TOKEN"

# But should get 403 Forbidden for tenants
curl -X GET "https://your-backend.azurecontainerapps.io/api/tenants" \
  -H "Authorization: Bearer COST_MANAGER_TOKEN"
```

---

## Troubleshooting

### Issue: "AADSTS50011: The reply URL specified in the request does not match"

**Solution**: Add the exact redirect URI in App Registration → Authentication:
```
https://your-exact-frontend-url.azurecontainerapps.io/auth/callback
```

### Issue: "AADSTS65001: User or administrator has not consented"

**Solution**: Grant admin consent in Azure Portal → App registrations → API permissions → Grant admin consent

### Issue: "Role claim not found in token"

**Solution**: 
1. Verify app roles are defined in App registrations → App roles
2. Assign users to roles in Enterprise applications → Users and groups
3. Check token contains roles: https://jwt.ms

### Issue: Users can't see admin portal

**Solution**: Check user has been assigned the role:
```bash
# List role assignments for your app
az ad app show --id $APP_ID \
  --query "appRoles[].{DisplayName:displayName, Value:value, Id:id}" \
  --output table

# Verify user assignment in Enterprise applications
```

---

## Next Steps

1. ✅ Complete Entra ID app registration
2. ✅ Assign admin users to roles
3. ✅ Update environment variables
4. ✅ Test authentication flow
5. ✅ Enable Entra ID in production deployment
6. 🔄 Monitor authentication logs in Application Insights
7. 🔄 Set up secret rotation reminders

---

## Additional Resources

- [Microsoft Identity Platform Documentation](https://learn.microsoft.com/en-us/azure/active-directory/develop/)
- [Azure RBAC Best Practices](https://learn.microsoft.com/en-us/azure/role-based-access-control/best-practices)
- [Secure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/authentication)
- [Key Vault Security](https://learn.microsoft.com/en-us/azure/key-vault/general/security-features)
