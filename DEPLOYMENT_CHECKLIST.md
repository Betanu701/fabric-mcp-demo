# Deployment Checklist

Use this checklist to track your deployment progress.

## 🔧 Pre-Deployment

### Local Environment Setup
- [ ] Clone repository
- [ ] Install Python 3.12+
- [ ] Install Node.js 18+
- [ ] Install Docker Desktop
- [ ] Install Azure CLI 2.50+
- [ ] Run `./scripts/init_local.sh`
- [ ] Test locally with `docker-compose up`

### Azure Prerequisites
- [ ] Azure subscription active
- [ ] Owner/Contributor access to subscription
- [ ] Azure CLI logged in (`az login`)
- [ ] Correct subscription selected (`az account set`)
- [ ] Resource group name decided
- [ ] Azure region selected (e.g., eastus)
- [ ] Container registry name chosen (globally unique)

## 🚀 Deployment

### Infrastructure Provisioning
- [ ] Review `infra/parameters.dev.json` or `infra/parameters.prod.json`
- [ ] Update `containerRegistryName` parameter
- [ ] Run `./scripts/provision_azure.sh -e dev -l eastus`
- [ ] Wait for deployment to complete (~15 minutes)
- [ ] Note backend URL from output
- [ ] Note frontend URL from output
- [ ] Note Key Vault name from output

### Verification
- [ ] Visit backend health endpoint: `{backend-url}/health`
- [ ] Visit API docs: `{backend-url}/docs`
- [ ] Visit frontend URL
- [ ] Test agents endpoint: `curl -H "X-Tenant-ID: default" {backend-url}/api/agents`
- [ ] Check Application Insights for telemetry

## ⚙️ Configuration

### Key Vault Setup
- [ ] Access Key Vault in Azure Portal
- [ ] Verify `tenant-default-config` secret exists
- [ ] Update `foundry_endpoint` with real URL
- [ ] Add additional tenant configurations
- [ ] Verify global branding secret exists

### Tenant Configuration
- [ ] Create tenant configuration for each customer
- [ ] Set rate limits (RPM, RPD, monthly)
- [ ] Configure budget limits and enforcement
- [ ] Set notification channels (email, SMS)
- [ ] Configure FoundryIQ endpoints

Example tenant config:
```bash
az keyvault secret set \
  --vault-name {keyvault-name} \
  --name "tenant-customer1-config" \
  --value '{
    "id": "customer1",
    "name": "Customer One",
    "enabled": true,
    "foundry_endpoint": "https://foundry.azure.com/customer1",
    "rate_limit_rpm": 100,
    "rate_limit_rpd": 10000,
    "quota_monthly_requests": 100000,
    "budget_limit": 1000.00,
    "budget_threshold": 90,
    "budget_enforcement": "warn"
  }'
```

### Branding Setup
- [ ] Set global branding colors and logo
- [ ] Upload global logo to Blob Storage
- [ ] Set per-tenant branding overrides
- [ ] Upload tenant logos
- [ ] Test branding via API: `curl -H "X-Tenant-ID: customer1" {backend-url}/api/branding`

### Cost Management
- [ ] Configure budget alerts in Azure Cost Management
- [ ] Set up Action Groups for notifications
- [ ] Test budget enforcement with low limits
- [ ] Verify cost tracking: `curl -H "X-Tenant-ID: default" {backend-url}/api/costs`

### Communication Services (Optional)
- [ ] Enable Communication Services in Bicep (`enableCommunicationServices: true`)
- [ ] Configure email domain
- [ ] Configure SMS number
- [ ] Test notification sending
- [ ] Update tenant configs with notification preferences

## 🔐 Security Hardening

### Entra ID Authentication (Optional)
- [ ] Create App Registration in Entra ID
- [ ] Configure redirect URIs
- [ ] Add API permissions
- [ ] Update Key Vault with client ID/secret
- [ ] Enable in deployment: `enableEntraAuth: true`
- [ ] Test authentication flow

### Network Security
- [ ] Review Container Apps ingress settings
- [ ] Configure IP restrictions if needed
- [ ] Set up private endpoints (optional)
- [ ] Enable VNet integration (optional)
- [ ] Configure NSG rules (if using VNet)

### Secrets Management
- [ ] Rotate Redis access keys
- [ ] Rotate Storage account keys
- [ ] Update Key Vault access policies
- [ ] Enable Key Vault logging
- [ ] Set up secret expiration alerts

## 📊 Monitoring

### Application Insights
- [ ] Verify telemetry flowing to App Insights
- [ ] Create custom dashboard
- [ ] Set up availability tests
- [ ] Configure alert rules:
  - [ ] HTTP 5xx errors
  - [ ] Response time > 5s
  - [ ] Failed requests > 10%
  - [ ] Budget threshold exceeded
- [ ] Create workbooks (optional):
  - [ ] Tenant usage
  - [ ] Rate limits
  - [ ] Agent performance
  - [ ] Cost analysis

### Cost Alerts
- [ ] Set up budget in Azure Cost Management
- [ ] Configure action group for cost alerts
- [ ] Test alert notifications
- [ ] Review cost breakdown weekly

### Health Monitoring
- [ ] Create uptime monitor (e.g., Pingdom, UptimeRobot)
- [ ] Set up health check alerts
- [ ] Configure PagerDuty/OpsGenie (optional)
- [ ] Document on-call procedures

## 🔄 CI/CD Pipeline

### GitHub Actions Setup
- [ ] Create Azure Service Principal: `az ad sp create-for-rbac`
- [ ] Add GitHub secrets:
  - [ ] `AZURE_CREDENTIALS`
  - [ ] `AZURE_SUBSCRIPTION_ID`
  - [ ] `ACR_LOGIN_SERVER`
  - [ ] `ACR_USERNAME`
  - [ ] `ACR_PASSWORD`
