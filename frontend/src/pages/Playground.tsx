import { useContext, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Play, Book, Github, Lock } from 'lucide-react';
import { AppContext } from '../context/AppContext';
import { PromptInput } from '../components/optimization/PromptInput';
import { Badge } from '@/components/ui/badge';

const Playground = () => {
  const { activeMode, setActiveMode, isModeLocked } = useContext(AppContext)!;

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
    <div className="min-h-screen w-full bg-[#0a0c10]">
      {/* Top Navigation */}
      <nav className="w-full px-8 py-4 border-b border-white/[0.08]">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo */}
          <Link
            to="/"
            className="text-white font-bold text-xl tracking-tight hover:text-[#4da3ff] transition-colors duration-200"
          >
            prompt-ops
          </Link>

          {/* Right Nav */}
          <div className="flex items-center gap-2">
            <Link
              to="/playground"
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-white bg-[#0064E0]"
            >
              <Play size={16} />
              <span>Playground</span>
            </Link>

            <Link
              to="/docs"
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium glass-nav-link"
            >
              <Book size={16} />
              <span>Docs</span>
            </Link>

            <a
              href="https://github.com/meta-llama/prompt-ops"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium glass-nav-link"
            >
              <Github size={16} />
              <span>GitHub</span>
            </a>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="px-8 py-12">
        <div className="max-w-5xl mx-auto">
          {/* Mode Toggle - Glassmorphism style */}
          <div className="flex justify-center mb-10">
            <div className="bg-white/[0.08] backdrop-blur-xl p-1.5 rounded-full border border-white/[0.15] relative shadow-[0_8px_32px_rgba(0,0,0,0.12)] ring-1 ring-white/[0.05] ring-inset">
              <div className="grid grid-cols-2 gap-1 relative">
                {/* Sliding indicator - frosted glass style */}
                <div
                  className={`absolute top-0.5 bottom-0.5 rounded-full transition-all duration-300 ease-out bg-white/[0.15] backdrop-blur-md border border-white/[0.2] shadow-[inset_0_1px_1px_rgba(255,255,255,0.1)] ${
                    activeMode === 'migrate'
                      ? 'left-0.5 right-1/2 mr-0.5'
                      : 'left-1/2 right-0 mr-0.5'
                  }`}
                />

                {/* Lock icon when mode is locked */}
                {isModeLocked && (
                  <div className="absolute -top-2 -right-2 bg-white/90 backdrop-blur-sm rounded-full p-1 z-20 shadow-lg">
                    <Lock size={14} className="text-[#0a0c10]" />
                  </div>
                )}

                <button
                  onClick={() => !isModeLocked && setActiveMode('migrate')}
                  disabled={isModeLocked}
                  className={`relative w-full px-8 py-2.5 text-sm font-medium z-10 transition-all duration-200 rounded-full ${
                    activeMode === 'migrate'
                      ? 'text-white'
                      : 'text-white/50 hover:text-white/80'
                  } ${isModeLocked ? 'cursor-not-allowed' : ''}`}
                >
                  Optimize
                </button>

                <button
                  onClick={() => !isModeLocked && setActiveMode('enhance')}
                  disabled={isModeLocked}
                  className={`relative w-full px-8 py-2.5 text-sm font-medium z-10 transition-all duration-200 rounded-full ${
                    activeMode === 'enhance'
                      ? 'text-white'
                      : 'text-white/50 hover:text-white/80'
                  } ${isModeLocked ? 'cursor-not-allowed' : ''}`}
                >
                  <div className="flex items-center justify-center gap-2">
                    Enhance
                    <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-white/[0.1] text-white/60 border border-white/[0.1]">
                      Beta
                    </span>
                  </div>
                </button>
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
