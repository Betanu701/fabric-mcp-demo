import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import Chat from './pages/Chat';
import Layout from './components/Layout';
import Dashboard from './pages/admin/Dashboard';
import TenantList from './pages/admin/TenantList';
import TenantForm from './pages/admin/TenantForm';
import AgentList from './pages/admin/AgentList';
import CostDashboard from './pages/admin/CostDashboard';
import BrandingManager from './pages/admin/BrandingManager';
import NotificationCenter from './pages/admin/NotificationCenter';
import Settings from './pages/admin/Settings';
import SetupWizard from './pages/admin/SetupWizard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000,
    },
  },
});

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="app">
        <Routes>
          <Route path="/" element={<Navigate to="/admin" replace />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/setup" element={<SetupWizard />} />
          <Route path="/admin" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="tenants" element={<TenantList />} />
            <Route path="tenants/new" element={<TenantForm />} />
            <Route path="tenants/:id" element={<TenantForm />} />
            <Route path="agents" element={<AgentList />} />
            <Route path="costs" element={<CostDashboard />} />
            <Route path="branding" element={<BrandingManager />} />
            <Route path="notifications" element={<NotificationCenter />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
        <Toaster position="top-right" richColors />
      </div>
    </QueryClientProvider>
  );
};

export default App;
