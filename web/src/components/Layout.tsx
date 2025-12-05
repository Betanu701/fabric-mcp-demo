/**
 * Main application layout with navigation
 */
import React, { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Palette,
  Bell,
  Settings,
  Database,
  DollarSign,
  MessageSquare,
  Menu,
  X,
} from 'lucide-react';
import { useTenant } from '../context/TenantContext';

const Layout: React.FC = () => {
  const location = useLocation();
  const { tenantId } = useTenant();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const navItems = [
    { path: '/admin', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/admin/tenants', icon: Users, label: 'Tenants' },
    { path: '/admin/agents', icon: Database, label: 'Agents' },
    { path: '/admin/costs', icon: DollarSign, label: 'Costs' },
    { path: '/admin/branding', icon: Palette, label: 'Branding' },
    { path: '/admin/notifications', icon: Bell, label: 'Notifications' },
    { path: '/admin/settings', icon: Settings, label: 'Settings' },
  ];

  const isActive = (path: string) => {
    if (path === '/admin') {
      return location.pathname === '/admin';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="layout">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
          <h1 className="header-title">Enterprise MCP Admin</h1>
          <div className="header-actions">
            <span className="tenant-badge">Tenant: {tenantId}</span>
            <Link to="/chat" className="button button-secondary">
              <MessageSquare size={16} />
              Chat
            </Link>
          </div>
        </div>
      </header>

      <div className="layout-body">
        {/* Sidebar */}
        <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
          <nav className="sidebar-nav">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`nav-item ${isActive(item.path) ? 'active' : ''}`}
              >
                <item.icon size={20} />
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
