/**
 * Tenant Form - Create/Edit tenant
 */
import React, { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { Save, ArrowLeft } from 'lucide-react';
import { Card, Spinner } from '../../components/ui';
import api from '../../api/services';
import type { Tenant } from '../../types';
import { toast } from 'sonner';

const TenantForm: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEdit = !!id;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<Tenant>();

  const { data: tenant, isLoading } = useQuery({
    queryKey: ['tenant', id],
    queryFn: () => (id ? api.tenants.get(id).then((res) => res.data) : null),
    enabled: isEdit,
  });

  useEffect(() => {
    if (tenant) {
      reset(tenant);
    }
  }, [tenant, reset]);

  const saveMutation = useMutation({
    mutationFn: (data: Partial<Tenant>) =>
      isEdit ? api.tenants.update(id!, data) : api.tenants.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      toast.success(isEdit ? 'Tenant updated' : 'Tenant created');
      navigate('/admin/tenants');
    },
    onError: () => {
      toast.error(isEdit ? 'Failed to update tenant' : 'Failed to create tenant');
    },
  });

  const onSubmit = (data: Tenant) => {
    saveMutation.mutate(data);
  };

  if (isEdit && isLoading) return <Spinner />;

  return (
    <div className="tenant-form">
      <div className="page-header">
        <div>
          <button onClick={() => navigate('/admin/tenants')} className="button button-ghost mb-2">
            <ArrowLeft size={16} />
            Back to Tenants
          </button>
          <h1>{isEdit ? 'Edit Tenant' : 'Create New Tenant'}</h1>
          <p className="text-secondary">
            {isEdit ? 'Update tenant configuration' : 'Set up a new tenant'}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <Card title="Basic Information" className="mb-6">
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="id" className="form-label">
                Tenant ID *
              </label>
              <input
                id="id"
                type="text"
                className="input"
                {...register('id', { required: 'Tenant ID is required' })}
                disabled={isEdit}
                placeholder="customer-001"
              />
              {errors.id && <span className="form-error">{errors.id.message}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="name" className="form-label">
                Tenant Name *
              </label>
              <input
                id="name"
                type="text"
                className="input"
                {...register('name', { required: 'Tenant name is required' })}
                placeholder="Customer Name"
              />
              {errors.name && <span className="form-error">{errors.name.message}</span>}
            </div>

            <div className="form-group full-width">
              <label htmlFor="foundry_endpoint" className="form-label">
                FoundryIQ Endpoint *
              </label>
              <input
                id="foundry_endpoint"
                type="url"
                className="input"
                {...register('foundry_endpoint', {
                  required: 'FoundryIQ endpoint is required',
                })}
                placeholder="https://foundry.azure.com/..."
              />
              {errors.foundry_endpoint && (
                <span className="form-error">{errors.foundry_endpoint.message}</span>
              )}
            </div>

            <div className="form-group">
              <label className="form-checkbox">
                <input type="checkbox" {...register('enabled')} />
                <span>Enable tenant</span>
              </label>
            </div>
          </div>
        </Card>

        <Card title="Rate Limits" className="mb-6">
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="rate_limit_rpm" className="form-label">
                Requests Per Minute
              </label>
              <input
                id="rate_limit_rpm"
                type="number"
                className="input"
                {...register('rate_limit_rpm', { valueAsNumber: true, min: 1 })}
                placeholder="100"
              />
            </div>

            <div className="form-group">
              <label htmlFor="rate_limit_rpd" className="form-label">
                Requests Per Day
              </label>
              <input
                id="rate_limit_rpd"
                type="number"
                className="input"
                {...register('rate_limit_rpd', { valueAsNumber: true, min: 1 })}
                placeholder="10000"
              />
            </div>

            <div className="form-group full-width">
              <label htmlFor="quota_monthly_requests" className="form-label">
                Monthly Request Quota
              </label>
              <input
                id="quota_monthly_requests"
                type="number"
                className="input"
                {...register('quota_monthly_requests', { valueAsNumber: true, min: 1 })}
                placeholder="100000"
              />
            </div>
          </div>
        </Card>

        <Card title="Budget Management" className="mb-6">
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="budget_limit" className="form-label">
                Budget Limit ($)
              </label>
              <input
                id="budget_limit"
                type="number"
                step="0.01"
                className="input"
                {...register('budget_limit', { valueAsNumber: true, min: 0 })}
                placeholder="1000.00"
              />
            </div>

            <div className="form-group">
              <label htmlFor="budget_threshold" className="form-label">
                Alert Threshold (%)
              </label>
              <input
                id="budget_threshold"
                type="number"
                className="input"
                {...register('budget_threshold', { valueAsNumber: true, min: 0, max: 100 })}
                placeholder="90"
              />
            </div>

            <div className="form-group full-width">
              <label htmlFor="budget_enforcement" className="form-label">
                Enforcement Mode
              </label>
              <select id="budget_enforcement" className="input" {...register('budget_enforcement')}>
                <option value="warn">Warn Only</option>
                <option value="block">Block Requests</option>
              </select>
            </div>
          </div>
        </Card>

        <Card title="Notifications" className="mb-6">
          <div className="form-group">
            <label className="form-label">Notification Channels</label>
            <div className="checkbox-group">
              <label className="form-checkbox">
                <input type="checkbox" {...register('notification_channels.0')} value="in-app" />
                <span>In-App Notifications</span>
              </label>
              <label className="form-checkbox">
                <input type="checkbox" {...register('notification_channels.1')} value="email" />
                <span>Email Notifications</span>
              </label>
              <label className="form-checkbox">
                <input type="checkbox" {...register('notification_channels.2')} value="sms" />
                <span>SMS Notifications</span>
              </label>
            </div>
          </div>
        </Card>

        <div className="form-actions">
          <button type="button" onClick={() => navigate('/admin/tenants')} className="button button-secondary">
            Cancel
          </button>
          <button type="submit" className="button button-primary" disabled={saveMutation.isPending}>
            <Save size={16} />
            {saveMutation.isPending ? 'Saving...' : 'Save Tenant'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default TenantForm;