- [ ] Test workflow on `develop` branch
- [ ] Verify deployment to dev environment
- [ ] Test workflow on `main` branch
- [ ] Verify deployment to prod environment

### Deployment Process
- [ ] Document branching strategy
- [ ] Set up branch protection rules
- [ ] Require PR reviews
- [ ] Run tests on all PRs
- [ ] Auto-deploy on merge

## 🧪 Testing

### Functional Testing
- [ ] Test health endpoint
- [ ] Test agent listing
- [ ] Test chat functionality with mock responses
- [ ] Test rate limiting (exceed RPM limit)
- [ ] Test budget enforcement (set low limit)
- [ ] Test cost tracking
- [ ] Test notification sending
- [ ] Test branding API
- [ ] Test logo upload
- [ ] Test tenant CRUD operations

### Load Testing (Optional)
- [ ] Install load testing tool (k6, Apache Bench)
- [ ] Create test scenarios
- [ ] Run load test against dev environment
- [ ] Verify auto-scaling works
- [ ] Monitor resource usage
- [ ] Document performance baselines

### End-to-End Testing
- [ ] Create test tenant configuration
- [ ] Send chat messages via API
- [ ] Verify FoundryIQ integration (when connected)
- [ ] Check cost attribution
- [ ] Verify rate limiting enforcement
- [ ] Test branding inheritance
- [ ] Check notification delivery

## 📚 Documentation

### Internal Documentation
- [ ] Document tenant onboarding process
- [ ] Create runbooks for common operations
- [ ] Document disaster recovery procedures
- [ ] Create troubleshooting guide
- [ ] Document API usage for customers

### User Documentation (Optional)
- [ ] Create user guide for chat interface
- [ ] Document API endpoints for integration
- [ ] Create FAQ
- [ ] Document branding customization
- [ ] Create video tutorials

## 🚨 Disaster Recovery

### Backup Configuration
- [ ] Enable Redis persistence (Premium tier)
- [ ] Configure Key Vault backups
- [ ] Enable Blob Storage versioning
- [ ] Set up geo-replication (prod only)
- [ ] Document backup locations
- [ ] Test backup restoration

### DR Testing
- [ ] Schedule quarterly DR drills
- [ ] Document DR procedures
- [ ] Test failover to secondary region (if multi-region)
- [ ] Verify RTO/RPO targets
- [ ] Update contact information

### Backup Schedule
- [ ] Daily: Redis RDB export
- [ ] Daily: Key Vault secrets backup
- [ ] Continuous: Blob Storage versioning
- [ ] Weekly: Full configuration export
- [ ] Monthly: Test restoration

## ✅ Go-Live

### Pre-Launch Checks
- [ ] All tests passing
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Documentation complete
- [ ] Backup procedures tested
- [ ] DR plan documented
- [ ] On-call rotation established
- [ ] Customer notifications sent

### Launch Day
- [ ] Deploy to production
- [ ] Run smoke tests
- [ ] Monitor logs for errors
- [ ] Check Application Insights
- [ ] Verify all endpoints responding
- [ ] Test with real tenants
- [ ] Monitor cost accumulation
- [ ] Document any issues

### Post-Launch
- [ ] Monitor for 48 hours
- [ ] Review Application Insights
- [ ] Check error rates
- [ ] Verify auto-scaling
- [ ] Review costs
- [ ] Collect user feedback
- [ ] Plan iterative improvements

## 🔄 Ongoing Operations

### Daily Tasks
- [ ] Check Application Insights for errors
- [ ] Review cost dashboard
- [ ] Monitor health endpoints
- [ ] Check notification queue

### Weekly Tasks
- [ ] Review Application Insights metrics
- [ ] Analyze cost trends
- [ ] Review security alerts
- [ ] Check for Azure service updates
- [ ] Review rate limit violations

### Monthly Tasks
- [ ] Review and optimize costs
- [ ] Update dependencies
- [ ] Rotate secrets
- [ ] Test disaster recovery
- [ ] Review and update documentation
- [ ] Plan feature enhancements

### Quarterly Tasks
- [ ] Full DR drill
- [ ] Security audit
- [ ] Performance review
- [ ] Cost optimization review
- [ ] Update runbooks
- [ ] Review SLAs

## 📈 Optimization

### Performance
- [ ] Analyze slow API endpoints
- [ ] Optimize database queries
- [ ] Implement caching strategies
- [ ] Review container resource allocation
- [ ] Optimize Docker images

### Cost
- [ ] Review Redis tier (Standard vs Premium)
- [ ] Optimize container replica counts
- [ ] Review storage lifecycle policies
- [ ] Consider reserved instances
- [ ] Analyze unused resources

### Security
- [ ] Review RBAC assignments
- [ ] Audit Key Vault access logs
- [ ] Update security policies
- [ ] Patch dependencies
- [ ] Review network security rules

## 🎯 Next Steps

After completing this checklist:
1. **Integrate Real FoundryIQ**: Replace mock responses with actual API calls
2. **Build Admin UI**: Complete tenant management components
3. **Add Setup Wizard**: First-run configuration experience
4. **Implement Multi-Region**: Set up disaster recovery failover
5. **Custom Workbooks**: Create Application Insights dashboards
6. **Advanced Features**: Add more capabilities based on user feedback

---

**Note**: This checklist is comprehensive. Not all items are required for a minimal deployment. Focus on sections marked as required for your initial launch, then iterate on optional features.
