/**
 * Admin Dashboard - Overview of system metrics and status
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Activity,
  Users,
  DollarSign,
  AlertTriangle,
  TrendingUp,
  Database,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { StatsCard, Card, Spinner, Badge } from '../../components/ui';
import api from '../../api/services';

const Dashboard: React.FC = () => {
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.health.check().then((res) => res.data),
    refetchInterval: 30000,
  });

  const { data: usage } = useQuery({
    queryKey: ['usage'],
    queryFn: () => api.usage.get().then((res) => res.data),
    retry: false,
    // Usage endpoint might not exist yet, so we handle gracefully
  });

  const { data: costs, isLoading: costsLoading } = useQuery({
    queryKey: ['costs'],
    queryFn: () => api.costs.get().then((res) => res.data),
  });

  const { data: tenants, isLoading: tenantsLoading } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => api.tenants.list().then((res) => res.data),
  });

  const { data: agentsResponse, isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => api.agents.list().then((res) => res.data),
  });

  // Extract agents array from response
  const agents = agentsResponse?.agents || [];

  if (healthLoading || costsLoading || tenantsLoading || agentsLoading) {
    return <Spinner />;
  }

  const activeTenants = tenants?.filter((t) => t.enabled).length || 0;
  const activeAgents = agents.filter((a) => a.status === 'active').length;

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p className="text-secondary">Overview of your MCP server</p>
      </div>

      {/* System Health */}
      <Card title="System Health" className="mb-6">
        <div className="health-grid">
          <div className="health-item">
            <span className="health-label">Overall Status</span>
            <Badge variant={health?.status === 'healthy' ? 'success' : 'error'}>
              {health?.status || 'Unknown'}
            </Badge>
          </div>
          <div className="health-item">
            <span className="health-label">Redis</span>
            {health?.components.redis ? (
              <CheckCircle size={20} className="text-success" />
            ) : (
              <XCircle size={20} className="text-error" />
            )}
          </div>
          <div className="health-item">
            <span className="health-label">Key Vault</span>
            {health?.components.key_vault ? (
              <CheckCircle size={20} className="text-success" />
            ) : (
              <XCircle size={20} className="text-error" />
            )}
          </div>
          <div className="health-item">
            <span className="health-label">Storage</span>
            {health?.components.storage ? (
              <CheckCircle size={20} className="text-success" />
            ) : (
              <XCircle size={20} className="text-error" />
            )}
          </div>
          <div className="health-item">
            <span className="health-label">FoundryIQ</span>
            {health?.components.foundry ? (
              <CheckCircle size={20} className="text-success" />
            ) : (
              <XCircle size={20} className="text-error" />
            )}
          </div>
        </div>
      </Card>

      {/* Key Metrics */}
      <div className="stats-grid mb-6">
        <Link to="/admin/tenants" style={{ textDecoration: 'none' }}>
          <StatsCard
            label="Active Tenants"
            value={activeTenants}
            icon={<Users size={24} />}
            variant="default"
          />
        </Link>
        <Link to="/admin/agents" style={{ textDecoration: 'none' }}>
          <StatsCard
            label="Active Agents"
            value={activeAgents}
            icon={<Database size={24} />}
            variant="default"
          />
        </Link>
        <StatsCard
          label="Total Requests"
          value={usage?.requests_total.toLocaleString() || '0'}
          icon={<Activity size={24} />}
          variant="success"
        />
        <Link to="/admin/costs" style={{ textDecoration: 'none' }}>
          <StatsCard
            label="Monthly Cost"
            value={`$${costs?.total_cost.toFixed(2) || '0.00'}`}
            icon={<DollarSign size={24} />}
            variant="warning"
          />
        </Link>
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-2 gap-6">
        <Card title="Usage Overview">
          <div className="metric-list">
            <div className="metric-item">
              <span className="metric-label">Average Response Time</span>
              <span className="metric-value">{usage?.avg_response_time.toFixed(0)}ms</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Error Rate</span>
              <span className="metric-value">{((usage?.error_rate ?? 0) * 100).toFixed(2)}%</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Total Tenants</span>
              <span className="metric-value">{tenants?.length || 0}</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Total Agents</span>
              <span className="metric-value">{agents?.length || 0}</span>
            </div>
          </div>
        </Card>

        <Card title="Quick Actions">
          <div className="action-list">
            <Link to="/admin/tenants/new" className="action-item">
              <Users size={20} />
              <span>Create New Tenant</span>
            </Link>
            <Link to="/admin/agents" className="action-item">
              <Database size={20} />
              <span>Discover Agents</span>
            </Link>
            <Link to="/admin/branding" className="action-item">
              <TrendingUp size={20} />
              <span>Customize Branding</span>
            </Link>
            <Link to="/admin/settings" className="action-item">
              <AlertTriangle size={20} />
              <span>Configure Settings</span>
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
