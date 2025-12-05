/**
 * TypeScript type definitions for the application
 */

export interface Tenant {
  id: string;
  name: string;
  enabled: boolean;
  foundry_endpoint: string;
  rate_limit_rpm: number;
  rate_limit_rpd: number;
  quota_monthly_requests: number;
  budget_limit: number;
  budget_threshold: number;
  budget_enforcement: 'warn' | 'block';
  notification_channels: string[];
  branding?: BrandingConfig;
  created_at?: string;
  updated_at?: string;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'inactive';
  foundry_agent_id: string;
  model_endpoint?: string | null;
  knowledge_sources: string[];
  keywords: string[];
  priority: number;
  created_at?: string;
  updated_at?: string;
}

export interface CostData {
  tenant_id: string;
  total_cost: number;
  period_start: string;
  period_end: string;
  breakdown: {
    [service: string]: number;
  };
}

export interface Budget {
  tenant_id: string;
  limit: number;
  current: number;
  threshold: number;
  enforcement: 'warn' | 'block';
  alerts_sent: number;
}

export interface BrandingConfig {
  inherit_global?: boolean;
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  background_color?: string;
  text_color?: string;
  font_family?: string;
  logo_url?: string;
  favicon_url?: string;
  company_name?: string;
  tagline?: string;
  custom_css?: string;
}

export interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  action_url?: string;
}

export interface UsageMetrics {
  requests_total: number;
  requests_by_agent: Record<string, number>;
  avg_response_time: number;
  error_rate: number;
  period: string;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: {
    redis: boolean;
    key_vault: boolean;
    storage: boolean;
    foundry: boolean;
  };
  timestamp: string;
}

export interface ChatMessage {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  agent_id?: string;
  timestamp?: string;
  metadata?: Record<string, any>;
}

export interface ChatSession {
  id: string;
  tenant_id: string;
  agent_id: string;
  started_at: string;
  ended_at?: string;
  messages: ChatMessage[];
}

export interface SetupStep {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  required: boolean;
}
