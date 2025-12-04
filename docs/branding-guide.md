# Branding Guide - Enterprise MCP Server

## Overview

The Enterprise MCP Server supports hierarchical white-label branding, allowing global defaults with per-tenant overrides. This enables multi-tenant deployments where each customer can customize the look and feel while maintaining a consistent base experience.

## Branding Hierarchy

```
Global Branding (Base)
└── Tenant Branding (Overrides)
    └── Runtime Theme (Applied to UI)
```

### Inheritance Model
- **Global branding** defines defaults for all tenants
- **Tenant branding** overrides specific properties
- **Unset tenant properties** inherit from global
- **`inherit_global: false`** disables inheritance (use tenant values only)

## Branding Properties

### Colors

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `primary_color` | Hex Color | Primary brand color | `#0078D4` |
| `secondary_color` | Hex Color | Secondary accent | `#50E6FF` |
| `accent_color` | Hex Color | Call-to-action color | `#FFB900` |
| `background_color` | Hex Color | Main background | `#FFFFFF` |
| `text_color` | Hex Color | Primary text | `#201F1E` |
| `link_color` | Hex Color | Hyperlinks | `#0078D4` |

### Typography

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `font_family` | CSS Font Stack | Primary font | `Segoe UI, sans-serif` |
| `heading_font` | CSS Font Stack | Heading font | `Segoe UI Semibold, sans-serif` |
| `font_size_base` | CSS Size | Base font size | `14px` |

### Assets

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `logo_url` | URL | Main logo (PNG/SVG) | `https://cdn.../logo.png` |
| `logo_dark_url` | URL | Dark mode logo | `https://cdn.../logo-dark.png` |
| `favicon_url` | URL | Browser favicon | `https://cdn.../favicon.ico` |
| `background_image_url` | URL | Login background | `https://cdn.../bg.jpg` |

### Metadata

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `app_name` | String | Application name | `Contoso MCP` |
| `tagline` | String | Marketing tagline | `AI for Your Business` |
| `custom_css` | String | Custom CSS rules | `.btn { border-radius: 8px; }` |

## Configuration Methods

### Method 1: API Endpoints

#### Get Global Branding
```bash
curl -X GET https://api.example.com/api/branding/global \
  -H "X-Tenant-ID: admin"
```

#### Set Global Branding
```bash
curl -X PUT https://api.example.com/api/branding/global \
  -H "X-Tenant-ID: admin" \
  -H "Content-Type: application/json" \
  -d '{
    "primary_color": "#0078D4",
    "secondary_color": "#50E6FF",
    "accent_color": "#FFB900",
    "font_family": "Segoe UI, sans-serif",
    "app_name": "Enterprise MCP",
    "logo_url": "https://cdn.example.com/logo.png"
  }'
```

#### Get Tenant Branding
```bash
curl -X GET https://api.example.com/api/branding \
  -H "X-Tenant-ID: contoso"
```

#### Set Tenant Branding
```bash
curl -X PUT https://api.example.com/api/branding \
  -H "X-Tenant-ID: contoso" \
  -H "Content-Type: application/json" \
  -d '{
    "inherit_global": true,
    "primary_color": "#FF5722",
    "app_name": "Contoso Data Portal"
  }'
```

### Method 2: Key Vault (Manual)

#### Global Branding Secret
**Secret Name**: `branding-global`

```json
{
  "primary_color": "#0078D4",
  "secondary_color": "#50E6FF",
  "accent_color": "#FFB900",
  "font_family": "Segoe UI, sans-serif",
  "logo_url": "https://cdn.example.com/branding/global-logo.png",
  "favicon_url": "https://cdn.example.com/branding/favicon.ico",
  "app_name": "Enterprise MCP"
}
```

#### Tenant Branding Secret
**Secret Name**: `tenant-{tenant-id}-branding`

```json
{
  "inherit_global": true,
  "primary_color": "#FF5722",
  "app_name": "Contoso Data Portal",
  "logo_url": "https://cdn.example.com/branding/contoso-logo.png"
}
```

```bash
# Set via Azure CLI
az keyvault secret set \
  --vault-name mcp-server-kv \
  --name "tenant-contoso-branding" \
  --value '{
    "inherit_global": true,
    "primary_color": "#FF5722",
    "app_name": "Contoso Data Portal"
  }'
```

### Method 3: Upload Logo

#### Upload Tenant Logo
```bash
curl -X POST https://api.example.com/api/branding/logo \
  -H "X-Tenant-ID: contoso" \
  -F "file=@./contoso-logo.png"
```

