# Disaster Recovery Guide - Enterprise MCP Server

## Overview

This guide outlines disaster recovery (DR) procedures for the Enterprise MCP Server, including multi-region failover, backup strategies, and recovery procedures.

## Recovery Objectives

### RTO (Recovery Time Objective)
- **Development**: 4 hours
- **Staging**: 2 hours
- **Production**: 1 hour

### RPO (Recovery Point Objective)
- **Development**: 24 hours
- **Staging**: 12 hours
- **Production**: 1 hour

## Architecture

### Single-Region Deployment (Default)
```
Primary Region (e.g., East US)
├── Container Apps Environment
├── Redis Cache (Standard/Premium with persistence)
├── Key Vault (soft-delete + purge protection)
├── Storage Account (LRS/ZRS with versioning)
├── Application Insights (90-day retention)
└── Managed Identity
```

### Multi-Region Deployment (Optional)
```
Primary Region (East US)          Secondary Region (West US)
├── Container Apps              ├── Container Apps (standby)
├── Redis Cache (Primary)       ├── Redis Cache (geo-replica)
├── Key Vault (Primary)         ├── Key Vault (replica)
├── Storage (Primary)           ├── Storage (geo-replica)
├── App Insights (Primary)      ├── App Insights (separate)
└── Traffic Manager (Active/Passive)
```

## Backup Strategies

### 1. Key Vault Backups

#### Automatic Soft-Delete
- **Enabled by default**: 90-day soft-delete retention
- **Purge protection**: Enabled in production
- **Access**: Azure RBAC with audit logging

#### Manual Backup
```bash
# Backup all secrets
KEY_VAULT_NAME="mcp-server-prod-kv"
BACKUP_DIR="./backups/keyvault/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# List and backup each secret
az keyvault secret list \
  --vault-name $KEY_VAULT_NAME \
  --query "[].name" -o tsv | \
while read secret_name; do
  echo "Backing up: $secret_name"
  az keyvault secret backup \
    --vault-name $KEY_VAULT_NAME \
    --name $secret_name \
    --file "${BACKUP_DIR}/${secret_name}.backup"
done

echo "✓ Backup complete: $BACKUP_DIR"
```

#### Restore Secrets
```bash
# Restore from backup
BACKUP_FILE="./backups/keyvault/20251204/tenant-default-config.backup"
NEW_VAULT_NAME="mcp-server-dr-kv"

az keyvault secret restore \
  --vault-name $NEW_VAULT_NAME \
  --file $BACKUP_FILE
```

### 2. Redis Cache Backups

#### Redis Premium (RDB Persistence)
```bash
# Configure persistence (Premium tier only)
az redis patch-schedule set \
  --name mcp-server-prod-redis \
  --resource-group mcp-server-prod \
  --schedule-entries '[{"dayOfWeek":"Sunday","startHourUtc":2,"maintenanceWindow":"PT2H"}]'

# Export RDB file
az redis export \
  --name mcp-server-prod-redis \
  --resource-group mcp-server-prod \
  --prefix redis-backup-$(date +%Y%m%d) \
  --container https://mcpstorage.blob.core.windows.net/redis-backups \
  --file-format RDB
```

#### Redis Standard/Basic (Data Export)
```bash
# Manual snapshot via Redis CLI
redis-cli -h mcp-redis.redis.cache.windows.net \
  -p 6380 --tls -a {access-key} \
  --rdb /tmp/redis-snapshot-$(date +%Y%m%d).rdb
```

### 3. Blob Storage Backups

#### Enable Versioning and Soft Delete
```bash
# Enable blob versioning
az storage account blob-service-properties update \
  --account-name mcpstorageprod \
  --enable-versioning true

# Enable soft delete (90 days)
az storage account blob-service-properties update \
  --account-name mcpstorageprod \
  --enable-delete-retention true \
  --delete-retention-days 90
```

#### Geo-Replication (Production)
```bash
# Upgrade to geo-redundant storage
az storage account update \
  --name mcpstorageprod \
  --resource-group mcp-server-prod \
  --sku Standard_GZRS
```

