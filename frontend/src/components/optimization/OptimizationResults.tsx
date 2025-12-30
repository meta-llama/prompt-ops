import React, { useState, useMemo } from 'react';
import { Copy, Check, Columns, LayoutList } from 'lucide-react';
import { diffWords } from 'diff';
import { Button } from '@/components/ui/button';

interface OptimizationResultsProps {
  originalPrompt: string;
  optimizedPrompt: string;
  onCopy: () => void;
}

// Renders text with diff highlighting
const DiffView: React.FC<{
  original: string;
  optimized: string;
  showOriginal: boolean;
}> = ({ original, optimized, showOriginal }) => {
  const diffResult = useMemo(() => diffWords(original, optimized), [original, optimized]);

  return (
    <div className="whitespace-pre-wrap text-white text-base leading-relaxed font-mono">
      {diffResult.map((part, index) => {
        // For the "original" side, show removed parts highlighted, skip added parts
        if (showOriginal) {
          if (part.added) return null;
          if (part.removed) {
            return (
              <span
                key={index}
                className="bg-red-900/40 text-red-300 px-0.5 rounded line-through decoration-red-400"
              >
                {part.value}
              </span>
            );
          }
          return <span key={index}>{part.value}</span>;
        }

        // For the "optimized" side, show added parts highlighted, skip removed parts
        if (part.removed) return null;
        if (part.added) {
          return (
            <span
              key={index}
              className="bg-emerald-900/40 text-emerald-300 px-0.5 rounded"
            >
              {part.value}
            </span>
          );
        }
        return <span key={index}>{part.value}</span>;
      })}
    </div>
  );
};

// Unified diff view showing all changes inline
const UnifiedDiffView: React.FC<{ original: string; optimized: string }> = ({
  original,
  optimized
}) => {
  const diffResult = useMemo(() => diffWords(original, optimized), [original, optimized]);

  return (
    <div className="whitespace-pre-wrap text-white text-base leading-relaxed font-mono">
      {diffResult.map((part, index) => {
        if (part.removed) {
          return (
            <span
              key={index}
              className="bg-red-900/40 text-red-300 px-0.5 rounded line-through decoration-red-400"
            >
              {part.value}
            </span>
          );
        }
        if (part.added) {
          return (
            <span
              key={index}
              className="bg-emerald-900/40 text-emerald-300 px-0.5 rounded"
            >
              {part.value}
            </span>
          );
        }
        return <span key={index}>{part.value}</span>;
      })}
    </div>
  );
};

export const OptimizationResults: React.FC<OptimizationResultsProps> = ({
  originalPrompt,
  optimizedPrompt,
  onCopy
}) => {
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<'split' | 'unified'>('split');

  const handleCopy = () => {
    onCopy();
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Calculate diff stats
  const stats = useMemo(() => {
    const diff = diffWords(originalPrompt, optimizedPrompt);
    let added = 0;
    let removed = 0;
    diff.forEach(part => {
      if (part.added) added += part.value.split(/\s+/).filter(Boolean).length;
      if (part.removed) removed += part.value.split(/\s+/).filter(Boolean).length;
    });
    return { added, removed };
  }, [originalPrompt, optimizedPrompt]);

  return (
    <div className="glass-panel-solid rounded-3xl p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-normal text-white">Results</h2>

        {/* View mode toggle and stats */}
        <div className="flex items-center gap-4">
          {/* Diff stats */}
          <div className="flex items-center gap-3 text-sm">
            <span className="flex items-center gap-1.5 text-emerald-300 bg-emerald-900/30 px-2.5 py-1 rounded-md border border-emerald-800">
              <span className="font-semibold">+{stats.added}</span>
              <span className="text-emerald-400">words</span>
            </span>
            <span className="flex items-center gap-1.5 text-red-300 bg-red-900/30 px-2.5 py-1 rounded-md border border-red-800">
              <span className="font-semibold">-{stats.removed}</span>
              <span className="text-red-400">words</span>
            </span>
          </div>

          {/* View toggle */}
          <div className="bg-white/[0.05] p-1 rounded-full inline-flex border border-white/[0.1]">
            <button
              onClick={() => setViewMode('split')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-full transition-colors ${
                viewMode === 'split'
                  ? 'bg-white/[0.1] text-white shadow-sm'
                  : 'text-white/60 hover:text-white'
              }`}
              title="Side by side"
            >
              <Columns size={16} />
              Split
            </button>
            <button
              onClick={() => setViewMode('unified')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-full transition-colors ${
                viewMode === 'unified'
                  ? 'bg-white/[0.1] text-white shadow-sm'
                  : 'text-white/60 hover:text-white'
              }`}
              title="Unified view"
            >
              <LayoutList size={16} />
              Unified
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {viewMode === 'split' ? (
        /* Side-by-side view */
        <div className="grid grid-cols-2 gap-4 mb-8">
          {/* Before panel */}
          <div className="flex flex-col">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-3 h-3 rounded-full bg-red-400"></div>
              <span className="text-sm font-semibold text-white/60 uppercase tracking-wide">
                Original
              </span>
            </div>
            <div className="flex-1 border border-white/[0.1] bg-white/[0.03] rounded-2xl p-5 h-[60vh] overflow-y-auto">
              <DiffView
                original={originalPrompt}
                optimized={optimizedPrompt}
                showOriginal={true}
              />
            </div>
          </div>

          {/* After panel */}
          <div className="flex flex-col">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-3 h-3 rounded-full bg-emerald-400"></div>
              <span className="text-sm font-semibold text-white/60 uppercase tracking-wide">
                Enhanced
              </span>
            </div>
            <div className="flex-1 border border-white/[0.1] bg-white/[0.03] rounded-2xl p-5 h-[60vh] overflow-y-auto">
              <DiffView
                original={originalPrompt}
                optimized={optimizedPrompt}
                showOriginal={false}
              />
            </div>
          </div>
        </div>
      ) : (
        /* Unified view */
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-sm font-semibold text-white/60 uppercase tracking-wide">
              All Changes
            </span>
            <span className="text-xs text-white/40">
              (strikethrough = removed, highlighted = added)
            </span>
          </div>
          <div className="border border-white/[0.1] bg-white/[0.03] rounded-2xl p-5 h-[60vh] overflow-y-auto">
            <UnifiedDiffView original={originalPrompt} optimized={optimizedPrompt} />
          </div>
        </div>
      )}

      {/* Legend and Copy button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm text-white/60">
          <div className="flex items-center gap-2">
            <span className="inline-block w-4 h-4 bg-red-900/40 border border-red-800 rounded"></span>
            <span>Removed</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-4 h-4 bg-emerald-900/40 border border-emerald-800 rounded"></span>
            <span>Added</span>
          </div>
        </div>

        <Button
          onClick={handleCopy}
          variant="filled"
          size="medium"
        >
          {copied ? 'Copied!' : 'Copy Enhanced Prompt'}
          {copied ? <Check /> : <Copy />}
        </Button>
      </div>
    </div>
  );
};
