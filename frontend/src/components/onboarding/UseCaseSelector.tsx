import React from 'react';
import { cn } from '@/lib/utils';
import { FileQuestion, Database, Settings, Check } from 'lucide-react';

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
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Select Your Use Case
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Choose the type that best matches your project to get relevant options in the next steps
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {useCases.map((useCase) => (
          <button
            key={useCase.id}
            onClick={() => onSelectUseCase(useCase.id, useCase.config)}
            className={cn(
              "relative p-6 rounded-xl border-2",
              "text-left transition-all duration-200",
              "hover:shadow-lg hover:-translate-y-1",
              selectedUseCase === useCase.id
                ? "border-facebook-blue bg-facebook-blue/5"
                : "border-gray-300 bg-white hover:border-gray-400"
            )}
          >
            {/* Selection indicator */}
            {selectedUseCase === useCase.id && (
              <div className="absolute top-3 right-3 w-6 h-6 bg-facebook-blue rounded-full flex items-center justify-center">
                <Check className="w-4 h-4 text-white" />
              </div>
            )}

            {/* Icon */}
            <div className={cn(
              "w-12 h-12 rounded-lg flex items-center justify-center mb-4",
              selectedUseCase === useCase.id
                ? "bg-facebook-blue text-white"
                : "bg-gray-100 text-gray-600"
            )}>
              {useCase.icon}
            </div>

            {/* Content */}
            <h4 className="font-semibold text-gray-900 mb-2">
              {useCase.title}
            </h4>
            <p className="text-sm text-gray-700 mb-3">
              {useCase.description}
            </p>

            {/* Use case examples */}
            <div className="space-y-1">
              <p className="text-xs font-medium text-gray-600 mb-2">
                Common applications:
              </p>
              {useCase.examples.slice(0, 4).map((example, index) => (
                <p key={index} className="text-xs text-gray-700 flex items-center">
                  <span className="w-1 h-1 bg-facebook-blue rounded-full mr-2 flex-shrink-0"></span>
                  {example}
                </p>
              ))}
              {useCase.examples.length > 4 && (
                <p className="text-xs text-gray-500 italic">
                  +{useCase.examples.length - 4} more...
                </p>
              )}
            </div>
          </button>
        ))}
      </div>

      {/* Expected Format Section */}
      {selectedUseCase && useCases.find(uc => uc.id === selectedUseCase)?.expectedFormat && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h4 className="text-sm font-semibold text-gray-900 mb-3">
            {useCases.find(uc => uc.id === selectedUseCase)?.expectedFormat?.title}
          </h4>
          <pre className="text-xs text-gray-700 bg-white p-3 rounded border overflow-x-auto">
            <code>{useCases.find(uc => uc.id === selectedUseCase)?.expectedFormat?.structure}</code>
          </pre>
        </div>
      )}

      {/* Helper text based on selection */}
      {selectedUseCase && (
        <div className={cn(
          "mt-4 p-4 rounded-lg",
          "bg-blue-50 border border-blue-200"
        )}>
          <p className="text-sm">
            {selectedUseCase === 'custom'
              ? "You'll configure all settings manually in the following steps based on your specific requirements."
              : `Perfect! We'll show you the most relevant options for ${
                  useCases.find(uc => uc.id === selectedUseCase)?.title
                } applications in the next steps.`
            }
          </p>
        </div>
      )}
    </div>
  );
};
