/**
 * Cost Management Dashboard
 */
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DollarSign, TrendingUp, AlertCircle } from 'lucide-react';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Card, Spinner, StatsCard } from '../../components/ui';
import api from '../../api/services';

const COLORS = ['#0078D4', '#50E6FF', '#FFB900', '#00B294', '#E81123', '#8764B8'];

const CostDashboard: React.FC = () => {
  const [dateRange] = useState({ start: '2024-01-01', end: '2024-12-31' });

  const { data: costs, isLoading: costsLoading } = useQuery({
    queryKey: ['costs', dateRange],
    queryFn: () => api.costs.get(dateRange.start, dateRange.end).then((res) => res.data),
  });

  const { data: tenants, isLoading: tenantsLoading } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => api.tenants.list().then((res) => res.data),
  });

  if (costsLoading || tenantsLoading) return <Spinner />;

  const breakdownData = Object.entries(costs?.breakdown || {}).map(([name, value]) => ({
    name,
    value,
  }));

  const tenantCostData = tenants?.map((tenant) => ({
    name: tenant.name,
    cost: Math.random() * 1000, // Mock data - replace with actual
    budget: tenant.budget_limit,
  }));

  return (
    <div className="cost-dashboard">
      <div className="page-header">
        <h1>Cost Management</h1>
        <p className="text-secondary">Track and analyze platform costs</p>
      </div>

      {/* Stats Overview */}
      <div className="stats-grid mb-6">
        <StatsCard
          label="Total Monthly Cost"
          value={`$${costs?.total_cost.toFixed(2) || '0.00'}`}
          icon={<DollarSign size={24} />}
          variant="default"
        />
        <StatsCard
          label="Average Per Tenant"
          value={`$${((costs?.total_cost || 0) / (tenants?.length || 1)).toFixed(2)}`}
          icon={<TrendingUp size={24} />}
          variant="default"
        />
        <StatsCard
          label="Over Budget Tenants"
          value={tenantCostData?.filter((t) => t.cost > t.budget).length || 0}
          icon={<AlertCircle size={24} />}
          variant="error"
        />
      </div>

      {/* Cost Breakdown */}
      <div className="grid grid-2 gap-6 mb-6">
        <Card title="Cost by Service">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={breakdownData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: $${entry.value.toFixed(2)}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {breakdownData.map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Cost by Tenant">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={tenantCostData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
              <Legend />
              <Bar dataKey="cost" fill="#0078D4" name="Current Cost" />
              <Bar dataKey="budget" fill="#50E6FF" name="Budget Limit" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Tenant Budget Status */}
      <Card title="Tenant Budget Status">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Tenant</th>
                <th>Current Cost</th>
                <th>Budget Limit</th>
                <th>Usage %</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {tenantCostData?.map((tenant, index) => {
                const usagePercent = (tenant.cost / tenant.budget) * 100;
                const status =
                  usagePercent >= 100
                    ? 'over'
                    : usagePercent >= 90
                    ? 'warning'
                    : 'normal';
                return (
                  <tr key={index}>
                    <td>{tenant.name}</td>
                    <td>${tenant.cost.toFixed(2)}</td>
                    <td>${tenant.budget.toFixed(2)}</td>
                    <td>{usagePercent.toFixed(1)}%</td>
                    <td>
                      <span className={`badge badge-${status === 'over' ? 'error' : status === 'warning' ? 'warning' : 'success'}`}>
                        {status === 'over' ? 'Over Budget' : status === 'warning' ? 'Warning' : 'Normal'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default CostDashboard;
