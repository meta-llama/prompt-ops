import { createContext, useContext, useEffect, ReactNode } from 'react';

// Dark-only theme - no light mode support
type Theme = 'dark';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: 'dark';
}

const ThemeContext = createContext<ThemeContextType | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  // Always dark mode
  const theme: Theme = 'dark';
  const resolvedTheme: 'dark' = 'dark';

  // Always apply dark class on mount
  useEffect(() => {
    const root = document.documentElement;
    root.classList.add('dark');
  }, []);

  // setTheme is a no-op in dark-only mode
  const setTheme = () => {};

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