#### Manual Backup
```bash
# Copy branding container to backup location
az storage blob copy start-batch \
  --source-account-name mcpstorageprod \
  --source-container branding \
  --destination-account-name mcpstoragebackup \
  --destination-container branding-backup-$(date +%Y%m%d)
```

### 4. Application Insights Data

#### Export Configuration
```bash
# Enable continuous export to Storage
az monitor app-insights component continues-export create \
  --app mcp-server-prod-ai \
  --resource-group mcp-server-prod \
  --record-types Requests,Exceptions,Metrics,CustomEvents \
  --dest-account mcpstorageprod \
  --dest-container app-insights-export
```

#### Query Historical Data
```bash
# Export specific time range
az monitor app-insights query \
  --app mcp-server-prod-ai \
  --analytics-query "requests | where timestamp > ago(30d)" \
  --output table > backup-requests-$(date +%Y%m%d).csv
```

## Failover Procedures

### Scenario 1: Container App Failure

#### Symptoms
- Health endpoint returns 503
- Application Insights shows high error rate
- Users cannot access the application

#### Recovery Steps
```bash
# 1. Check container app status
az containerapp show \
  --name mcp-server-prod-backend \
  --resource-group mcp-server-prod \
  --query "properties.provisioningState"

# 2. View recent logs
az containerapp logs show \
  --name mcp-server-prod-backend \
  --resource-group mcp-server-prod \
  --tail 100

# 3. Restart container app
az containerapp revision restart \
  --name mcp-server-prod-backend \
  --resource-group mcp-server-prod

# 4. If restart fails, rollback to previous revision
PREVIOUS_REVISION=$(az containerapp revision list \
  --name mcp-server-prod-backend \
  --resource-group mcp-server-prod \
  --query "[1].name" -o tsv)

az containerapp revision activate \
  --name mcp-server-prod-backend \
  --resource-group mcp-server-prod \
  --revision $PREVIOUS_REVISION

# 5. Verify recovery
curl -s https://backend-url/health | jq
```

**RTO**: 15 minutes

### Scenario 2: Redis Cache Failure

#### Symptoms
- Rate limiting not working
- High backend latency
- Redis connection errors in logs

#### Recovery Steps
```bash
# 1. Check Redis status
az redis show \
  --name mcp-server-prod-redis \
  --resource-group mcp-server-prod \
  --query "provisioningState,redisVersion"

# 2. Restart Redis (Premium tier)
az redis regenerate-key \
  --name mcp-server-prod-redis \
  --resource-group mcp-server-prod \
  --key-type Primary

# 3. If Redis is down, deploy new instance
az redis create \
  --name mcp-server-prod-redis-dr \
  --resource-group mcp-server-prod \
  --location eastus \
  --sku Premium \
  --vm-size P1

# 4. Import backup (Premium only)
az redis import \
  --name mcp-server-prod-redis-dr \
  --resource-group mcp-server-prod \
  --files https://mcpstorage.blob.core.windows.net/redis-backups/backup.rdb

# 5. Update connection string in Key Vault
NEW_REDIS_KEY=$(az redis list-keys \
  --name mcp-server-prod-redis-dr \
  --resource-group mcp-server-prod \
  --query primaryKey -o tsv)

az keyvault secret set \
  --vault-name mcp-server-prod-kv \
  --name redis-connection-string \
  --value "mcp-server-prod-redis-dr.redis.cache.windows.net:6380,password=${NEW_REDIS_KEY},ssl=True"

# 6. Restart container apps to pick up new connection
az containerapp revision restart \
  --name mcp-server-prod-backend \
  --resource-group mcp-server-prod
```

**RTO**: 30 minutes (Premium), 60 minutes (Standard)

### Scenario 3: Key Vault Failure

#### Symptoms
- Cannot read tenant configurations
- Authentication failures
- "Key Vault access denied" errors

