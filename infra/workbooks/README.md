# Application Insights Workbooks

This directory contains pre-built workbook templates for monitoring the Enterprise MCP Server.

## Available Workbooks

### 1. Tenant Usage Dashboard (`tenant-usage.json`)
Monitor request patterns and performance by tenant:
- **Requests by Tenant** - Bar chart of request counts
- **Average Response Time** - Latency metrics per tenant
- **Error Rate** - Success/failure rates by tenant

**Use Cases**:
- Identify high-traffic tenants
- Detect performance issues
- Monitor tenant-specific errors

### 2. Cost Analysis Dashboard (`cost-analysis.json`)
Track Azure costs and budget alerts:
- **Cost by Tenant** - Pie chart of spend distribution
- **Cost by Service** - Azure service breakdown
- **Budget Alerts** - Recent budget threshold warnings

**Use Cases**:
- Optimize resource allocation
- Track per-tenant costs
- Monitor budget compliance

## Importing Workbooks

### Option 1: Azure Portal (Easiest)

1. Go to **Application Insights** in Azure Portal
2. Click **Workbooks** in the left menu
3. Click **+ New**
4. Click **Advanced Editor** (</> icon in toolbar)
5. Delete default content
6. Paste workbook JSON from this directory
7. Click **Apply**
8. Click **Done Editing**
9. Click **Save** and give it a name

### Option 2: Azure CLI

```bash
# Set variables
RESOURCE_GROUP="mcp-server-dev"
APP_INSIGHTS_NAME="mcp-server-dev-ai"

# Get Application Insights resource ID
APP_INSIGHTS_ID=$(az monitor app-insights component show \
  --app $APP_INSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

# Import tenant usage workbook
az monitor app-insights workbook create \
  --resource-group $RESOURCE_GROUP \
  --name "tenant-usage-$(date +%s)" \
  --display-name "Tenant Usage Dashboard" \
  --source-id $APP_INSIGHTS_ID \
  --serialized-data @tenant-usage.json \
  --category "MCP"

# Import cost analysis workbook
az monitor app-insights workbook create \
  --resource-group $RESOURCE_GROUP \
  --name "cost-analysis-$(date +%s)" \
  --display-name "Cost Analysis Dashboard" \
  --source-id $APP_INSIGHTS_ID \
  --serialized-data @cost-analysis.json \
  --category "MCP"

echo "✓ Workbooks imported successfully"
```

### Option 3: Automated Import Script

Create `import-workbooks.sh`:

```bash
#!/bin/bash
set -e

RESOURCE_GROUP=${1:-"mcp-server-dev"}
ENVIRONMENT=${2:-"dev"}
APP_INSIGHTS_NAME="mcp-server-${ENVIRONMENT}-ai"

echo "Importing workbooks to $APP_INSIGHTS_NAME..."

# Get resource ID
APP_INSIGHTS_ID=$(az monitor app-insights component show \
  --app $APP_INSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

# Import all workbooks
for workbook in *.json; do
  NAME=$(basename "$workbook" .json)
  echo "Importing $NAME..."
  
  az monitor app-insights workbook create \
    --resource-group $RESOURCE_GROUP \
    --name "${NAME}-$(date +%s)" \
    --display-name "${NAME//-/ }" \
    --source-id $APP_INSIGHTS_ID \
    --serialized-data @"$workbook" \
    --category "MCP" \
    --output none
done

echo "✓ All workbooks imported"
```

Run with:
```bash
cd infra/workbooks
chmod +x import-workbooks.sh
./import-workbooks.sh mcp-server-dev dev
```

## Customizing Workbooks

### Update Resource IDs
After importing, workbooks may need to be updated with your actual resource IDs:

1. Open workbook in Azure Portal
2. Click **Edit**
3. Find `fallbackResourceIds` section
4. Replace placeholders with actual IDs:
   ```json
   "fallbackResourceIds": [
     "/subscriptions/YOUR-SUB-ID/resourceGroups/YOUR-RG/providers/microsoft.insights/components/YOUR-AI-NAME"
   ]
   ```
5. Click **Done Editing** and **Save**

### Add Custom Queries
To add your own charts:

1. Open workbook and click **Edit**
2. Click **+ Add** → **Add query**
3. Write KQL query, for example:
   ```kusto
   requests
   | where timestamp > ago(24h)
   | extend tenant_id = tostring(customDimensions.tenant_id)
   | summarize count() by bin(timestamp, 1h), tenant_id
   | render timechart
   ```
4. Choose visualization type
5. Save the workbook

## Example Queries

### Top 10 Slowest Endpoints
```kusto
requests
| where timestamp > ago(1d)
| summarize AvgDuration = avg(duration), Count = count() by operation_Name
| order by AvgDuration desc
| take 10
```

### Rate Limit Violations
```kusto
customEvents
| where name == "rate_limit_exceeded"
| extend tenant_id = tostring(customDimensions.tenant_id)
| summarize Violations = count() by tenant_id, bin(timestamp, 1h)
| order by timestamp desc
```

### Budget Threshold Breaches
```kusto
customEvents
| where name == "budget_alert"
| extend tenant_id = tostring(customDimensions.tenant_id)
| extend usage_percent = todouble(customDimensions.usage_percent)
| where usage_percent > 80
| project timestamp, tenant_id, usage_percent
```

### Agent Performance
```kusto
dependencies
| where type == "HTTP"
| where target contains "foundry"
| summarize 
    AvgDuration = avg(duration),
    P95Duration = percentile(duration, 95),
    CallCount = count()
    by operation_Name
| order by AvgDuration desc
```

## Sharing Workbooks

### Export for Version Control
1. Open workbook in Azure Portal
2. Click **Advanced Editor** (</> icon)
3. Copy JSON content
4. Save to this directory
5. Commit to Git

### Share with Team
1. Open workbook in Azure Portal
2. Click **Share** in toolbar
3. Choose sharing options:
   - **Link** - Share URL (requires Azure access)
   - **Download** - Save as .workbook file
   - **Pin to Dashboard** - Add to Azure Dashboard

## Best Practices

1. **Use Parameters**: Add time range and tenant filters for flexibility
2. **Keep Queries Simple**: Complex queries can slow down workbooks
3. **Use Caching**: Enable caching for expensive queries
4. **Version Control**: Commit workbook JSON to Git after changes
5. **Document Metrics**: Add text blocks explaining what each chart shows
6. **Test Queries**: Verify queries in Log Analytics before adding to workbooks

## Troubleshooting

### Issue: "No data available"
- Verify Application Insights is receiving telemetry
- Check time range parameter
- Ensure custom dimensions are being logged

### Issue: "Query failed"
- Test query in Log Analytics workspace
- Check for typos in column names
- Verify customDimensions structure

### Issue: "Workbook import failed"
- Ensure JSON is valid (use JSON validator)
- Check Azure CLI version (2.50+)
- Verify you have permissions on Application Insights

## Additional Resources

- [Workbook Documentation](https://docs.microsoft.com/en-us/azure/azure-monitor/visualize/workbooks-overview)
- [KQL Reference](https://docs.microsoft.com/en-us/azure/data-explorer/kusto/query/)
- [Application Insights Query](https://docs.microsoft.com/en-us/azure/azure-monitor/logs/log-query-overview)
