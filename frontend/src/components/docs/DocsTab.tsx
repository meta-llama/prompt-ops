import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Book, Search, FileText, Code, Settings, ChevronRight } from 'lucide-react';
import { DocsContent } from './DocsContent';
import { DocsSidebar } from './DocsSidebar';
import type { DocItem } from '@/types';

export type { DocItem } from '@/types';

export const DocsTab = () => {
  const { docId } = useParams<{ docId?: string }>();
  const navigate = useNavigate();
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
      script.setAttribute('runllm-name', 'prompt-ops Assistant');
      script.setAttribute('runllm-position', 'BOTTOM_RIGHT');
      // RunLLM Assistant ID from https://app.runllm.com/assistant/1149
      script.setAttribute('runllm-assistant-id', '1149');
      script.setAttribute('runllm-theme-color', '#0064E0');
      script.setAttribute('runllm-floating-button-text', 'Ask AI');
      script.setAttribute('runllm-disclaimer', 'This AI assistant can help you navigate the prompt-ops documentation.');
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
      description: 'Learn the fundamentals of prompt-ops',
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

  // Sync selectedDoc with URL parameter
  useEffect(() => {
    if (docId) {
      const doc = docsStructure.find(d => d.id === docId);
      if (doc) {
        setSelectedDoc(doc);
      }
    } else {
      setSelectedDoc(null);
    }
  }, [docId]);

  // Handler to update both state and URL when selecting a doc
  const handleSelectDoc = (doc: DocItem) => {
    setSelectedDoc(doc);
    navigate(`/docs/${doc.id}`);
  };

  const filteredDocs = docsStructure.filter(doc =>
    doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const categories = Array.from(new Set(docsStructure.map(doc => doc.category)));

  return (
    <div className="h-full flex gap-6 px-8 py-6 max-w-7xl mx-auto">
      {/* Sidebar */}
      <div className={`transition-all duration-300 ${sidebarOpen ? 'w-72' : 'w-0'} flex-shrink-0`}>
        <DocsSidebar
          docs={filteredDocs}
          categories={categories}
          selectedDoc={selectedDoc}
          onSelectDoc={handleSelectDoc}
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
        />
      </div>

      {/* Content Area */}
      <div className="flex-1 min-w-0 overflow-hidden">
        {selectedDoc ? (
          <DocsContent doc={selectedDoc} />
        ) : (
          <DocsOverview docs={docsStructure} onSelectDoc={handleSelectDoc} />
        )}
      </div>
    </div>
  );
};

// Overview component showing doc categories when no specific doc is selected
const DocsOverview = ({ docs, onSelectDoc }: { docs: DocItem[], onSelectDoc: (doc: DocItem) => void }) => {
  const categories = Array.from(new Set(docs.map(doc => doc.category)));

  return (
    <div className="h-full glass-panel overflow-y-auto p-8 animate-fade-in">
      <div className="space-y-8">
        {/* Welcome Header */}
        <div className="text-center py-6">
          <div className="w-16 h-16 rounded-2xl bg-white/[0.05] border border-white/[0.1] flex items-center justify-center mx-auto mb-4">
            <Book className="w-8 h-8 text-[#4da3ff]" />
          </div>
          <h2 className="text-2xl font-semibold text-white mb-2">
            Documentation
          </h2>
          <p className="text-white/60 max-w-md mx-auto">
            Select a document from the sidebar or browse by category below.
            <span className="block mt-2 text-sm text-[#4da3ff]">
              Press ⌘J to ask AI for help
            </span>
          </p>
        </div>

        {/* Category Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {categories.map(category => {
            const categoryDocs = docs.filter(doc => doc.category === category);
            return (
              <div
                key={category}
                className="glass-panel-solid p-5 hover:bg-white/[0.08] transition-all duration-300"
              >
                <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                  {category === 'Basics' && <Book className="w-4 h-4 text-[#4da3ff]" />}
                  {category === 'Guides' && <FileText className="w-4 h-4 text-[#4da3ff]" />}
                  {category === 'Intermediate' && <Settings className="w-4 h-4 text-[#4da3ff]" />}
                  {category === 'Advanced' && <Code className="w-4 h-4 text-[#4da3ff]" />}
                  {category}
                </h3>
                <div className="space-y-1">
                  {categoryDocs.map(doc => (
                    <button
                      key={doc.id}
                      onClick={() => onSelectDoc(doc)}
                      className="w-full text-left p-3 rounded-xl hover:bg-white/[0.08] transition-all duration-200 group"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-white/90 group-hover:text-white transition-colors text-sm">
                            {doc.title}
                          </h4>
                          {doc.description && (
                            <p className="text-xs text-white/50 mt-0.5 group-hover:text-white/60 transition-colors">
                              {doc.description}
                            </p>
                          )}
                        </div>
                        <ChevronRight className="w-4 h-4 text-white/30 group-hover:text-[#4da3ff] group-hover:translate-x-0.5 transition-all" />
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
