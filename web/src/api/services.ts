/**
 * API service for all backend interactions
 */
import { apiClient } from './client';
import type {
  Tenant,
  Agent,
  CostData,
  Budget,
  BrandingConfig,
  Notification,
  UsageMetrics,
  HealthStatus,
} from '../types';

export const api = {
  // Health
  health: {
    check: () => apiClient.get<HealthStatus>('/health'),
  },

  // Tenants
  tenants: {
    list: () => apiClient.get<Tenant[]>('/api/admin/tenants'),
    get: (id: string) => apiClient.get<Tenant>(`/api/admin/tenants/${id}`),
    create: (data: Partial<Tenant>) => apiClient.post<Tenant>('/api/admin/tenants', data),
    update: (id: string, data: Partial<Tenant>) =>
      apiClient.put<Tenant>(`/api/admin/tenants/${id}`, data),
    delete: (id: string) => apiClient.delete(`/api/admin/tenants/${id}`),
    enable: (id: string) => apiClient.post(`/api/admin/tenants/${id}/enable`),
    disable: (id: string) => apiClient.post(`/api/admin/tenants/${id}/disable`),
  },

  // Agents
  agents: {
    list: () => apiClient.get<{ agents: Agent[] }>('/api/agents'),
    get: (id: string) => apiClient.get<Agent>(`/api/agents/${id}`),
    discover: (endpoint: string) =>
      apiClient.post<{ agents: Agent[] }>('/api/agents/discover', { endpoint }),
  },

  // Chat
  chat: {
    send: (message: string, agentId?: string, sessionId?: string) =>
      apiClient.post<{ message: string; agent_id: string; session_id: string }>('/api/chat', {
        message,
        agent_id: agentId,
        session_id: sessionId,
      }),
  },

  // Costs
  costs: {
    get: (startDate?: string, endDate?: string) =>
      apiClient.get<CostData>('/api/costs', {
        params: { start_date: startDate, end_date: endDate },
      }),
    getByTenant: (tenantId: string, startDate?: string, endDate?: string) =>
      apiClient.get<CostData>(`/api/costs/tenants/${tenantId}`, {
        params: { start_date: startDate, end_date: endDate },
      }),
  },

  // Budgets
  budgets: {
    get: () => apiClient.get<Budget>('/api/budgets'),
    set: (limit: number, threshold: number, enforcement: 'warn' | 'block') =>
      apiClient.post<Budget>('/api/budgets', { limit, threshold, enforcement }),
  },

  // Branding
  branding: {
    get: () => apiClient.get<BrandingConfig>('/api/branding'),
    getGlobal: () => apiClient.get<BrandingConfig>('/api/admin/branding/global'),
    setGlobal: (data: BrandingConfig) =>
      apiClient.put<BrandingConfig>('/api/admin/branding/global', data),
    getTenant: (tenantId: string) =>
      apiClient.get<BrandingConfig>(`/api/admin/branding/tenants/${tenantId}`),
    setTenant: (tenantId: string, data: BrandingConfig) =>
      apiClient.put<BrandingConfig>(`/api/admin/branding/tenants/${tenantId}`, data),
    uploadLogo: (file: File, scope: 'global' | string) => {
      const formData = new FormData();
      formData.append('logo', file);
      return apiClient.post<{ url: string }>(`/api/admin/branding/${scope}/logo`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    uploadBrandGuide: (file: File, scope: 'global' | string) => {
      const formData = new FormData();
      formData.append('file', file);
      return apiClient.post(`/api/admin/branding/${scope}/guide`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
  },

  // Notifications
  notifications: {
    list: () => apiClient.get<Notification[]>('/api/notifications'),
    markRead: (id: string) => apiClient.post(`/api/notifications/${id}/read`),
    markAllRead: () => apiClient.post('/api/notifications/read-all'),
    getPreferences: () => apiClient.get('/api/notifications/preferences'),
    setPreferences: (channels: string[]) =>
      apiClient.put('/api/notifications/preferences', { channels }),
  },

  // Usage Metrics
  usage: {
    get: (startDate?: string, endDate?: string) =>
      apiClient.get<UsageMetrics>('/api/usage', {
        params: { start_date: startDate, end_date: endDate },
      }),
  },

  // Source Discovery
  sources: {
    discover: () => apiClient.post<{ sources: any[] }>('/api/admin/sources/discover'),
    list: () => apiClient.get<any[]>('/api/admin/sources'),
    add: (data: any) => apiClient.post('/api/admin/sources', data),
    remove: (id: string) => apiClient.delete(`/api/admin/sources/${id}`),
  },
};

export default api;
