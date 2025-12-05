# Enterprise MCP Web Frontend

Modern React + TypeScript admin dashboard for the Enterprise MCP server with comprehensive tenant management, cost tracking, branding customization, and agent orchestration.

## Features

### ✨ Complete Admin Dashboard
- **Real-time System Health Monitoring**: Redis, Key Vault, Storage, FoundryIQ status
- **Key Metrics Overview**: Active tenants, agents, requests, and costs
- **Quick Actions**: Fast access to common tasks

### 👥 Tenant Management
- **Full CRUD Operations**: Create, read, update, delete tenants
- **Configuration Panel**: Rate limits, budgets, quotas, notifications
- **Tenant Grid View**: Visual overview with status indicators
- **Search & Filter**: Quick tenant lookup
- **Enable/Disable**: Toggle tenant access

### 🤖 Agent Management
- **Agent Discovery**: Auto-discover from FoundryIQ endpoints
- **Agent Catalog**: Visual grid with capabilities and metadata
- **Status Tracking**: Active/inactive agent monitoring
- **Search Functionality**: Find agents by name, type, or description

### 💰 Cost Management
- **Cost Analytics Dashboard**: Visualize spending across services
- **Tenant Cost Breakdown**: Per-tenant cost tracking
- **Budget Monitoring**: Real-time budget vs actual comparison
- **Service Cost Charts**: Pie and bar charts for cost analysis
- **Over-Budget Alerts**: Visual indicators for budget violations

### 🎨 Branding Manager
- **Global & Tenant-Level Branding**: Hierarchical theme system
- **Color Customization**: Primary, secondary, accent colors
- **Logo Upload**: Custom logo support
- **Typography Control**: Font family selection
- **Live Preview Mode**: See changes in real-time
- **Custom CSS**: Advanced customization options
- **Inheritance System**: Tenants can inherit or override global branding

### 🔔 Notification Center
- **In-App Notifications**: Real-time alerts and messages
- **Notification Types**: Info, warning, error, success
- **Read/Unread Tracking**: Mark as read functionality
- **Preferences Management**: Configure notification channels
- **Action Links**: Direct navigation from notifications

### ⚙️ Settings
- **System Information**: Version, status, environment
- **Feature Flags**: Enable/disable platform features
- **Maintenance Actions**: Cache clearing, system reset
- **Environment Variables**: Configuration overview

### 🚀 Setup Wizard
- **First-Time Setup Flow**: Guided 4-step onboarding
- **Tenant Creation**: Initial tenant configuration
- **Agent Discovery**: Optional FoundryIQ integration
- **Branding Setup**: Quick theme customization
- **Progress Tracking**: Visual step indicators

## Tech Stack

- **React 18**: Modern UI library
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **React Router**: Client-side routing
- **TanStack Query**: Data fetching and caching
- **React Hook Form**: Form state management
- **Recharts**: Data visualization
- **Lucide React**: Icon system
- **Sonner**: Toast notifications
- **Date-fns**: Date formatting

## Project Structure

```
web/
├── src/
│   ├── api/
│   │   ├── client.ts          # Axios instance with interceptors
│   │   └── services.ts        # API service methods
│   ├── components/
│   │   ├── Layout.tsx         # Main layout with sidebar
│   │   └── ui.tsx             # Reusable UI components
│   ├── context/
│   │   ├── TenantContext.tsx  # Tenant state management
│   │   └── ThemeContext.tsx   # Theme/branding management
│   ├── pages/
│   │   ├── Chat.tsx           # Chat interface
│   │   └── admin/
│   │       ├── Dashboard.tsx          # Main dashboard
│   │       ├── TenantList.tsx         # Tenant grid view
│   │       ├── TenantForm.tsx         # Create/edit tenant
│   │       ├── AgentList.tsx          # Agent catalog
│   │       ├── CostDashboard.tsx      # Cost analytics
│   │       ├── BrandingManager.tsx    # Theme customization
│   │       ├── NotificationCenter.tsx # Notifications
│   │       ├── Settings.tsx           # System settings
│   │       └── SetupWizard.tsx        # First-time setup
│   ├── styles/
│   │   └── app.css            # Global styles
│   ├── types/
│   │   └── index.ts           # TypeScript definitions
│   ├── App.tsx                # Root component with routes
│   └── main.tsx               # Application entry point
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend server running on http://localhost:8000

### Installation

```bash
cd web
npm install
```

### Development

```bash
npm run dev
```

The app will be available at http://localhost:5173

### Build for Production

```bash
npm run build
```

Output will be in `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Environment Variables

Create a `.env` file in the `web/` directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

For production:

```env
VITE_API_BASE_URL=https://your-backend.azurecontainerapps.io
```

## Configuration

### API Client

The API client (`src/api/client.ts`) automatically:
- Adds `X-Tenant-ID` header from localStorage
- Handles authentication errors (403)
- Handles budget exceeded errors (402)
- Sets 30-second timeout

### React Query

Configured with:
- No refetch on window focus
- 1 retry on failure
- 30-second stale time

### Theme System

The app uses CSS variables for theming:
- `--color-primary`: Main brand color
- `--color-secondary`: Secondary color
- `--color-accent`: Accent color
- Colors can be customized via Branding Manager

