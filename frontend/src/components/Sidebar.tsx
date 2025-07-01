import React, { useState } from 'react';
import { Heart, Play, FileText, Book, Github } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Sidebar = () => {
  // Set 'playground' as default active tab since it's the homepage
  const [activeTab, setActiveTab] = useState('playground');

  const navItems = [
    { id: 'playground', label: 'Playground', icon: Play, path: '/' },
    // { id: 'logging', label: 'Logging', icon: FileText },
    // { id: 'docs', label: 'Docs', icon: Book },
    { id: 'github', label: 'GitHub', icon: Github, path: 'https://github.com/meta-llama/llama-prompt-ops', external: true },
  ];

  return (
    <nav className="relative z-10 w-full px-8 py-6 bg-white/80 backdrop-blur-sm border-b border-facebook-border">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Logo/Brand */}
        <div className="flex items-center gap-3">
          <Heart className="text-facebook-blue fill-facebook-blue" size={32} />
          <span className="text-facebook-text font-bold text-2xl tracking-tight">llama-prompt-ops</span>
        </div>

        {/* Navigation Links */}
        <div className="flex items-center gap-6">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

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

            return (
              <Link
                key={item.id}
                to={item.path}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-base font-medium transition-all duration-200 ${
                  isActive
                    ? 'text-white bg-facebook-blue shadow-sm'
                    : 'text-facebook-text/70 hover:text-facebook-blue hover:bg-facebook-gray/50'
                }`}
              >
                {navContent}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
