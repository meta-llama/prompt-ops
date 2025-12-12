import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import rehypeSlug from 'rehype-slug';
import { Copy, Check, ExternalLink, Clock, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DocItem } from './DocsTab';
import { apiUrl } from '@/lib/config';
import 'highlight.js/styles/github.css';

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

\`\`\`javascript
// Example code block
const optimizePrompt = async (prompt, config) => {
  const response = await fetch('/api/optimize', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt, config }),
  });

  return response.json();
};
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
      <div className="h-full bg-white rounded-3xl border border-meta-gray-300/50 p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-meta-gray-100/20 rounded-lg w-3/4"></div>
          <div className="h-4 bg-meta-gray-100/20 rounded-lg w-1/2"></div>
          <div className="space-y-2">
            <div className="h-4 bg-meta-gray-100/20 rounded-lg"></div>
            <div className="h-4 bg-meta-gray-100/20 rounded-lg w-5/6"></div>
            <div className="h-4 bg-meta-gray-100/20 rounded-lg w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full bg-white rounded-3xl border border-meta-gray-300/50 p-8">
        <div className="text-center py-12">
          <FileText className="w-16 h-16 text-meta-gray/20 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-meta-gray mb-2">
            Content Not Available
          </h3>
          <p className="text-meta-gray/70 mb-4">
            {error}
          </p>
          <p className="text-sm text-meta-gray/50">
            This is a demo version. In a real implementation, the content would be loaded from the actual markdown files.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-white rounded-3xl border border-meta-gray-300/50 overflow-hidden flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-meta-gray-300">
        <div className="flex items-center gap-3">
          {doc.icon && <doc.icon className="w-6 h-6 text-meta-blue" />}
          <div>
            <h1 className="text-2xl font-bold text-meta-gray">
              {doc.title}
            </h1>
            <p className="text-sm text-meta-gray/60">
              {doc.category} • {doc.path}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={handleCopy}
            variant="ghost"
            size="sm"
            className="hover:bg-meta-gray-100/20"
          >
            {copySuccess ? (
              <Check className="w-4 h-4 text-meta-teal" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="prose prose-lg max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight, rehypeSlug]}
            components={{
              // Custom components for better styling
              h1: ({node, ...props}) => (
                <h1 className="text-3xl font-bold text-meta-gray mb-4 pb-2 border-b border-meta-gray-300" {...props} />
              ),
              h2: ({node, ...props}) => (
                <h2 className="text-2xl font-bold text-meta-gray mb-3 mt-8" {...props} />
              ),
              h3: ({node, ...props}) => (
                <h3 className="text-xl font-bold text-meta-gray mb-2 mt-6" {...props} />
              ),
              p: ({node, ...props}) => (
                <p className="text-meta-gray/80 mb-4 leading-relaxed" {...props} />
              ),
              a: ({node, ...props}) => (
                <a
                  className="text-meta-blue hover:text-meta-blue-800 underline decoration-meta-blue/30 hover:decoration-meta-blue transition-colors"
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
                  <code className="bg-meta-gray-100/20 text-meta-gray px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                    {children}
                  </code>
                );
              },
              pre: ({node, ...props}) => (
                <pre className="bg-meta-gray-100/10 border border-meta-gray-300 rounded-lg p-4 overflow-x-auto mb-4" {...props} />
              ),
              blockquote: ({node, ...props}) => (
                <blockquote className="border-l-4 border-meta-blue pl-4 italic text-meta-gray/70 my-4" {...props} />
              ),
              ul: ({node, ...props}) => (
                <ul className="list-disc list-inside mb-4 text-meta-gray/80 space-y-1" {...props} />
              ),
              ol: ({node, ...props}) => (
                <ol className="list-decimal list-inside mb-4 text-meta-gray/80 space-y-1" {...props} />
              ),
              li: ({node, ...props}) => (
                <li className="leading-relaxed" {...props} />
              ),
              table: ({node, ...props}) => (
                <div className="overflow-x-auto mb-4">
                  <table className="min-w-full border-collapse border border-meta-gray-300" {...props} />
                </div>
              ),
              th: ({node, ...props}) => (
                <th className="border border-meta-gray-300 px-4 py-2 bg-meta-gray-100/20 text-meta-gray font-medium text-left" {...props} />
              ),
              td: ({node, ...props}) => (
                <td className="border border-meta-gray-300 px-4 py-2 text-meta-gray/80" {...props} />
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
