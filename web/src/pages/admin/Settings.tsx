/**
 * Settings Page
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Settings as SettingsIcon, Info, Shield, Database, Bell } from 'lucide-react';
import { Card, Badge } from '../../components/ui';
import api from '../../api/services';

const Settings: React.FC = () => {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.health.check().then((res) => res.data),
  });

  return (
    <div className="settings">
      <div className="page-header">
        <h1>Settings</h1>
        <p className="text-secondary">System configuration and information</p>
      </div>

      <Card title="System Information" className="mb-6">
        <div className="settings-grid">
          <div className="setting-item">
            <Info size={20} className="setting-icon" />
            <div>
              <div className="setting-label">Version</div>
              <div className="setting-value">1.0.0</div>
            </div>
          </div>
          <div className="setting-item">
            <Database size={20} className="setting-icon" />
            <div>
              <div className="setting-label">Database Status</div>
              <Badge variant={health?.components.redis ? 'success' : 'error'}>
                {health?.components.redis ? 'Connected' : 'Disconnected'}
              </Badge>
            </div>
          </div>
          <div className="setting-item">
            <Shield size={20} className="setting-icon" />
            <div>
              <div className="setting-label">Security</div>
              <Badge variant="success">Enabled</Badge>
            </div>
          </div>
          <div className="setting-item">
            <Bell size={20} className="setting-icon" />
            <div>
              <div className="setting-label">Notifications</div>
              <Badge variant="success">Active</Badge>
            </div>
          </div>
        </div>
      </Card>

      <Card title="Environment Variables" className="mb-6">
        <div className="env-list">
          <div className="env-item">
            <span className="env-key">API_BASE_URL</span>
            <code className="env-value">{import.meta.env?.VITE_API_BASE_URL || 'http://localhost:8000'}</code>
          </div>
          <div className="env-item">
            <span className="env-key">NODE_ENV</span>
            <code className="env-value">{import.meta.env?.MODE || 'development'}</code>
          </div>
        </div>
      </Card>

      <Card title="Feature Flags" className="mb-6">
        <div className="feature-list">
          <div className="feature-item">
            <div>
              <div className="feature-name">Entra ID Authentication</div>
              <div className="feature-description">Enable Azure AD authentication</div>
            </div>
            <Badge variant="warning">Coming Soon</Badge>
          </div>
          <div className="feature-item">
            <div>
              <div className="feature-name">Communication Services</div>
              <div className="feature-description">Email and SMS notifications via Azure Communication Services</div>
            </div>
            <Badge variant="warning">Coming Soon</Badge>
          </div>
          <div className="feature-item">
            <div>
              <div className="feature-name">Agent Auto-Discovery</div>
              <div className="feature-description">Automatically discover agents from FoundryIQ</div>
            </div>
            <Badge variant="info">Beta</Badge>
          </div>
          <div className="feature-item">
            <div>
              <div className="feature-name">White-Label Branding</div>
              <div className="feature-description">Tenant-specific branding and themes</div>
            </div>
            <Badge variant="success">Enabled</Badge>
          </div>
        </div>
      </Card>

      <Card title="Maintenance">
        <div className="maintenance-actions">
          <button className="button button-secondary">
            <Database size={16} />
            Clear Cache
          </button>
          <button className="button button-secondary">
            <SettingsIcon size={16} />
            Rebuild Indexes
          </button>
          <button className="button button-danger">
            <Shield size={16} />
            Reset System
          </button>
        </div>
      </Card>
    </div>
  );
};

export default Settings;
