import { useContext } from 'react';
import { Play, Book, Github, Sun, Moon, Monitor } from 'lucide-react';
import { Link } from 'react-router-dom';
import { AppContext } from '../../context/AppContext';
import { useTheme } from '../../context/ThemeContext';

export const Sidebar = () => {
  const { activeMode, setActiveMode } = useContext(AppContext)!;
  const { theme, setTheme } = useTheme();

  const navItems = [
    { id: 'playground', label: 'Playground', icon: Play, path: '/', mode: 'migrate' },
    { id: 'docs', label: 'Docs', icon: Book, path: '/docs', mode: 'docs' },
    { id: 'github', label: 'GitHub', icon: Github, path: 'https://github.com/meta-llama/llama-prompt-ops', external: true },
  ];

  const handleNavClick = (item: any) => {
    if (item.mode) {
      setActiveMode(item.mode);
    }
  };

  return (
    <nav className="relative z-10 w-full px-8 py-6 bg-panel border-b border-border">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Logo/Brand */}
        <div className="flex items-center gap-3">
          <Link
            to="/"
            className="text-foreground font-bold text-2xl tracking-tight hover:text-meta-blue transition-colors duration-200 cursor-pointer"
          >
            llama-prompt-ops
          </Link>
        </div>

        {/* Navigation Links */}
        <div className="flex items-center gap-6">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = (item.mode === 'docs' && activeMode === 'docs') ||
                           (item.mode === 'migrate' && activeMode !== 'docs');

            const navContent = (
              <>
                <Icon size={20} />
                <span>{item.label}</span>
              </>
            );

            if (item.external) {
              return (
                <a
                  key={item.id}
                  href={item.path}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-4 py-2 rounded-lg text-base font-medium transition-all duration-200 text-muted-foreground hover:text-meta-blue hover:bg-muted"
                >
                  {navContent}
                </a>
              );
            }

            if (item.path) {
              return (
                <Link
                  key={item.id}
                  to={item.path}
                  onClick={() => handleNavClick(item)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-base font-medium transition-all duration-200 ${
                    isActive
                      ? 'text-white bg-meta-blue shadow-sm dark:text-meta-gray-900'
                      : 'text-muted-foreground hover:text-meta-blue hover:bg-muted'
                  }`}
                >
                  {navContent}
                </Link>
              );
            }

            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-base font-medium transition-all duration-200 ${
                  isActive
                    ? 'text-white bg-meta-blue shadow-sm dark:text-meta-gray-900'
                    : 'text-muted-foreground hover:text-meta-blue hover:bg-muted'
                }`}
              >
                {navContent}
              </button>
            );
          })}

          {/* Theme Toggle */}
          <div className="flex items-center gap-1 bg-muted p-1 rounded-full border border-border">
            <button
              onClick={() => setTheme('light')}
              className={`p-2 rounded-full transition-colors ${
                theme === 'light' ? 'bg-panel text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
              }`}
              title="Light mode"
            >
              <Sun size={16} />
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={`p-2 rounded-full transition-colors ${
                theme === 'dark' ? 'bg-panel text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
              }`}
              title="Dark mode"
            >
              <Moon size={16} />
            </button>
            <button
              onClick={() => setTheme('system')}
              className={`p-2 rounded-full transition-colors ${
                theme === 'system' ? 'bg-panel text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
              }`}
              title="System preference"
            >
              <Monitor size={16} />
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};