#### Recovery Steps
```bash
# 1. Check Key Vault status
az keyvault show \
  --name mcp-server-prod-kv \
  --query "properties.provisioningState"

# 2. Check network rules
az keyvault network-rule list \
  --name mcp-server-prod-kv

# 3. If soft-deleted, recover
az keyvault recover \
  --name mcp-server-prod-kv

# 4. If permanently deleted, restore from backup
# Create new Key Vault
az keyvault create \
  --name mcp-server-prod-kv-dr \
  --resource-group mcp-server-prod \
  --location eastus \
  --enable-soft-delete true \
  --enable-purge-protection true

# Restore all secrets
for backup_file in ./backups/keyvault/latest/*.backup; do
  az keyvault secret restore \
    --vault-name mcp-server-prod-kv-dr \
    --file "$backup_file"
done

# 5. Update RBAC permissions
MANAGED_IDENTITY_ID=$(az containerapp show \
  --name mcp-server-prod-backend \
  --resource-group mcp-server-prod \
  --query "identity.principalId" -o tsv)

az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee $MANAGED_IDENTITY_ID \
  --scope $(az keyvault show \
    --name mcp-server-prod-kv-dr \
    --query id -o tsv)

# 6. Update container app environment variable
az containerapp update \
  --name mcp-server-prod-backend \
  --resource-group mcp-server-prod \
  --set-env-vars KEY_VAULT_URL="https://mcp-server-prod-kv-dr.vault.azure.net/"
```

**RTO**: 45 minutes

### Scenario 4: Storage Account Failure

#### Symptoms
- Cannot upload logos
- Branding assets not loading
- CDN errors

#### Recovery Steps
```bash
# 1. Check storage account status
az storage account show \
  --name mcpstorageprod \
  --query "provisioningState,statusOfPrimary"

# 2. If using geo-replication, failover to secondary
az storage account failover \
  --name mcpstorageprod \
  --yes

# 3. If complete failure, restore from backup
# Create new storage account
az storage account create \
  --name mcpstoragedr \
  --resource-group mcp-server-prod \
  --location eastus \
  --sku Standard_GZRS

# Create containers
az storage container create \
  --account-name mcpstoragedr \
  --name branding \
  --public-access blob

# Restore from latest backup
az storage blob copy start-batch \
  --source-account-name mcpstoragebackup \
  --source-container branding-backup-latest \
  --destination-account-name mcpstoragedr \
  --destination-container branding

# 4. Update CDN origin
az cdn endpoint update \
  --name mcp-cdn-endpoint \
  --profile-name mcp-cdn \
  --resource-group mcp-server-prod \
  --origin-host-header mcpstoragedr.blob.core.windows.net

# 5. Update container app environment
az containerapp update \
  --name mcp-server-prod-backend \
  --resource-group mcp-server-prod \
  --set-env-vars STORAGE_ACCOUNT_URL="https://mcpstoragedr.blob.core.windows.net/"
```

**RTO**: 30 minutes

### Scenario 5: Region-Wide Outage

#### Symptoms
- All services in primary region unavailable
- Azure status page shows region outage
- Cannot access Azure Portal for primary region

#### Recovery Steps (Multi-Region Setup Required)
```bash
# 1. Verify secondary region health
az containerapp show \
  --name mcp-server-prod-backend-westus \
  --resource-group mcp-server-prod-westus \
  --query "properties.provisioningState"

# 2. Update Traffic Manager to route to secondary
az network traffic-manager endpoint update \
  --name primary-endpoint \
  --profile-name mcp-traffic-manager \
  --resource-group mcp-server-prod \
  --type azureEndpoints \
  --endpoint-status Disabled

az network traffic-manager endpoint update \
  --name secondary-endpoint \
  --profile-name mcp-traffic-manager \
  --resource-group mcp-server-prod \
  --type azureEndpoints \
  --endpoint-status Enabled

# 3. Verify DNS propagation
nslookup mcp-server.trafficmanager.net

# 4. Monitor secondary region
az monitor metrics list \
  --resource /subscriptions/{id}/resourceGroups/mcp-server-prod-westus/providers/Microsoft.App/containerApps/mcp-server-prod-backend-westus \
  --metric Requests \
  --interval PT1M

# 5. When primary recovers, failback
az network traffic-manager endpoint update \
  --name primary-endpoint \
  --profile-name mcp-traffic-manager \
  --resource-group mcp-server-prod \
  --type azureEndpoints \
  --endpoint-status Enabled
```

