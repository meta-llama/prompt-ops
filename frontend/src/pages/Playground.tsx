import { useContext, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Play, Book, Github, Sun, Moon, Monitor, Lock } from 'lucide-react';
import { AppContext } from '../context/AppContext';
import { useTheme } from '../context/ThemeContext';
import { PromptInput } from '../components/optimization/PromptInput';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const Playground = () => {
  const { activeMode, setActiveMode, isModeLocked } = useContext(AppContext)!;
  const { theme, setTheme } = useTheme();

  // Set page title and meta description
  useEffect(() => {
    document.title = 'Playground | prompt-ops';
    
    let metaDescription = document.querySelector('meta[name="description"]');
    if (!metaDescription) {
      metaDescription = document.createElement('meta');
      metaDescription.setAttribute('name', 'description');
      document.head.appendChild(metaDescription);
    }
    metaDescription.setAttribute('content', 'Try prompt-ops playground to optimize and enhance your LLM prompts with AI-powered strategies.');

    return () => {
      document.title = 'prompt-ops';
    };
  }, []);

  return (
    <div className="min-h-screen w-full bg-background">
      {/* Top Navigation */}
      <nav className="w-full px-8 py-6 bg-panel border-b border-border">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo */}
          <Link
            to="/"
            className="text-foreground font-bold text-2xl tracking-tight hover:text-meta-blue transition-colors duration-200"
          >
            prompt-ops
          </Link>

          {/* Right Nav */}
          <div className="flex items-center gap-4">
            <Link
              to="/playground"
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-base font-medium text-white bg-meta-blue shadow-sm"
            >
              <Play size={18} />
              <span>Playground</span>
            </Link>

            <Link
              to="/docs"
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-base font-medium text-muted-foreground hover:text-meta-blue hover:bg-muted transition-all duration-200"
            >
              <Book size={18} />
              <span>Docs</span>
            </Link>

            <a
              href="https://github.com/meta-llama/prompt-ops"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-base font-medium text-muted-foreground hover:text-meta-blue hover:bg-muted transition-all duration-200"
            >
              <Github size={18} />
              <span>GitHub</span>
            </a>

            {/* Theme Toggle */}
            <div className="flex items-center gap-1 bg-muted p-1 rounded-full border border-border">
              <button
                onClick={() => setTheme('light')}
                className={`p-2 rounded-full transition-colors ${
                  theme === 'light'
                    ? 'bg-panel text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
                title="Light mode"
              >
                <Sun size={16} />
              </button>
              <button
                onClick={() => setTheme('dark')}
                className={`p-2 rounded-full transition-colors ${
                  theme === 'dark'
                    ? 'bg-panel text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
                title="Dark mode"
              >
                <Moon size={16} />
              </button>
              <button
                onClick={() => setTheme('system')}
                className={`p-2 rounded-full transition-colors ${
                  theme === 'system'
                    ? 'bg-panel text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
                title="System preference"
              >
                <Monitor size={16} />
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="px-8 py-12">
        <div className="max-w-5xl mx-auto">
          {/* Hero Section */}
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-semibold text-foreground mb-4 tracking-tight">
              Optimize your prompt
            </h1>
            <p className="text-lg text-muted-foreground">
              Use AI-powered strategies to enhance your prompts for better results
            </p>
          </div>

          {/* Mode Toggle */}
          <div className="flex justify-center mb-10">
            <div className="bg-muted p-1 rounded-full border border-border relative">
              <div className="grid grid-cols-2 gap-1 relative">
                {/* Sliding indicator */}
                <div
                  className={`absolute top-0 bottom-0 rounded-full transition-all duration-300 ease-in-out bg-meta-blue ${
                    activeMode === 'migrate'
                      ? 'left-0 right-1/2 mr-0.5'
                      : 'left-1/2 right-0 ml-0.5'
                  }`}
                />

                {/* Lock icon when mode is locked */}
                {isModeLocked && (
                  <div className="absolute -top-2 -right-2 bg-foreground rounded-full p-1 z-20">
                    <Lock size={14} className="text-background" />
                  </div>
                )}

                <Button
                  onClick={() => !isModeLocked && setActiveMode('migrate')}
                  variant="ghost"
                  disabled={isModeLocked}
                  className={`relative w-full px-8 py-3 text-lg font-medium z-10 transition-colors rounded-full hover:bg-transparent ${
                    activeMode === 'migrate'
                      ? 'text-white hover:text-white dark:text-meta-gray-900 dark:hover:text-meta-gray-900'
                      : 'text-foreground hover:text-foreground'
                  } ${isModeLocked ? 'cursor-not-allowed' : ''}`}
                >
                  Optimize
                </Button>

                <Button
                  onClick={() => !isModeLocked && setActiveMode('enhance')}
                  variant="ghost"
                  disabled={isModeLocked}
                  className={`relative w-full px-8 py-3 text-lg font-medium z-10 transition-colors rounded-full hover:bg-transparent ${
                    activeMode === 'enhance'
                      ? 'text-white hover:text-white dark:text-meta-gray-900 dark:hover:text-meta-gray-900'
                      : 'text-foreground hover:text-foreground'
                  } ${isModeLocked ? 'cursor-not-allowed' : ''}`}
                >
                  <div className="flex items-center justify-center gap-2">
                    Enhance
                    <Badge
                      variant="warning"
                      className="bg-meta-orange text-white border-meta-orange"
                    >
                      Experimental
                    </Badge>
                  </div>
                </Button>
              </div>
            </div>
          </div>

          {/* Prompt Input */}
          <div className="mb-8">
            <PromptInput />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Playground;
