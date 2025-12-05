/**
 * Branding Manager - Customize themes and branding
 */
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { Upload, Save, Eye, RefreshCw } from 'lucide-react';
import { Card, Spinner, Badge } from '../../components/ui';
import api from '../../api/services';
import type { BrandingConfig } from '../../types';
import { toast } from 'sonner';

const BrandingManager: React.FC = () => {
  const queryClient = useQueryClient();
  const [scope, setScope] = useState<'global' | string>('global');
  const [previewMode, setPreviewMode] = useState(false);
  const [logoFile, setLogoFile] = useState<File | null>(null);

  const { register, handleSubmit, reset, watch } = useForm<BrandingConfig>();

  const { data: branding, isLoading } = useQuery({
    queryKey: ['branding', scope],
    queryFn: () =>
      scope === 'global'
        ? api.branding.getGlobal().then((res) => res.data)
        : api.branding.getTenant(scope).then((res) => res.data),
  });

  const { data: tenants } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => api.tenants.list().then((res) => res.data),
  });

  useEffect(() => {
    if (branding) {
      reset(branding);
    }
  }, [branding, reset]);

  const saveMutation = useMutation({
    mutationFn: (data: BrandingConfig) =>
      scope === 'global'
        ? api.branding.setGlobal(data)
        : api.branding.setTenant(scope, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branding'] });
      toast.success('Branding updated successfully');
    },
    onError: () => {
      toast.error('Failed to update branding');
    },
  });

  const uploadLogoMutation = useMutation({
    mutationFn: () => {
      if (!logoFile) throw new Error('No file selected');
      return api.branding.uploadLogo(logoFile, scope);
    },
    onSuccess: (_response) => {
      queryClient.invalidateQueries({ queryKey: ['branding'] });
      toast.success('Logo uploaded successfully');
      setLogoFile(null);
    },
    onError: () => {
      toast.error('Failed to upload logo');
    },
  });

  const onSubmit = (data: BrandingConfig) => {
    saveMutation.mutate(data);
  };

  // Apply preview colors in real-time
  const watchedColors = watch();
  useEffect(() => {
    if (previewMode) {
      const root = document.documentElement;
      if (watchedColors.primary_color) root.style.setProperty('--color-primary', watchedColors.primary_color);
      if (watchedColors.secondary_color) root.style.setProperty('--color-secondary', watchedColors.secondary_color);
      if (watchedColors.accent_color) root.style.setProperty('--color-accent', watchedColors.accent_color);
      if (watchedColors.background_color) root.style.setProperty('--color-background', watchedColors.background_color);
      if (watchedColors.text_color) root.style.setProperty('--color-text', watchedColors.text_color);
    }
  }, [previewMode, watchedColors]);

  const resetPreview = () => {
    setPreviewMode(false);
    const root = document.documentElement;
    root.style.removeProperty('--color-primary');
    root.style.removeProperty('--color-secondary');
    root.style.removeProperty('--color-accent');
    root.style.removeProperty('--color-background');
    root.style.removeProperty('--color-text');
  };

  if (isLoading) return <Spinner />;

  return (
    <div className="branding-manager">
      <div className="page-header">
        <div>
          <h1>Branding Manager</h1>
          <p className="text-secondary">Customize theme and white-label configuration</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setPreviewMode(!previewMode)}
            className={`button ${previewMode ? 'button-primary' : 'button-secondary'}`}
          >
            <Eye size={16} />
            {previewMode ? 'Exit Preview' : 'Preview Mode'}
          </button>
          {previewMode && (
            <button onClick={resetPreview} className="button button-secondary">
              <RefreshCw size={16} />
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Scope Selector */}
      <Card className="mb-6">
        <div className="form-group">
          <label className="form-label">Branding Scope</label>
          <div className="flex gap-2 items-center">
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value)}
              className="input"
              style={{ flex: 1 }}
            >
              <option value="global">Global (Default)</option>
              {tenants?.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.name} ({tenant.id})
                </option>
              ))}
            </select>
            <Badge variant={scope === 'global' ? 'info' : 'default'}>
              {scope === 'global' ? 'Affects all tenants' : 'Tenant-specific'}
            </Badge>
          </div>
        </div>
      </Card>

      <form onSubmit={handleSubmit(onSubmit)}>
        {/* Colors */}
        <Card title="Color Scheme" className="mb-6">
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="primary_color" className="form-label">
                Primary Color
              </label>
              <div className="color-input-group">
                <input
                  id="primary_color"
                  type="color"
                  {...register('primary_color')}
                  className="color-picker"
                />
                <input
                  type="text"
                  {...register('primary_color')}
                  className="input"
                  placeholder="#0078D4"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="secondary_color" className="form-label">
                Secondary Color
              </label>
              <div className="color-input-group">
                <input
                  id="secondary_color"
                  type="color"
                  {...register('secondary_color')}
                  className="color-picker"
                />
                <input
                  type="text"
                  {...register('secondary_color')}
                  className="input"
                  placeholder="#50E6FF"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="accent_color" className="form-label">
                Accent Color
              </label>
              <div className="color-input-group">
                <input
                  id="accent_color"
                  type="color"
                  {...register('accent_color')}
                  className="color-picker"
                />
                <input
                  type="text"
                  {...register('accent_color')}
                  className="input"
                  placeholder="#FFB900"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="background_color" className="form-label">
                Background Color
              </label>
              <div className="color-input-group">
                <input
                  id="background_color"
                  type="color"
                  {...register('background_color')}
                  className="color-picker"
                />
                <input
                  type="text"
                  {...register('background_color')}
                  className="input"
                  placeholder="#FFFFFF"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="text_color" className="form-label">
                Text Color
              </label>
              <div className="color-input-group">
                <input
                  id="text_color"
                  type="color"
                  {...register('text_color')}
                  className="color-picker"
                />
                <input
                  type="text"
                  {...register('text_color')}
                  className="input"
                  placeholder="#323130"
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Typography */}
        <Card title="Typography" className="mb-6">
          <div className="form-group">
            <label htmlFor="font_family" className="form-label">
              Font Family
            </label>
            <select id="font_family" className="input" {...register('font_family')}>
              <option value="Segoe UI, -apple-system, BlinkMacSystemFont, sans-serif">
                Segoe UI (Default)
              </option>
              <option value="Inter, sans-serif">Inter</option>
              <option value="Roboto, sans-serif">Roboto</option>
              <option value="Open Sans, sans-serif">Open Sans</option>
              <option value="Lato, sans-serif">Lato</option>
              <option value="Poppins, sans-serif">Poppins</option>
            </select>
          </div>
        </Card>

        {/* Company Info */}
        <Card title="Company Information" className="mb-6">
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="company_name" className="form-label">
                Company Name
              </label>
              <input
                id="company_name"
                type="text"
                className="input"
                {...register('company_name')}
                placeholder="Your Company"
              />
            </div>

            <div className="form-group">
              <label htmlFor="tagline" className="form-label">
                Tagline
              </label>
              <input
                id="tagline"
                type="text"
                className="input"
                {...register('tagline')}
                placeholder="Your company tagline"
              />
            </div>
          </div>
        </Card>

        {/* Logo Upload */}
        <Card title="Logo" className="mb-6">
          <div className="form-group">
            <label className="form-label">Upload Logo</label>
            <div className="upload-area">
              {branding?.logo_url && (
                <div className="current-logo mb-4">
                  <img src={branding.logo_url} alt="Current logo" className="logo-preview" />
                </div>
              )}
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setLogoFile(e.target.files?.[0] || null)}
                className="file-input"
              />
              {logoFile && (
                <button
                  type="button"
                  onClick={() => uploadLogoMutation.mutate()}
                  className="button button-primary mt-2"
                  disabled={uploadLogoMutation.isPending}
                >
                  <Upload size={16} />
                  {uploadLogoMutation.isPending ? 'Uploading...' : 'Upload Logo'}
                </button>
              )}
            </div>
          </div>
        </Card>

        {/* Custom CSS */}
        <Card title="Custom CSS" className="mb-6">
          <div className="form-group">
            <label htmlFor="custom_css" className="form-label">
              Custom CSS (Advanced)
            </label>
            <textarea
              id="custom_css"
              {...register('custom_css')}
              className="textarea"
              rows={10}
              placeholder=".custom-class { color: red; }"
            />
            <p className="form-hint">Add custom CSS to further customize the appearance</p>
          </div>
        </Card>

        {/* Inheritance (for tenant scopes) */}
        {scope !== 'global' && (
          <Card className="mb-6">
            <div className="form-group">
              <label className="form-checkbox">
                <input type="checkbox" {...register('inherit_global')} />
                <span>Inherit from global branding</span>
              </label>
              <p className="form-hint">
                When enabled, this tenant will inherit global branding settings unless overridden
              </p>
            </div>
          </Card>
        )}

        {/* Actions */}
        <div className="form-actions">
          <button type="button" onClick={() => reset(branding)} className="button button-secondary">
            Reset
          </button>
          <button type="submit" className="button button-primary" disabled={saveMutation.isPending}>
            <Save size={16} />
            {saveMutation.isPending ? 'Saving...' : 'Save Branding'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default BrandingManager;
