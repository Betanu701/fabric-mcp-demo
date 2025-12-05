/**
 * Theme context provider for dynamic theming
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface BrandingConfig {
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  font_family?: string;
  logo_url?: string;
  favicon_url?: string;
}

interface ThemeContextType {
  branding: BrandingConfig;
  loadTheme: () => Promise<void>;
}

const defaultBranding: BrandingConfig = {
  primary_color: '#0078D4',
  secondary_color: '#50E6FF',
  accent_color: '#FFB900',
  font_family: 'Segoe UI, -apple-system, BlinkMacSystemFont, sans-serif',
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [branding, _setBranding] = useState<BrandingConfig>(defaultBranding);

  const loadTheme = async () => {
    try {
      // TODO: Fetch branding from API
      // const response = await apiClient.get('/api/admin/branding');
      // setBranding(response.data);
      
      // Apply CSS variables
      applyTheme(branding);
    } catch (error) {
      console.error('Failed to load theme:', error);
    }
  };

  const applyTheme = (config: BrandingConfig) => {
    const root = document.documentElement;
    if (config.primary_color) root.style.setProperty('--color-primary', config.primary_color);
    if (config.secondary_color) root.style.setProperty('--color-secondary', config.secondary_color);
    if (config.accent_color) root.style.setProperty('--color-accent', config.accent_color);
    if (config.font_family) root.style.setProperty('--font-family', config.font_family);
  };

  useEffect(() => {
    loadTheme();
  }, []);

  return (
    <ThemeContext.Provider value={{ branding, loadTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};
