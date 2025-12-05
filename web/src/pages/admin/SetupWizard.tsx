/**
 * Setup Wizard - First-time setup flow
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { CheckCircle, Circle, ArrowRight, ArrowLeft, Check } from 'lucide-react';
import { Card, Badge } from '../../components/ui';
import api from '../../api/services';
import type { Tenant, BrandingConfig } from '../../types';
import { toast } from 'sonner';

interface SetupState {
  tenant: Partial<Tenant>;
  branding: BrandingConfig;
  discoveryEndpoint: string;
  complete: boolean;
}

const STEPS = [
  { id: 'tenant', title: 'Create First Tenant', description: 'Set up your initial tenant configuration' },
  { id: 'discovery', title: 'Discover Agents', description: 'Connect to your FoundryIQ endpoint' },
  { id: 'branding', title: 'Customize Branding', description: 'Apply your brand colors and logo' },
  { id: 'complete', title: 'Complete Setup', description: 'Review and finish' },
];

const SetupWizard: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [setupState, setSetupState] = useState<SetupState>({
    tenant: {
      id: '',
      name: '',
      enabled: true,
      rate_limit_rpm: 100,
      rate_limit_rpd: 10000,
      quota_monthly_requests: 100000,
      budget_limit: 1000,
      budget_threshold: 90,
      budget_enforcement: 'warn',
      notification_channels: ['in-app'],
    },
    branding: {
      primary_color: '#0078D4',
      secondary_color: '#50E6FF',
      accent_color: '#FFB900',
    },
    discoveryEndpoint: '',
    complete: false,
  });

  const createTenantMutation = useMutation({
    mutationFn: () => api.tenants.create(setupState.tenant),
    onSuccess: () => {
      toast.success('Tenant created successfully');
      setCurrentStep(1);
    },
    onError: () => {
      toast.error('Failed to create tenant');
    },
  });

  const discoverAgentsMutation = useMutation({
    mutationFn: () => api.agents.discover(setupState.discoveryEndpoint),
    onSuccess: (response) => {
      toast.success(`Discovered ${response.data.agents.length} agents`);
      setCurrentStep(2);
    },
    onError: () => {
      toast.error('Failed to discover agents');
    },
  });

  const saveBrandingMutation = useMutation({
    mutationFn: () => api.branding.setGlobal(setupState.branding),
    onSuccess: () => {
      toast.success('Branding saved successfully');
      setCurrentStep(3);
    },
    onError: () => {
      toast.error('Failed to save branding');
    },
  });

  const handleNext = () => {
    switch (currentStep) {
      case 0:
        createTenantMutation.mutate();
        break;
      case 1:
        if (setupState.discoveryEndpoint) {
          discoverAgentsMutation.mutate();
        } else {
          setCurrentStep(2); // Skip if no endpoint
        }
        break;
      case 2:
        saveBrandingMutation.mutate();
        break;
      case 3:
        navigate('/admin');
        break;
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    setCurrentStep(currentStep + 1);
  };

  const updateTenant = (updates: Partial<Tenant>) => {
    setSetupState({ ...setupState, tenant: { ...setupState.tenant, ...updates } });
  };

  const updateBranding = (updates: BrandingConfig) => {
    setSetupState({ ...setupState, branding: { ...setupState.branding, ...updates } });
  };

  const isStepValid = () => {
    switch (currentStep) {
      case 0:
        return setupState.tenant.id && setupState.tenant.name && setupState.tenant.foundry_endpoint;
      case 1:
        return true; // Optional step
      case 2:
        return true; // Optional step
      case 3:
        return true;
      default:
        return false;
    }
  };

  return (
    <div className="setup-wizard">
      <div className="wizard-header">
        <h1>Welcome to Enterprise MCP</h1>
        <p className="text-secondary">Let's get you set up in a few simple steps</p>
      </div>

      {/* Progress Steps */}
      <Card className="mb-6">
        <div className="wizard-steps">
          {STEPS.map((step, index) => (
            <div
              key={step.id}
              className={`wizard-step ${index === currentStep ? 'active' : ''} ${
                index < currentStep ? 'completed' : ''
              }`}
            >
              <div className="step-indicator">
                {index < currentStep ? (
                  <CheckCircle size={24} className="text-success" />
                ) : index === currentStep ? (
                  <Circle size={24} className="text-primary" />
                ) : (
                  <Circle size={24} className="text-secondary" />
                )}
              </div>
              <div className="step-content">
                <div className="step-title">{step.title}</div>
                <div className="step-description">{step.description}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Step Content */}
      <Card className="mb-6">
        {currentStep === 0 && (
          <div className="wizard-content">
            <h2>Create Your First Tenant</h2>
            <p className="text-secondary mb-4">
              Tenants represent different customers or departments using your MCP server.
            </p>

            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Tenant ID *</label>
                <input
                  type="text"
                  className="input"
                  value={setupState.tenant.id}
                  onChange={(e) => updateTenant({ id: e.target.value })}
                  placeholder="customer-001"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Tenant Name *</label>
                <input
                  type="text"
                  className="input"
                  value={setupState.tenant.name}
                  onChange={(e) => updateTenant({ name: e.target.value })}
                  placeholder="Customer Name"
                />
              </div>

              <div className="form-group full-width">
                <label className="form-label">FoundryIQ Endpoint *</label>
                <input
                  type="url"
                  className="input"
                  value={setupState.tenant.foundry_endpoint || ''}
                  onChange={(e) => updateTenant({ foundry_endpoint: e.target.value })}
                  placeholder="https://foundry.azure.com/..."
                />
              </div>

              <div className="form-group">
                <label className="form-label">Budget Limit ($)</label>
                <input
                  type="number"
                  className="input"
                  value={setupState.tenant.budget_limit}
                  onChange={(e) => updateTenant({ budget_limit: parseFloat(e.target.value) })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Rate Limit (req/min)</label>
                <input
                  type="number"
                  className="input"
                  value={setupState.tenant.rate_limit_rpm}
                  onChange={(e) => updateTenant({ rate_limit_rpm: parseInt(e.target.value) })}
                />
              </div>
            </div>
          </div>
        )}

        {currentStep === 1 && (
          <div className="wizard-content">
            <h2>Discover Agents (Optional)</h2>
            <p className="text-secondary mb-4">
              Connect to your FoundryIQ endpoint to automatically discover available DataAgents.
            </p>

            <div className="form-group">
              <label className="form-label">Discovery Endpoint</label>
              <input
                type="url"
                className="input"
                value={setupState.discoveryEndpoint}
                onChange={(e) => setSetupState({ ...setupState, discoveryEndpoint: e.target.value })}
                placeholder="https://foundry.azure.com/..."
              />
              <p className="form-hint">
                Leave blank to skip this step. You can discover agents later from the admin panel.
              </p>
            </div>

            <Badge variant="info">You can add more agents later from the Admin panel</Badge>
          </div>
        )}

        {currentStep === 2 && (
          <div className="wizard-content">
            <h2>Customize Branding (Optional)</h2>
            <p className="text-secondary mb-4">
              Apply your brand colors to customize the appearance of the platform.
            </p>

            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Primary Color</label>
                <div className="color-input-group">
                  <input
                    type="color"
                    value={setupState.branding.primary_color}
                    onChange={(e) => updateBranding({ primary_color: e.target.value })}
                    className="color-picker"
                  />
                  <input
                    type="text"
                    value={setupState.branding.primary_color}
                    onChange={(e) => updateBranding({ primary_color: e.target.value })}
                    className="input"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Secondary Color</label>
                <div className="color-input-group">
                  <input
                    type="color"
                    value={setupState.branding.secondary_color}
                    onChange={(e) => updateBranding({ secondary_color: e.target.value })}
                    className="color-picker"
                  />
                  <input
                    type="text"
                    value={setupState.branding.secondary_color}
                    onChange={(e) => updateBranding({ secondary_color: e.target.value })}
                    className="input"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Accent Color</label>
                <div className="color-input-group">
                  <input
                    type="color"
                    value={setupState.branding.accent_color}
                    onChange={(e) => updateBranding({ accent_color: e.target.value })}
                    className="color-picker"
                  />
                  <input
                    type="text"
                    value={setupState.branding.accent_color}
                    onChange={(e) => updateBranding({ accent_color: e.target.value })}
                    className="input"
                  />
                </div>
              </div>
            </div>

            <Badge variant="info">You can customize more branding options later</Badge>
          </div>
        )}

        {currentStep === 3 && (
          <div className="wizard-content">
            <div className="completion-message">
              <div className="completion-icon">
                <Check size={48} />
              </div>
              <h2>Setup Complete!</h2>
              <p className="text-secondary mb-4">
                Your Enterprise MCP server is ready to use. Here's what you can do next:
              </p>

              <div className="next-steps">
                <div className="next-step-item">
                  <CheckCircle size={20} className="text-success" />
                  <span>Tenant created and configured</span>
                </div>
                {setupState.discoveryEndpoint && (
                  <div className="next-step-item">
                    <CheckCircle size={20} className="text-success" />
                    <span>Agents discovered from FoundryIQ</span>
                  </div>
                )}
                <div className="next-step-item">
                  <CheckCircle size={20} className="text-success" />
                  <span>Branding customized</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Navigation */}
      <div className="wizard-actions">
        {currentStep > 0 && currentStep < 3 && (
          <button onClick={handleBack} className="button button-secondary">
            <ArrowLeft size={16} />
            Back
          </button>
        )}
        {currentStep > 0 && currentStep < 3 && (
          <button onClick={handleSkip} className="button button-ghost">
            Skip
          </button>
        )}
        <button
          onClick={handleNext}
          className="button button-primary"
          disabled={!isStepValid() || createTenantMutation.isPending || discoverAgentsMutation.isPending || saveBrandingMutation.isPending}
        >
          {currentStep === 3 ? (
            <>
              <Check size={16} />
              Go to Dashboard
            </>
          ) : (
            <>
              {currentStep === 0 && createTenantMutation.isPending ? 'Creating...' :
               currentStep === 1 && discoverAgentsMutation.isPending ? 'Discovering...' :
               currentStep === 2 && saveBrandingMutation.isPending ? 'Saving...' : 'Next'}
              <ArrowRight size={16} />
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default SetupWizard;
