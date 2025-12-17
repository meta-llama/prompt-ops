import React from 'react';
import { ChevronDown, ChevronRight, Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { DocItem } from '@/types';

interface DocsSidebarProps {
  docs: DocItem[];
  categories: string[];
  selectedDoc: DocItem | null;
  onSelectDoc: (doc: DocItem) => void;
  isOpen: boolean;
  onToggle: () => void;
}

export const DocsSidebar: React.FC<DocsSidebarProps> = ({
  docs,
  categories,
  selectedDoc,
  onSelectDoc,
  isOpen,
  onToggle,
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
        <Button
          onClick={onToggle}
          variant="ghost"
          size="sm"
          className="fixed left-4 top-1/2 -translate-y-1/2 z-10 bg-white border border-meta-gray-300/50 rounded-full"
        >
          <Menu className="w-4 h-4" />
        </Button>
      </div>
    );
  }

  return (
    <div className="h-full bg-white rounded-3xl border border-meta-gray-300/50 p-4 overflow-hidden flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-meta-gray">Contents</h3>
        <Button
          onClick={onToggle}
          variant="ghost"
          size="sm"
          className="hover:bg-meta-gray-100/20"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto">
        <div className="space-y-2">
          {categories.map((category) => {
            const categoryDocs = docs.filter(doc => doc.category === category);
            const isExpanded = expandedCategories.has(category);

            return (
              <div key={category} className="space-y-1">
                {/* Category Header */}
                <button
                  onClick={() => toggleCategory(category)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-left rounded-lg hover:bg-meta-gray-100/20 transition-all duration-200 group"
                >
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-meta-gray/50 group-hover:text-meta-blue" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-meta-gray/50 group-hover:text-meta-blue" />
                  )}
                  <span className="font-medium text-meta-gray group-hover:text-meta-blue">
                    {category}
                  </span>
                  <span className="text-xs text-meta-gray/40 ml-auto">
                    {categoryDocs.length}
                  </span>
                </button>

                {/* Category Items */}
                {isExpanded && (
                  <div className="ml-6 space-y-1">
                    {categoryDocs.map((doc) => {
                      const isSelected = selectedDoc?.id === doc.id;
                      const Icon = doc.icon;

                      return (
                        <button
                          key={doc.id}
                          onClick={() => onSelectDoc(doc)}
                          className={`w-full flex items-center gap-2 px-3 py-2 text-left rounded-lg transition-all duration-200 group ${
                            isSelected
                              ? 'bg-meta-blue text-white shadow-sm'
                              : 'hover:bg-meta-gray-100/20 text-meta-gray hover:text-meta-blue'
                          }`}
                        >
                          {Icon && (
                            <Icon className={`w-4 h-4 ${
                              isSelected ? 'text-white' : 'text-meta-gray/50 group-hover:text-meta-blue'
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
      <div className="mt-6 pt-4 border-t border-meta-gray-300">
        <div className="text-xs text-meta-gray/50 text-center">
          {docs.length} documents
        </div>
      </div>
    </div>
  );
};