Response:
```json
{
  "logo_url": "https://cdn.example.com/branding/contoso-logo.png",
  "cdn_url": "https://cdn.example.com/branding/contoso-logo.png"
}
```

#### Supported Formats
- **PNG**: Recommended, supports transparency
- **JPG**: Good for photos
- **SVG**: Vector graphics, scalable
- **GIF**: Animated logos (use sparingly)

#### Specifications
- **Max file size**: 5 MB
- **Recommended dimensions**: 
  - Logo: 200x60px (width x height)
  - Favicon: 32x32px
  - Background: 1920x1080px
- **Format**: PNG with transparency preferred

### Method 4: Brand Guide Upload

Upload a complete brand guide (JSON or CSS file) to apply all settings at once.

#### JSON Format
```bash
curl -X POST https://api.example.com/api/branding/brand-guide \
  -H "X-Tenant-ID: contoso" \
  -F "file=@./brand-guide.json"
```

`brand-guide.json`:
```json
{
  "colors": {
    "primary": "#FF5722",
    "secondary": "#FFC107",
    "accent": "#4CAF50",
    "background": "#FAFAFA",
    "text": "#212121"
  },
  "typography": {
    "font_family": "Roboto, sans-serif",
    "heading_font": "Roboto Slab, serif",
    "font_size_base": "16px"
  },
  "assets": {
    "logo": "https://brand.contoso.com/logo.png",
    "favicon": "https://brand.contoso.com/favicon.ico"
  },
  "metadata": {
    "app_name": "Contoso Data Portal",
    "tagline": "Your Data, Your Way"
  }
}
```

#### CSS Format
```bash
curl -X POST https://api.example.com/api/branding/brand-guide \
  -H "X-Tenant-ID: contoso" \
  -F "file=@./brand.css"
```

`brand.css`:
```css
:root {
  --primary-color: #FF5722;
  --secondary-color: #FFC107;
  --accent-color: #4CAF50;
  --background-color: #FAFAFA;
  --text-color: #212121;
  --font-family: 'Roboto', sans-serif;
  --heading-font: 'Roboto Slab', serif;
}
```

## Frontend Integration

### React Context
```tsx
import { useTheme } from './hooks/useTheme';

function MyComponent() {
  const theme = useTheme();
  
  return (
    <div style={{
      backgroundColor: theme.primary_color,
      fontFamily: theme.font_family
    }}>
      <img src={theme.logo_url} alt={theme.app_name} />
      <h1>{theme.app_name}</h1>
    </div>
  );
}
```

### CSS Variables
The frontend automatically injects CSS variables:

```css
/* These variables are set dynamically based on branding */
:root {
  --primary-color: #0078D4;
  --secondary-color: #50E6FF;
  --accent-color: #FFB900;
  --font-family: 'Segoe UI', sans-serif;
}

/* Use in your CSS */
.button {
  background-color: var(--primary-color);
  font-family: var(--font-family);
}
```

### Runtime Theme Updates
```typescript
// Fetch and apply tenant branding
async function applyTenantBranding(tenantId: string) {
  const response = await fetch('/api/branding', {
    headers: { 'X-Tenant-ID': tenantId }
  });
  
  const branding = await response.json();
  
  // Update CSS variables
  document.documentElement.style.setProperty(
    '--primary-color',
    branding.primary_color
  );
  document.documentElement.style.setProperty(
    '--font-family',
    branding.font_family
  );
  
  // Update page title
  document.title = branding.app_name;
  
  // Update favicon
  const favicon = document.querySelector('link[rel="icon"]');
  if (favicon && branding.favicon_url) {
    favicon.setAttribute('href', branding.favicon_url);
  }
}
```

## Examples

### Example 1: Microsoft-style Branding
```json
{
  "primary_color": "#0078D4",
  "secondary_color": "#50E6FF",
  "accent_color": "#FFB900",
  "font_family": "Segoe UI, -apple-system, sans-serif",
  "app_name": "Enterprise MCP",
  "logo_url": "https://cdn.example.com/ms-logo.svg"
}
```

### Example 2: Dark Mode Theme
```json
{
  "primary_color": "#BB86FC",
  "secondary_color": "#03DAC6",
  "accent_color": "#CF6679",
  "background_color": "#121212",
  "text_color": "#FFFFFF",
  "font_family": "Roboto, sans-serif",
  "app_name": "Dark Portal"
}
```

