/**
 * Tenant Management - List all tenants
 */
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Plus, Edit, Trash2, Power, PowerOff, Search } from 'lucide-react';
import { Card, Spinner, EmptyState, Badge, Modal } from '../../components/ui';
import api from '../../api/services';
import type { Tenant } from '../../types';
import { toast } from 'sonner';

const TenantList: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteModal, setDeleteModal] = useState<{ open: boolean; tenant?: Tenant }>({
    open: false,
  });

  const { data: tenants, isLoading } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => api.tenants.list().then((res) => res.data),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      enabled ? api.tenants.disable(id) : api.tenants.enable(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      toast.success('Tenant status updated');
    },
    onError: () => {
      toast.error('Failed to update tenant status');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.tenants.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      setDeleteModal({ open: false });
      toast.success('Tenant deleted');
    },
    onError: () => {
      toast.error('Failed to delete tenant');
    },
  });

  const filteredTenants = tenants?.filter(
    (t) =>
      t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isLoading) return <Spinner />;

  return (
    <div className="tenant-list">
      <div className="page-header">
        <div>
          <h1>Tenant Management</h1>
          <p className="text-secondary">Manage tenant configurations and access</p>
        </div>
        <Link to="/admin/tenants/new" className="button button-primary">
          <Plus size={16} />
          New Tenant
        </Link>
      </div>

      <Card className="mb-6">
        <div className="search-box">
          <Search size={20} />
          <input
            type="text"
            placeholder="Search tenants..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
      </Card>

      {filteredTenants?.length === 0 ? (
        <EmptyState
          title="No tenants found"
          description={
            searchTerm
              ? 'Try adjusting your search criteria'
              : 'Get started by creating your first tenant'
          }
          action={
            !searchTerm && (
              <Link to="/admin/tenants/new" className="button button-primary">
                <Plus size={16} />
                Create Tenant
              </Link>
            )
          }
        />
      ) : (
        <div className="tenant-grid">
          {filteredTenants?.map((tenant) => (
            <Card key={tenant.id} className="tenant-card">
              <div className="tenant-card-header">
                <div>
                  <h3 className="tenant-name">{tenant.name}</h3>
                  <p className="tenant-id">{tenant.id}</p>
                </div>
                <Badge variant={tenant.enabled ? 'success' : 'error'}>
                  {tenant.enabled ? 'Active' : 'Disabled'}
                </Badge>
              </div>

              <div className="tenant-card-body">
                <div className="tenant-stat">
                  <span className="stat-label">Rate Limit</span>
                  <span className="stat-value">{tenant.rate_limit_rpm}/min</span>
                </div>
                <div className="tenant-stat">
                  <span className="stat-label">Budget</span>
                  <span className="stat-value">${tenant.budget_limit}</span>
                </div>
                <div className="tenant-stat">
                  <span className="stat-label">Monthly Quota</span>
                  <span className="stat-value">{tenant.quota_monthly_requests.toLocaleString()}</span>
                </div>
                <div className="tenant-stat">
                  <span className="stat-label">Enforcement</span>
                  <Badge variant={tenant.budget_enforcement === 'block' ? 'error' : 'warning'}>
                    {tenant.budget_enforcement}
                  </Badge>
                </div>
              </div>

              <div className="tenant-card-actions">
                <Link to={`/admin/tenants/${tenant.id}`} className="button button-sm button-secondary">
                  <Edit size={16} />
                  Edit
                </Link>
                <button
                  onClick={() => toggleMutation.mutate({ id: tenant.id, enabled: tenant.enabled })}
                  className="button button-sm button-secondary"
                  disabled={toggleMutation.isPending}
                >
                  {tenant.enabled ? <PowerOff size={16} /> : <Power size={16} />}
                  {tenant.enabled ? 'Disable' : 'Enable'}
                </button>
                <button
                  onClick={() => setDeleteModal({ open: true, tenant })}
                  className="button button-sm button-danger"
                >
                  <Trash2 size={16} />
                  Delete
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteModal.open}
        onClose={() => setDeleteModal({ open: false })}
        title="Delete Tenant"
        footer={
          <>
            <button
              onClick={() => setDeleteModal({ open: false })}
              className="button button-secondary"
            >
              Cancel
            </button>
            <button
              onClick={() => deleteModal.tenant && deleteMutation.mutate(deleteModal.tenant.id)}
              className="button button-danger"
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </button>
          </>
        }
      >
        <p>
          Are you sure you want to delete tenant <strong>{deleteModal.tenant?.name}</strong>? This
          action cannot be undone.
        </p>
      </Modal>
    </div>
  );
};

export default TenantList;
