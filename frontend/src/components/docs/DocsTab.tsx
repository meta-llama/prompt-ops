import React, { useState, useEffect } from 'react';
import { Book, Search, FileText, Code, Settings, ChevronRight, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { DocsContent } from './DocsContent';
import { DocsSidebar } from './DocsSidebar';

export interface DocItem {
  id: string;
  title: string;
  path: string;
  category: string;
  description?: string;
  lastModified?: string;
  icon?: React.ElementType;
}

export const DocsTab = () => {
  const [selectedDoc, setSelectedDoc] = useState<DocItem | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Load RunLLM widget when component mounts
  useEffect(() => {
    const loadRunLLMWidget = () => {
      // Check if script already exists
      if (document.getElementById('runllm-widget-script')) {
        return;
      }

      const script = document.createElement('script');
      script.type = 'module';
      script.id = 'runllm-widget-script';
      script.src = 'https://widget.runllm.com';
      script.setAttribute('version', 'stable');
      script.setAttribute('crossorigin', 'true');
      script.setAttribute('runllm-keyboard-shortcut', 'Mod+j');
      script.setAttribute('runllm-name', 'llama-prompt-ops Assistant');
      script.setAttribute('runllm-position', 'BOTTOM_RIGHT');
      // RunLLM Assistant ID from https://app.runllm.com/assistant/1149
      script.setAttribute('runllm-assistant-id', '1149');
      script.setAttribute('runllm-theme-color', '#1877f2'); // Facebook blue
      script.setAttribute('runllm-floating-button-text', 'Ask AI');
      script.setAttribute('runllm-disclaimer', 'This AI assistant can help you navigate the llama-prompt-ops documentation.');
      script.async = true;

      document.head.appendChild(script);
    };

    loadRunLLMWidget();

    // Cleanup function to remove the script when component unmounts
    return () => {
      const script = document.getElementById('runllm-widget-script');
      if (script) {
        document.head.removeChild(script);
      }
    };
  }, []);

  // Sample docs structure - in a real app, this would come from an API
  const docsStructure: DocItem[] = [
    {
      id: 'getting-started',
      title: 'Getting Started',
      path: 'README.md',
      category: 'Basics',
      description: 'Learn the fundamentals of llama-prompt-ops',
      icon: Book
    },
    {
      id: 'metrics-guide',
      title: 'Metric Selection Guide',
      path: 'metric_selection_guide.md',
      category: 'Guides',
      description: 'Choose the right metrics for your optimization',
      icon: Settings
    },
    {
      id: 'dataset-adapter',
      title: 'Dataset Adapter Guide',
      path: 'dataset_adapter_selection_guide.md',
      category: 'Guides',
      description: 'Configure dataset adapters for different data formats',
      icon: FileText
    },
    {
      id: 'intermediate-guide',
      title: 'Facility YAML Configuration',
      path: 'intermediate/readme.md',
      category: 'Intermediate',
      description: 'Advanced YAML configuration options for facility management tasks',
      icon: Code
    },
    {
      id: 'inference-providers',
      title: 'Inference Providers',
      path: 'inference_providers.md',
      category: 'Advanced',
      description: 'Configure and use different inference providers',
      icon: Code
    }
  ];

  const filteredDocs = docsStructure.filter(doc =>
    doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const categories = Array.from(new Set(docsStructure.map(doc => doc.category)));

  return (
    <div className="max-w-7xl mx-auto h-full">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-black text-facebook-text mb-4 tracking-tight">
          Documentation
        </h1>
        <p className="text-lg text-facebook-text/70 max-w-8xl">
          Comprehensive guides, API references, and examples to help you get the most out of llama-prompt-ops.
          <span className="inline-block ml-2 px-2 py-1 bg-facebook-blue/10 text-facebook-blue text-sm rounded-full font-medium">
            💬 Ask AI for help (Cmd+J)
          </span>
        </p>
      </div>

      {/* Search Bar */}
      <div className="mb-8">
        <div className="relative max-w-lg">
          <Search className="absolute left-3 top-3 h-4 w-4 text-facebook-text/50" />
          <Input
            placeholder="Search documentation..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 h-12 text-lg border-facebook-border focus:border-facebook-blue focus:ring-facebook-blue/20"
          />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex gap-8 h-[calc(100vh-240px)]">
        {/* Sidebar */}
        <div className={`transition-all duration-300 ${sidebarOpen ? 'w-80' : 'w-0'} flex-shrink-0`}>
          <DocsSidebar
            docs={filteredDocs}
            categories={categories}
            selectedDoc={selectedDoc}
            onSelectDoc={setSelectedDoc}
            isOpen={sidebarOpen}
            onToggle={() => setSidebarOpen(!sidebarOpen)}
          />
        </div>

        {/* Content Area */}
        <div className="flex-1 min-w-0">
          {selectedDoc ? (
            <DocsContent doc={selectedDoc} />
          ) : (
            <DocsOverview docs={docsStructure} onSelectDoc={setSelectedDoc} />
          )}
        </div>
      </div>
    </div>
  );
};

// Overview component showing doc categories when no specific doc is selected
const DocsOverview = ({ docs, onSelectDoc }: { docs: DocItem[], onSelectDoc: (doc: DocItem) => void }) => {
  const categories = Array.from(new Set(docs.map(doc => doc.category)));

  return (
    <div className="space-y-8">
      <div className="text-center py-8">
        <Book className="w-16 h-16 text-facebook-blue/20 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-facebook-text mb-2">
          Welcome to the Documentation
        </h2>
        <p className="text-facebook-text/70">
          Select a document from the sidebar or browse by category below.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {categories.map(category => {
          const categoryDocs = docs.filter(doc => doc.category === category);
          return (
            <div
              key={category}
              className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-facebook-border hover:shadow-xl transition-all duration-300"
            >
              <h3 className="text-xl font-bold text-facebook-text mb-4 flex items-center gap-2">
                {category === 'Basics' && <Book className="w-5 h-5 text-facebook-blue" />}
                {category === 'Guides' && <FileText className="w-5 h-5 text-facebook-blue" />}
                {category === 'Intermediate' && <Settings className="w-5 h-5 text-facebook-blue" />}
                {category === 'Advanced' && <Code className="w-5 h-5 text-facebook-blue" />}
                {category}
              </h3>
              <div className="space-y-3">
                {categoryDocs.map(doc => (
                  <button
                    key={doc.id}
                    onClick={() => onSelectDoc(doc)}
                    className="w-full text-left p-3 rounded-lg hover:bg-facebook-gray/20 transition-all duration-200 group"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium text-facebook-text group-hover:text-facebook-blue transition-colors">
                          {doc.title}
                        </h4>
                        {doc.description && (
                          <p className="text-sm text-facebook-text/60 mt-1">
                            {doc.description}
                          </p>
                        )}
                      </div>
                      <ChevronRight className="w-4 h-4 text-facebook-text/40 group-hover:text-facebook-blue transition-colors" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
