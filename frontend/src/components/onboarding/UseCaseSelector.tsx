import React from 'react';
import { cn } from '@/lib/utils';
import { FileQuestion, Database, Settings } from 'lucide-react';
import { SelectableCard } from '@/components/ui/selectable-card';
import { InfoBox } from '@/components/ui/info-box';

interface UseCase {
  id: string;
  title: string;
  description: string;
  examples: string[];
  expectedFormat?: {
    title: string;
    structure: string;
  };
  icon: React.ReactNode;
  config: {
    datasetAdapter?: string;
    metrics?: string;
    optimizer?: string;
    model?: string;
  };
}

interface UseCaseSelectorProps {
  selectedUseCase?: string;
  onSelectUseCase: (useCaseId: string, config: any) => void;
  className?: string;
}

const useCases: UseCase[] = [
  {
    id: 'qa',
    title: 'Q&A',
    description: 'Direct question-answering systems',
    examples: [
      'Customer support chatbots',
      'FAQ systems',
      'Educational Q&A',
      'Knowledge base queries'
    ],
    expectedFormat: {
      title: 'Expected Format for Q&A:',
      structure: `[
  {
    "question": "What is the capital of France?",
    "answer": "Paris"
  }
]`
    },
    icon: <FileQuestion className="w-6 h-6" />,
    config: {
      datasetAdapter: 'Question-Answer',
      metrics: 'Exact Match',
      optimizer: 'MiPro',
    }
  },
  {
    id: 'rag',
    title: 'RAG',
    description: 'Document-based information retrieval',
    examples: [
      'Legal document analysis',
      'Technical documentation search',
      'Content summarization',
      'Code repository queries'
    ],
    expectedFormat: {
      title: 'Expected Format for RAG:',
      structure: `[
  {
    "query": "What are the key terms in this contract?",
    "context": [
      "Document 1 content text...",
      "Document 2 content text..."
    ],
    "answer": "The key terms include..."
  }
]`
    },
    icon: <Database className="w-6 h-6" />,
    config: {
      datasetAdapter: 'Document-Query',
      metrics: 'Retrieval F1',
      optimizer: 'MIPRO-RAG',
    }
  },
  {
    id: 'custom',
    title: 'Custom',
    description: 'Configure all settings manually for specialized use cases',
    examples: [
      'Unique business requirements',
      'Experimental configurations',
      'Domain-specific optimizations'
    ],
    icon: <Settings className="w-6 h-6" />,
    config: {}
  }
];

export const UseCaseSelector: React.FC<UseCaseSelectorProps> = ({
  selectedUseCase,
  onSelectUseCase,
  className
}) => {
  return (
    <div className={cn("space-y-4", className)}>
      <div>
        <h3 className="text-lg font-semibold text-foreground mb-2">
          Select Your Use Case
        </h3>
        <p className="text-sm text-muted-foreground mb-4">
          Choose the type that best matches your project to get relevant options in the next steps
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {useCases.map((useCase) => (
          <SelectableCard
            key={useCase.id}
            selected={selectedUseCase === useCase.id}
            onClick={() => onSelectUseCase(useCase.id, useCase.config)}
            icon={useCase.icon}
            title={useCase.title}
            description={useCase.description}
          >
            {/* Use case examples */}
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground mb-2">
                Common applications:
              </p>
              {useCase.examples.slice(0, 4).map((example, index) => (
                <p key={index} className="text-xs text-muted-foreground flex items-center">
                  <span className="w-1 h-1 bg-meta-blue dark:bg-meta-blue-light rounded-full mr-2 flex-shrink-0"></span>
                  {example}
                </p>
              ))}
              {useCase.examples.length > 4 && (
                <p className="text-xs text-muted-foreground/70 italic">
                  +{useCase.examples.length - 4} more...
                </p>
              )}
            </div>
          </SelectableCard>
        ))}
      </div>

      {/* Expected Format Section */}
      {selectedUseCase && useCases.find(uc => uc.id === selectedUseCase)?.expectedFormat && (
        <div className="mt-4 p-4 bg-muted rounded-lg border border-border">
          <h4 className="text-sm font-semibold text-foreground mb-3">
            {useCases.find(uc => uc.id === selectedUseCase)?.expectedFormat?.title}
          </h4>
          <pre className="text-xs text-muted-foreground bg-card p-3 rounded border border-border overflow-x-auto">
            <code>{useCases.find(uc => uc.id === selectedUseCase)?.expectedFormat?.structure}</code>
          </pre>
        </div>
      )}

      {/* Helper text based on selection */}
      {selectedUseCase && (
        <InfoBox variant="info" className="mt-4">
          {selectedUseCase === 'custom'
            ? "You'll configure all settings manually in the following steps based on your specific requirements."
            : `Perfect! We'll show you the most relevant options for ${
                useCases.find(uc => uc.id === selectedUseCase)?.title
              } applications in the next steps.`
          }
        </InfoBox>
      )}
    </div>
  );
};
