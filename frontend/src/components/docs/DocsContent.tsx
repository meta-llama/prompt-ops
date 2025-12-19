import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import rehypeSlug from 'rehype-slug';
import { Copy, Check, FileText } from 'lucide-react';
import type { DocItem } from '@/types';
import { apiUrl } from '@/lib/config';
import 'highlight.js/styles/github-dark.css';

interface DocsContentProps {
  doc: DocItem;
}

export const DocsContent: React.FC<DocsContentProps> = ({ doc }) => {
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);

  useEffect(() => {
    const fetchContent = async () => {
      setLoading(true);
      setError(null);

      try {
        // Fetch content from the backend docs endpoint
        const response = await fetch(apiUrl(`/docs/${doc.path}`));
        if (!response.ok) {
          throw new Error(`Failed to load ${doc.title}`);
        }
        const text = await response.text();
        setContent(text);
      } catch (err) {
        // Fallback content for demo purposes when files aren't available
        const fallbackContent = `# ${doc.title}

This is a demonstration of the documentation system. The actual file \`${doc.path}\` could not be loaded.

## About This Document

${doc.description || 'This document provides comprehensive information about the topic.'}

## Features

- **Markdown Rendering**: Full support for GitHub Flavored Markdown
- **Syntax Highlighting**: Code blocks with syntax highlighting
- **Responsive Design**: Works great on all screen sizes
- **Search Functionality**: Find what you need quickly

## Code Example

\`\`\`python
# Example code block
from prompt_ops import optimize

async def optimize_prompt(prompt: str, config: dict):
    response = await optimize(
        prompt=prompt,
        metrics=config.get("metrics", ["accuracy"]),
        dataset=config.get("dataset"),
    )
    return response.optimized_prompt
\`\`\`

## Getting Started

To get started with ${doc.title.toLowerCase()}, follow these steps:

1. Review the configuration options
2. Prepare your dataset
3. Run the optimization process
4. Analyze the results

---

*This is a demo version. In a real implementation, this content would be loaded from \`docs/${doc.path}\`.*`;

        setContent(fallbackContent);
        setError(`Could not load ${doc.path}. Showing demo content instead.`);
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [doc]);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  if (loading) {
    return (
      <div className="h-full glass-panel p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-white/[0.1] rounded-lg w-3/4"></div>
          <div className="h-4 bg-white/[0.08] rounded-lg w-1/2"></div>
          <div className="space-y-2 mt-8">
            <div className="h-4 bg-white/[0.06] rounded-lg"></div>
            <div className="h-4 bg-white/[0.06] rounded-lg w-5/6"></div>
            <div className="h-4 bg-white/[0.06] rounded-lg w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full glass-panel overflow-hidden flex flex-col animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-white/[0.08]">
        <div className="flex items-center gap-3">
          {doc.icon && (
            <div className="w-10 h-10 rounded-xl bg-white/[0.05] border border-white/[0.1] flex items-center justify-center">
              <doc.icon className="w-5 h-5 text-[#4da3ff]" />
            </div>
          )}
          <div>
            <h1 className="text-xl font-semibold text-white">
              {doc.title}
            </h1>
            <p className="text-sm text-white/50">
              {doc.category} • {doc.path}
            </p>
          </div>
        </div>

        <button
          onClick={handleCopy}
          className="p-2 rounded-lg hover:bg-white/[0.08] transition-colors"
          title="Copy content"
        >
          {copySuccess ? (
            <Check className="w-4 h-4 text-emerald-400" />
          ) : (
            <Copy className="w-4 h-4 text-white/50 hover:text-white" />
          )}
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mx-6 mt-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-200 text-sm">
          {error}
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="prose-dark max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight, rehypeSlug]}
            components={{
              h1: ({node, ...props}) => (
                <h1 className="text-3xl font-semibold text-white mb-4 pb-3 border-b border-white/[0.1]" {...props} />
              ),
              h2: ({node, ...props}) => (
                <h2 className="text-2xl font-semibold text-white mb-3 mt-10" {...props} />
              ),
              h3: ({node, ...props}) => (
                <h3 className="text-xl font-semibold text-white mb-2 mt-8" {...props} />
              ),
              h4: ({node, ...props}) => (
                <h4 className="text-lg font-medium text-white mb-2 mt-6" {...props} />
              ),
              p: ({node, ...props}) => (
                <p className="text-white/70 mb-4 leading-relaxed" {...props} />
              ),
              a: ({node, ...props}) => (
                <a
                  className="text-[#4da3ff] hover:text-[#7dbdff] underline decoration-[#4da3ff]/30 hover:decoration-[#4da3ff] transition-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                  {...props}
                />
              ),
              code: ({node, className, children, ...props}) => {
                const match = /language-(\w+)/.exec(className || '');
                return match ? (
                  <code className={`${className} text-sm`} {...props}>
                    {children}
                  </code>
                ) : (
                  <code className="bg-white/[0.1] text-[#a5d6ff] px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                    {children}
                  </code>
                );
              },
              pre: ({node, ...props}) => (
                <pre className="bg-[#050608] border border-white/[0.08] rounded-xl p-4 overflow-x-auto mb-4 mt-2" {...props} />
              ),
              blockquote: ({node, ...props}) => (
                <blockquote className="border-l-2 border-[#4da3ff]/50 pl-4 italic text-white/60 my-4" {...props} />
              ),
              ul: ({node, ...props}) => (
                <ul className="list-disc list-outside ml-5 mb-4 text-white/70 space-y-1.5" {...props} />
              ),
              ol: ({node, ...props}) => (
                <ol className="list-decimal list-outside ml-5 mb-4 text-white/70 space-y-1.5" {...props} />
              ),
              li: ({node, ...props}) => (
                <li className="leading-relaxed" {...props} />
              ),
              table: ({node, ...props}) => (
                <div className="overflow-x-auto mb-4 rounded-xl border border-white/[0.1]">
                  <table className="min-w-full" {...props} />
                </div>
              ),
              th: ({node, ...props}) => (
                <th className="border-b border-white/[0.1] px-4 py-3 bg-white/[0.05] text-white font-medium text-left text-sm" {...props} />
              ),
              td: ({node, ...props}) => (
                <td className="border-b border-white/[0.05] px-4 py-3 text-white/70 text-sm" {...props} />
              ),
              hr: ({node, ...props}) => (
                <hr className="border-white/[0.1] my-8" {...props} />
              ),
              strong: ({node, ...props}) => (
                <strong className="text-white font-semibold" {...props} />
              ),
              em: ({node, ...props}) => (
                <em className="text-white/80 italic" {...props} />
              ),
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
};
