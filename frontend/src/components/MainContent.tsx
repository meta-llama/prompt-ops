import React, { useContext } from 'react';
import { AppContext } from '../context/AppContext';
import { PromptInput } from './PromptInput';
import { ConfigurationPanel } from './ConfigurationPanel';
import { Button } from '@/components/ui/button';
import { Lock } from 'lucide-react';

export const MainContent = () => {
  const { activeMode, setActiveMode, isModeLocked } = useContext(AppContext)!; // 'enhance' or 'migrate'
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

          {/* <p className="text-xl text-facebook-text/70 mb-12 max-w-2xl mx-auto leading-relaxed">
            Create apps and websites by chatting with AI
          </p> */}

          {/* Action Buttons */}

        </div>
        <div className="flex justify-center mb-8">
          <div className="bg-white p-1 rounded-xl inline-flex shadow-lg border border-facebook-border relative">
            {/* Sliding indicator with Facebook blue gradient */}
            <div
              className={`absolute top-1 bottom-1 rounded-lg transition-all duration-300 ease-in-out ${activeMode === 'enhance' ? 'left-1 right-[calc(50%+1px)]' : 'left-[calc(50%+1px)] right-1'}`}
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
              onClick={() => !isModeLocked && setActiveMode('enhance')}
              variant="ghost"
              disabled={isModeLocked}
              className={`relative min-w-[140px] px-8 py-3 text-lg font-medium z-10 transition-all duration-300 rounded-lg hover:bg-transparent ${
                activeMode === 'enhance'
                  ? 'text-white hover:text-white'
                  : 'text-facebook-text hover:text-facebook-text'
              } ${isModeLocked ? 'cursor-not-allowed' : ''}`}
            >
              Enhance
            </Button>
            <Button
              onClick={() => !isModeLocked && setActiveMode('migrate')}
              variant="ghost"
              disabled={isModeLocked}
              className={`relative min-w-[140px] px-8 py-3 text-lg font-medium z-10 transition-all duration-300 rounded-lg hover:bg-transparent ${
                activeMode === 'migrate'
                  ? 'text-white hover:text-white'
                  : 'text-facebook-text hover:text-facebook-text'
              } ${isModeLocked ? 'cursor-not-allowed' : ''}`}
            >
              Migrate
            </Button>
          </div>
        </div>

        {/* Prompt Input - Elevated and Centered */}
        <div className="mb-8">
          <PromptInput />
        </div>

        {/* Configuration Panel - Floating Card (only shown when migrate is selected) */}
        {activeMode === 'migrate' && <ConfigurationPanel />}
      </div>
    </div>
  );
};