### Example 3: Financial Services
```json
{
  "primary_color": "#003366",
  "secondary_color": "#0066CC",
  "accent_color": "#00CC66",
  "font_family": "Georgia, serif",
  "app_name": "FinTech Analytics",
  "logo_url": "https://cdn.example.com/fintech-logo.png"
}
```

### Example 4: Complete Custom Branding
```json
{
  "inherit_global": false,
  "primary_color": "#E91E63",
  "secondary_color": "#9C27B0",
  "accent_color": "#FF9800",
  "background_color": "#F5F5F5",
  "text_color": "#212121",
  "link_color": "#E91E63",
  "font_family": "Montserrat, sans-serif",
  "heading_font": "Playfair Display, serif",
  "font_size_base": "15px",
  "logo_url": "https://brand.startup.com/logo.svg",
  "logo_dark_url": "https://brand.startup.com/logo-dark.svg",
  "favicon_url": "https://brand.startup.com/favicon.png",
  "app_name": "StartupHub",
  "tagline": "Innovation at Scale",
  "custom_css": ".btn { border-radius: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }"
}
```

## Preview Mode

### Test Branding Before Saving
```bash
# Preview endpoint (doesn't persist)
curl -X POST https://api.example.com/api/branding/preview \
  -H "X-Tenant-ID: contoso" \
  -H "Content-Type: application/json" \
  -d '{
    "primary_color": "#FF5722",
    "app_name": "Test Theme"
  }'
```

Response includes preview URL:
```json
{
  "preview_id": "preview-abc123",
  "preview_url": "https://app.example.com/?preview=preview-abc123",
  "expires_at": "2025-12-04T12:00:00Z"
}
```

## Best Practices

### 1. Color Contrast
- Ensure WCAG AAA compliance (7:1 contrast ratio)
- Test with accessibility tools
- Provide high-contrast alternatives

### 2. Asset Optimization
- **Compress images**: Use tools like TinyPNG
- **Use SVGs** for logos when possible
- **Enable CDN caching**: Set Cache-Control headers
- **Provide retina versions**: @2x and @3x

### 3. Font Loading
- Use `font-display: swap` for custom fonts
- Limit to 2-3 font families
- Host fonts on CDN for performance

### 4. Mobile Responsiveness
- Test logos at multiple sizes
- Ensure touch targets are 44x44px minimum
- Use media queries for mobile overrides

### 5. Brand Consistency
- Document color usage guidelines
- Maintain style guide alongside code
- Version control brand assets

## Troubleshooting

### Issue: Branding not applying
```bash
# Clear cache
curl -X DELETE https://api.example.com/api/branding/cache \
  -H "X-Tenant-ID: contoso"

# Verify branding returned
curl -s https://api.example.com/api/branding \
  -H "X-Tenant-ID: contoso" | jq
```

### Issue: Logo not displaying
```bash
# Check logo URL accessible
curl -I https://cdn.example.com/branding/logo.png

# Verify CORS headers
curl -H "Origin: https://app.example.com" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS https://cdn.example.com/branding/logo.png
```

### Issue: Custom CSS not working
- Verify CSS is valid (use CSS validator)
- Check for CSP (Content Security Policy) violations
- Ensure CSS doesn't conflict with global styles

## Migration Guide

### Migrating from Hardcoded Branding
1. Extract current theme to JSON
2. Upload as global branding
3. Update components to use theme context
4. Test with multiple tenants
5. Document custom overrides

### Bulk Tenant Update
```bash
# Update all tenants with script
for tenant_id in $(az keyvault secret list \
  --vault-name mcp-server-kv \
  --query "[?starts_with(name, 'tenant-')].name" -o tsv | \
  sed 's/tenant-\(.*\)-config/\1/'); do
  
  echo "Updating branding for: $tenant_id"
  
  curl -X PUT https://api.example.com/api/branding \
    -H "X-Tenant-ID: $tenant_id" \
    -H "Content-Type: application/json" \
    -d '{
      "inherit_global": true,
      "primary_color": "#0078D4"
    }'
done
```

## Resources

- **Color Palette Tools**: 
  - [Adobe Color](https://color.adobe.com)
  - [Coolors](https://coolors.co)
  
- **Accessibility Checkers**:
  - [WAVE](https://wave.webaim.org/)
  - [Contrast Checker](https://webaim.org/resources/contrastchecker/)

- **Font Resources**:
  - [Google Fonts](https://fonts.google.com)
  - [Font Squirrel](https://www.fontsquirrel.com)

- **Image Optimization**:
  - [TinyPNG](https://tinypng.com)
  - [Squoosh](https://squoosh.app)
