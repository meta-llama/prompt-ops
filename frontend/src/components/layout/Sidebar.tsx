import { useContext } from 'react';
import { Play, Book, Github } from 'lucide-react';
import { Link } from 'react-router-dom';
import { AppContext } from '../../context/AppContext';

export const Sidebar = () => {
  const { activeMode, setActiveMode } = useContext(AppContext)!;

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
    <nav className="relative z-10 w-full px-8 py-6 bg-white/80 backdrop-blur-sm border-b border-facebook-border">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Logo/Brand */}
        <div className="flex items-center gap-3">
          <Link
            to="/"
            className="text-facebook-text font-bold text-2xl tracking-tight hover:text-facebook-blue transition-colors duration-200 cursor-pointer"
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
                  className="flex items-center gap-2 px-4 py-2 rounded-lg text-base font-medium transition-all duration-200 text-facebook-text/70 hover:text-facebook-blue hover:bg-facebook-gray/50"
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
                      ? 'text-white bg-facebook-blue shadow-sm'
                      : 'text-facebook-text/70 hover:text-facebook-blue hover:bg-facebook-gray/50'
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
                    ? 'text-white bg-facebook-blue shadow-sm'
                    : 'text-facebook-text/70 hover:text-facebook-blue hover:bg-facebook-gray/50'
                }`}
              >
                {navContent}
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
