import { Link, useLocation } from 'react-router-dom';
import { Play, Book, Github } from 'lucide-react';
import { DocsTab } from '../components/docs/DocsTab';

const Docs = () => {
  const location = useLocation();
  const isDocsActive = location.pathname.startsWith('/docs');

  return (
    <div className="fixed inset-0 w-screen h-screen overflow-hidden bg-[#0a0c10]">
      {/* Top Navigation - Slim */}
      <nav className="relative z-20 px-8 py-4 border-b border-white/[0.08]">
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
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium glass-nav-link"
            >
              <Play size={16} />
              <span>Playground</span>
            </Link>

            <Link
              to="/docs"
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                isDocsActive
                  ? 'text-white bg-[#0064E0]'
                  : 'glass-nav-link'
              }`}
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

      {/* Main Content Area */}
      <div className="h-[calc(100vh-73px)] overflow-hidden">
        <DocsTab />
      </div>
    </div>
  );
};

export default Docs;
