import React, { createContext, useState, ReactNode } from 'react';

interface AppContextType {
  activeMode: string;
  setActiveMode: (mode: string) => void;
  isModeLocked: boolean;
  setIsModeLocked: (locked: boolean) => void;
}

export const AppContext = createContext<AppContextType | undefined>(undefined);

interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [activeMode, setActiveMode] = useState('enhance');
  const [isModeLocked, setIsModeLocked] = useState(false);

  return (
    <AppContext.Provider value={{
      activeMode,
      setActiveMode,
      isModeLocked,
      setIsModeLocked
    }}>
      {children}
    </AppContext.Provider>
  );
};
