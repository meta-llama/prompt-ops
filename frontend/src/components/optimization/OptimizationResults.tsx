import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface OptimizationResultsProps {
  originalPrompt: string;
  optimizedPrompt: string;
  onCopy: () => void;
}

export const OptimizationResults: React.FC<OptimizationResultsProps> = ({
  originalPrompt,
  optimizedPrompt,
  onCopy
}) => {
  const [activeTab, setActiveTab] = useState<'before' | 'after'>('after');
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    onCopy();
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white/90 backdrop-blur-xl rounded-2xl p-8 shadow-xl border border-facebook-border">
      <h2 className="text-4xl font-black text-facebook-text text-center mb-8">Results</h2>

      {/* Toggle between before and after */}
      <div className="flex justify-center mb-8">
        <div className="bg-facebook-gray p-1 rounded-xl inline-flex shadow-md border border-facebook-border relative">
          {/* Sliding indicator with Facebook blue */}
          <div
            className={`absolute top-1 bottom-1 rounded-lg transition-all duration-300 ease-in-out ${
              activeTab === 'before' ? 'left-1 right-[calc(50%+1px)]' : 'left-[calc(50%+1px)] right-1'
            }`}
            style={{
              background: 'linear-gradient(135deg, hsl(var(--facebook-blue)), hsl(var(--facebook-blue-light)))'
            }}
          />

          <button
            onClick={() => setActiveTab('before')}
            className={`relative min-w-[100px] px-6 py-2 text-sm font-medium z-10 transition-all duration-300 rounded-lg hover:bg-transparent ${
              activeTab === 'before'
                ? 'text-white hover:text-white'
                : 'text-facebook-text hover:text-facebook-text'
            }`}
          >
            Before
          </button>
          <button
            onClick={() => setActiveTab('after')}
            className={`relative min-w-[100px] px-6 py-2 text-sm font-medium z-10 transition-all duration-300 rounded-lg hover:bg-transparent ${
              activeTab === 'after'
                ? 'text-white hover:text-white'
                : 'text-facebook-text hover:text-facebook-text'
            }`}
          >
            After
          </button>
        </div>
      </div>

      {/* Content container */}
      <div className="border border-facebook-border bg-white/60 backdrop-blur-sm rounded-xl p-6 mb-8 h-[70vh] overflow-y-auto relative">
        {/* Before content */}
        <textarea
          readOnly
          value={originalPrompt}
          className={`whitespace-pre-wrap text-facebook-text text-lg leading-relaxed transition-opacity duration-300 absolute inset-6 bg-transparent border-none outline-none resize-none w-[calc(100%-3rem)] h-[calc(100%-3rem)] ${
            activeTab === 'before' ? 'opacity-100 z-10' : 'opacity-0 z-0 pointer-events-none'
          }`}
        />
        {/* After content */}
        <textarea
          readOnly
          value={optimizedPrompt}
          className={`whitespace-pre-wrap text-facebook-text text-lg leading-relaxed transition-opacity duration-300 absolute inset-6 bg-transparent border-none outline-none resize-none w-[calc(100%-3rem)] h-[calc(100%-3rem)] ${
            activeTab === 'after' ? 'opacity-100 z-10' : 'opacity-0 z-0 pointer-events-none'
          }`}
        />
      </div>

      {/* Copy button */}
      <div className="flex justify-center">
        <button
          onClick={handleCopy}
          className="bg-facebook-blue hover:bg-facebook-blue-dark text-white px-8 py-3 rounded-xl font-medium transition-all duration-300 flex items-center gap-2 shadow-lg hover:shadow-facebook-blue/25 transform hover:scale-105"
        >
          {copied ? <Check size={18} /> : <Copy size={18} />}
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
    </div>
  );
};
