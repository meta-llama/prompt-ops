import React from 'react';
import { ChevronDown, ChevronRight, Menu, X, Search } from 'lucide-react';
import type { DocItem } from '@/types';

interface DocsSidebarProps {
  docs: DocItem[];
  categories: string[];
  selectedDoc: DocItem | null;
  onSelectDoc: (doc: DocItem) => void;
  isOpen: boolean;
  onToggle: () => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

export const DocsSidebar: React.FC<DocsSidebarProps> = ({
  docs,
  categories,
  selectedDoc,
  onSelectDoc,
  isOpen,
  onToggle,
  searchQuery,
  onSearchChange,
}) => {
  const [expandedCategories, setExpandedCategories] = React.useState<Set<string>>(
    new Set(categories)
  );

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  if (!isOpen) {
    return (
      <div className="w-0 overflow-hidden">
        <button
          onClick={onToggle}
          className="fixed left-4 top-1/2 -translate-y-1/2 z-10 p-2 glass-panel-solid hover:bg-white/[0.1] transition-colors"
        >
          <Menu className="w-4 h-4 text-white" />
        </button>
      </div>
    );
  }

  return (
    <div className="h-full glass-panel p-4 overflow-hidden flex flex-col animate-fade-in">
      {/* Header with Search */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-white/80 uppercase tracking-wider">Contents</h3>
          <button
            onClick={onToggle}
            className="p-1.5 rounded-lg hover:bg-white/[0.08] transition-colors"
          >
            <X className="w-4 h-4 text-white/50 hover:text-white" />
          </button>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
          <input
            type="text"
            placeholder="Search docs..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full glass-input pl-9 pr-3 py-2 text-sm"
          />
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto -mx-2 px-2">
        <div className="space-y-1">
          {categories.map((category) => {
            const categoryDocs = docs.filter(doc => doc.category === category);
            const isExpanded = expandedCategories.has(category);

            if (categoryDocs.length === 0) return null;

            return (
              <div key={category} className="space-y-0.5">
                {/* Category Header */}
                <button
                  onClick={() => toggleCategory(category)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-left rounded-lg hover:bg-white/[0.05] transition-all duration-200 group"
                >
                  {isExpanded ? (
                    <ChevronDown className="w-3.5 h-3.5 text-white/40 group-hover:text-[#4da3ff]" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5 text-white/40 group-hover:text-[#4da3ff]" />
                  )}
                  <span className="text-sm font-medium text-white/70 group-hover:text-white">
                    {category}
                  </span>
                  <span className="text-xs text-white/30 ml-auto">
                    {categoryDocs.length}
                  </span>
                </button>

                {/* Category Items */}
                {isExpanded && (
                  <div className="ml-4 space-y-0.5">
                    {categoryDocs.map((doc) => {
                      const isSelected = selectedDoc?.id === doc.id;
                      const Icon = doc.icon;

                      return (
                        <button
                          key={doc.id}
                          onClick={() => onSelectDoc(doc)}
                          className={`w-full flex items-center gap-2 px-3 py-2 text-left rounded-lg transition-all duration-200 group ${
                            isSelected
                              ? 'bg-[#0064E0] text-white'
                              : 'hover:bg-white/[0.05] text-white/60 hover:text-white'
                          }`}
                        >
                          {Icon && (
                            <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${
                              isSelected ? 'text-white' : 'text-white/40 group-hover:text-[#4da3ff]'
                            }`} />
                          )}
                          <span className="text-sm font-medium truncate">
                            {doc.title}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-white/[0.08]">
        <div className="text-xs text-white/30 text-center">
          {docs.length} documents
        </div>
      </div>
    </div>
  );
};