**RTO**: 1 hour (requires multi-region setup)

## Testing DR Procedures

### Quarterly DR Drills

#### Test 1: Container App Failover (Q1)
```bash
# Simulate failure by stopping container
az containerapp revision deactivate \
  --name mcp-server-prod-backend \
  --resource-group mcp-server-prod \
  --revision $(az containerapp revision list \
    --name mcp-server-prod-backend \
    --resource-group mcp-server-prod \
    --query "[0].name" -o tsv)

# Time recovery process
# Target: < 15 minutes

# Verify services restored
curl -s https://backend-url/health
```

#### Test 2: Key Vault Restore (Q2)
```bash
# Backup current state
./scripts/backup_keyvault.sh

# Delete a non-critical secret
az keyvault secret delete \
  --vault-name mcp-server-prod-kv \
  --name test-secret

# Restore from backup
# Target: < 30 minutes
```

#### Test 3: Redis Failover (Q3)
```bash
# Trigger Redis failover (Premium tier)
az redis force-reboot \
  --name mcp-server-prod-redis \
  --resource-group mcp-server-prod \
  --reboot-type AllNodes

# Monitor recovery
# Target: < 10 minutes
```

#### Test 4: Full Region Failover (Q4)
```bash
# Requires multi-region setup
# Disable primary region endpoints
# Verify secondary takes over
# Target: < 60 minutes
```

## Monitoring and Alerts

### Critical Alerts
```bash
# Set up alert rules
az monitor metrics alert create \
  --name "Container App Down" \
  --resource-group mcp-server-prod \
  --scopes /subscriptions/{id}/resourceGroups/mcp-server-prod/providers/Microsoft.App/containerApps/mcp-server-prod-backend \
  --condition "avg Requests < 1" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action email=ops@company.com sms=+1234567890

az monitor metrics alert create \
  --name "Redis Connection Failures" \
  --resource-group mcp-server-prod \
  --scopes /subscriptions/{id}/resourceGroups/mcp-server-prod/providers/Microsoft.Cache/Redis/mcp-server-prod-redis \
  --condition "avg connectedclients < 1" \
  --window-size 5m

az monitor metrics alert create \
  --name "Storage Account Unavailable" \
  --resource-group mcp-server-prod \
  --scopes /subscriptions/{id}/resourceGroups/mcp-server-prod/providers/Microsoft.Storage/storageAccounts/mcpstorageprod \
  --condition "avg Availability < 99.9" \
  --window-size 15m
```

## Contact Information

### On-Call Rotation
- **Primary**: ops-team@company.com
- **Secondary**: engineering@company.com
- **Escalation**: cto@company.com

### Azure Support
- **Subscription**: Contact your Azure TAM
- **Emergency**: 1-800-Microsoft
- **Portal**: https://aka.ms/azuresupport

## Appendix

### Backup Schedule
| Resource | Frequency | Retention | Automation |
|----------|-----------|-----------|------------|
| Key Vault Secrets | Daily | 90 days | Azure native |
| Redis RDB | Daily | 30 days | Scheduled task |
| Blob Storage | Continuous | 90 days | Versioning |
| App Insights | Real-time | 90 days | Continuous export |
| Container Images | Per build | 180 days | ACR retention |

### Recovery Checklists
- ✅ Verify health endpoints responding
- ✅ Check Application Insights for errors
- ✅ Test tenant authentication
- ✅ Verify rate limiting functional
- ✅ Test chat functionality end-to-end
- ✅ Confirm branding assets loading
- ✅ Validate cost tracking operational
- ✅ Check notification delivery
- ✅ Review audit logs
- ✅ Update incident documentation
