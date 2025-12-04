/**
 * Admin page component
 */
import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';

const AdminDashboard: React.FC = () => {
  return (
    <div className="container" style={{ marginTop: '40px' }}>
      <h1>Admin Dashboard</h1>
      <p className="text-secondary">Manage tenants, sources, and configuration</p>

      <div style={{ marginTop: '32px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
        <div className="card">
          <h3>Tenants</h3>
          <p className="text-secondary">Manage tenant configurations</p>
          <Link to="/admin/tenants" className="button" style={{ marginTop: '12px', display: 'inline-block', textDecoration: 'none' }}>
            Manage Tenants
          </Link>
        </div>

        <div className="card">
          <h3>Data Sources</h3>
          <p className="text-secondary">Discover and configure data sources</p>
          <Link to="/admin/sources" className="button" style={{ marginTop: '12px', display: 'inline-block', textDecoration: 'none' }}>
            Manage Sources
          </Link>
        </div>

        <div className="card">
          <h3>Branding</h3>
          <p className="text-secondary">Customize theme and branding</p>
          <Link to="/admin/branding" className="button" style={{ marginTop: '12px', display: 'inline-block', textDecoration: 'none' }}>
            Customize Branding
          </Link>
        </div>

        <div className="card">
          <h3>Settings</h3>
          <p className="text-secondary">Application settings and configuration</p>
          <Link to="/admin/settings" className="button" style={{ marginTop: '12px', display: 'inline-block', textDecoration: 'none' }}>
            Configure Settings
          </Link>
        </div>
      </div>
    </div>
  );
};

const Admin: React.FC = () => {
  return (
    <div>
      <nav style={{ backgroundColor: 'var(--color-primary)', padding: '16px', color: 'white' }}>
        <div className="container" style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
          <Link to="/admin" style={{ color: 'white', textDecoration: 'none', fontWeight: 'bold' }}>
            Enterprise MCP Admin
          </Link>
          <Link to="/chat" style={{ color: 'white', textDecoration: 'none' }}>
            Back to Chat
          </Link>
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<AdminDashboard />} />
        <Route
          path="/tenants"
          element={
            <div className="container" style={{ marginTop: '40px' }}>
              <h1>Tenant Management</h1>
              <p>Tenant management interface coming soon...</p>
            </div>
          }
        />
        <Route
          path="/sources"
          element={
            <div className="container" style={{ marginTop: '40px' }}>
              <h1>Data Sources</h1>
              <p>Data source management interface coming soon...</p>
            </div>
          }
        />
        <Route
          path="/branding"
          element={
            <div className="container" style={{ marginTop: '40px' }}>
              <h1>Branding</h1>
              <p>Branding customization interface coming soon...</p>
            </div>
          }
        />
        <Route
          path="/settings"
          element={
            <div className="container" style={{ marginTop: '40px' }}>
              <h1>Settings</h1>
              <p>Settings interface coming soon...</p>
            </div>
          }
        />
      </Routes>
    </div>
  );
};

export default Admin;
