import React, { useContext } from 'react';
import { AppContext } from '../../context/AppContext';
import { PromptInput } from '../optimization/PromptInput';
import { DocsTab } from '../docs/DocsTab';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Lock } from 'lucide-react';

export const MainContent = () => {
  const { activeMode, setActiveMode, isModeLocked } = useContext(AppContext)!;

  // If in docs mode, show only the docs content
  if (activeMode === 'docs') {
    return (
      <div className="relative z-10 flex-1 px-8 py-8">
        <DocsTab />
      </div>
    );
  }

  return (
    <div className="relative z-10 flex-1 px-8">
      <div className="max-w-5xl mx-auto">
        {/* Hero Section - Centered */}
        <div className="text-center mb-16 pt-12">
          <h1 className="text-6xl md:text-7xl font-black text-facebook-text mb-8 tracking-tight leading-none">
            Optimize your
            <br />
            <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
              prompt
            </span>
          </h1>
        </div>

        {/* Mode Toggle - Only Migrate and Enhance */}
        <div className="flex justify-center mb-8">
          <div className="bg-white p-1 rounded-xl shadow-lg border border-facebook-border relative">
            {/* Container using CSS Grid for equal button widths */}
            <div className="grid grid-cols-2 gap-1 relative">
              {/* Sliding indicator with Facebook blue gradient */}
              <div
                className={`absolute top-0 bottom-0 rounded-lg transition-all duration-300 ease-in-out ${
                  activeMode === 'migrate'
                    ? 'left-0 right-1/2 mr-0.5'
                    : 'left-1/2 right-0 ml-0.5'
                }`}
                style={{
                  background: 'linear-gradient(135deg, hsl(var(--facebook-blue)), hsl(var(--facebook-blue-light)))'
                }}
              />

              {/* Lock icon when mode is locked */}
              {isModeLocked && (
                <div className="absolute -top-2 -right-2 bg-facebook-text/80 rounded-full p-1 shadow-lg z-20">
                  <Lock size={14} className="text-white" />
                </div>
              )}

              <Button
                onClick={() => !isModeLocked && setActiveMode('migrate')}
                variant="ghost"
                disabled={isModeLocked}
                className={`relative w-full px-8 py-3 text-lg font-medium z-10 transition-all duration-300 rounded-lg hover:bg-transparent ${
                  activeMode === 'migrate'
                    ? 'text-white hover:text-white'
                    : 'text-facebook-text hover:text-facebook-text'
                } ${isModeLocked ? 'cursor-not-allowed' : ''}`}
              >
                Migrate
              </Button>

              <Button
                onClick={() => !isModeLocked && setActiveMode('enhance')}
                variant="ghost"
                disabled={isModeLocked}
                className={`relative w-full px-8 py-3 text-lg font-medium z-10 transition-all duration-300 rounded-lg hover:bg-transparent ${
                  activeMode === 'enhance'
                    ? 'text-white hover:text-white'
                    : 'text-facebook-text hover:text-facebook-text'
                } ${isModeLocked ? 'cursor-not-allowed' : ''}`}
              >
                <div className="flex items-center justify-center gap-2">
                  Enhance
                  <Badge
                    variant="secondary"
                    className="text-xs px-2 py-0.5 bg-orange-100 text-orange-600 border-orange-200 hover:bg-orange-100"
                  >
                    Experimental
                  </Badge>
                </div>
              </Button>
            </div>
          </div>
        </div>

        {/* Prompt Input - Elevated and Centered */}
        <div className="mb-8">
          <PromptInput />
        </div>
      </div>
    </div>
  );
};
