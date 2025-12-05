/**
 * Tenant context provider for managing tenant state
 */
import React, { createContext, useContext, useState, ReactNode } from 'react';

interface TenantContextType {
  tenantId: string;
  setTenantId: (id: string) => void;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export const TenantProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [tenantId, setTenantIdState] = useState<string>(() => {
    return localStorage.getItem('tenant_id') || 'default';
  });

  const setTenantId = (id: string) => {
    setTenantIdState(id);
    localStorage.setItem('tenant_id', id);
  };

  return (
    <TenantContext.Provider value={{ tenantId, setTenantId }}>
      {children}
    </TenantContext.Provider>
  );
};

export const useTenant = (): TenantContextType => {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant must be used within TenantProvider');
  }
  return context;
};