## Key Features Explained

### Multi-Tenant Architecture

The app supports multiple tenants:
- Tenant ID stored in localStorage
- Automatically added to all API requests
- Switch tenants via context provider
- Per-tenant branding customization

### Cost Tracking

Real-time cost visualization:
- Pie chart: Cost breakdown by service
- Bar chart: Cost per tenant vs budget
- Table: Budget status with alerts
- Mock data included for testing

### Branding System

Hierarchical branding:
1. **Global**: Default branding for all tenants
2. **Tenant**: Override global with custom branding
3. **Inheritance**: Tenants can inherit global settings

Supports:
- Color schemes (primary, secondary, accent, background, text)
- Typography (font family selection)
- Logos (upload and display)
- Custom CSS (advanced users)
- Live preview mode

### Agent Discovery

Automatically discover agents:
1. Enter FoundryIQ endpoint
2. Click "Discover Agents"
3. Agents are fetched and displayed
4. View capabilities and metadata

## Available Routes

### Public Routes
- `/chat` - Chat interface with agents

### Admin Routes (under `/admin`)
- `/admin` - Dashboard overview
- `/admin/tenants` - Tenant list
- `/admin/tenants/new` - Create tenant
- `/admin/tenants/:id` - Edit tenant
- `/admin/agents` - Agent management
- `/admin/costs` - Cost dashboard
- `/admin/branding` - Branding manager
- `/admin/notifications` - Notification center
- `/admin/settings` - System settings
- `/admin/setup` - Setup wizard (optional)

## Component Library

### Reusable Components (`src/components/ui.tsx`)

- **Card**: Container with optional header and actions
- **Spinner**: Loading indicator
- **EmptyState**: No data placeholder
- **Badge**: Status indicator
- **Modal**: Dialog overlay
- **StatsCard**: Metric display with icon

### Layout Components

- **Layout**: Main admin layout with sidebar
- **Navigation**: Responsive sidebar navigation

## API Integration

All API calls use TypeScript types for type safety:

```typescript
import api from '@/api/services';

// Get tenants
const tenants = await api.tenants.list();

// Create tenant
const newTenant = await api.tenants.create({
  id: 'customer-001',
  name: 'Customer One',
  // ...
});

// Get costs
const costs = await api.costs.get('2024-01-01', '2024-12-31');
```

## Styling

### CSS Architecture

- **CSS Variables**: Theme customization
- **Responsive Design**: Mobile-first approach
- **Grid Layouts**: Flexible component grids
- **Utility Classes**: Common patterns

### Responsive Breakpoints

- Desktop: > 768px
- Mobile: ≤ 768px

## Testing

The frontend can be tested against the backend:

1. Start backend: `docker-compose up`
2. Start frontend: `npm run dev`
3. Navigate to http://localhost:5173
4. Use tenant ID: `default`

## Troubleshooting

### API Connection Issues

**Problem**: Cannot connect to backend

**Solution**:
```bash
# Check backend is running
curl http://localhost:8000/health

# Check VITE_API_BASE_URL in .env
```

### Tenant Not Found

**Problem**: 403 errors

**Solution**:
- Ensure tenant exists in backend
- Check localStorage for `tenant_id`
- Use tenant ID: `default` for testing

### Build Errors

**Problem**: TypeScript errors during build

**Solution**:
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for type errors
npm run lint
```

## Future Enhancements

### Planned Features
- [ ] Real-time WebSocket notifications
- [ ] Advanced analytics dashboards
- [ ] Multi-language support (i18n)
- [ ] Dark mode toggle
- [ ] Keyboard shortcuts
- [ ] Accessibility improvements (ARIA labels)
- [ ] E2E testing with Playwright
- [ ] Component Storybook

### Backend Integration TODOs
- [ ] Replace mock cost data with real API
- [ ] Implement authentication flow
- [ ] Add file upload progress indicators
- [ ] WebSocket connection for live updates

## Performance

- **Code Splitting**: Automatic by Vite
- **Lazy Loading**: Route-based splitting
- **Query Caching**: TanStack Query
- **Optimistic Updates**: Instant UI feedback
- **Debounced Search**: Reduced API calls

## Security

- **XSS Protection**: React's built-in escaping
- **CSRF**: Token validation (when auth enabled)
- **Secrets**: Never commit API keys
- **HTTPS**: Required for production
- **Content Security Policy**: Recommended

## Deployment

### Azure Static Web Apps

```bash
npm run build
az staticwebapp create --name mcp-frontend --resource-group mcp-server-prod
az staticwebapp upload --name mcp-frontend --source ./dist
```

### Azure CDN (via Container Apps)

Already configured in main Bicep template. Frontend is served from Container Apps with CDN.

## Contributing

1. Follow TypeScript best practices
2. Use functional components with hooks
3. Add types for all props and state
4. Write descriptive commit messages
5. Test against local backend

## Support

For issues or questions:
- Check backend logs: `docker-compose logs -f backend`
- Check browser console for errors
- Review API responses in Network tab
- Consult [GETTING_STARTED.md](../GETTING_STARTED.md)

## License

Copyright © 2024. All rights reserved.
