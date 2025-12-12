import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
  Check,
  Info,
  Settings,
  Zap,
  Target,
  Brain,
  FileText,
  BarChart3,
  AlertCircle,
  HelpCircle,
} from "lucide-react";

// Helper components for complex parameter types
const ArrayInput: React.FC<{
  value: string[];
  onChange: (value: string[]) => void;
  arrayType: "string" | "number";
  placeholder: string;
}> = ({ value, onChange, arrayType, placeholder }) => {
  const [inputValue, setInputValue] = useState<string>(value.join(", "));

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);

    // Parse comma-separated values
    const items = newValue
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item.length > 0);

    if (arrayType === "number") {
      const numbers = items
        .map((item) => parseFloat(item))
        .filter((num) => !isNaN(num));
      onChange(numbers.map(String));
    } else {
      onChange(items);
    }
  };

  return (
    <input
      type="text"
      value={inputValue}
      onChange={handleChange}
      placeholder={placeholder}
      className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-facebook-blue focus:border-transparent"
    />
  );
};

const FieldMappingInput: React.FC<{
  value: Record<string, number>;
  onChange: (value: Record<string, number>) => void;
  placeholder: string;
}> = ({ value, onChange, placeholder }) => {
  const [inputValue, setInputValue] = useState<string>(
    Object.entries(value)
      .map(([key, val]) => `${key}: ${val}`)
      .join(", ")
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);

    // Parse field mappings (field_name: weight)
    const mappings: Record<string, number> = {};
    const pairs = newValue
      .split(",")
      .map((pair) => pair.trim())
      .filter((pair) => pair.length > 0);

    pairs.forEach((pair) => {
      const [key, value] = pair.split(":").map((item) => item.trim());
      if (key && value) {
        const numValue = parseFloat(value);
        if (!isNaN(numValue)) {
          mappings[key] = numValue;
        }
      }
    });

    onChange(mappings);
  };

  return (
    <input
      type="text"
      value={inputValue}
      onChange={handleChange}
      placeholder={placeholder}
      className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-facebook-blue focus:border-transparent"
    />
  );
};

interface MetricConfig {
  id: string;
  name: string;
  description: string;
  type: "exact" | "semantic" | "structured" | "custom";
  icon: React.ReactNode;
  useCases: string[];
  dataRequirements: string[];
  parameters?: {
    [key: string]: {
      type:
        | "boolean"
        | "number"
        | "string"
        | "select"
        | "array"
        | "object"
        | "fieldMapping";
      default: any;
      description: string;
      options?: string[];
      arrayType?: "string" | "number";
      objectSchema?: {
        [key: string]: {
          type: "string" | "number" | "boolean";
          required?: boolean;
        };
      };
    };
  };
  examples: {
    input: string;
    output: string;
    score: string;
  }[];
  pros: string[];
  cons: string[];
  recommendedFor: string[];
}

interface MetricsSelectorProps {
  useCase: string;
  fieldMappings: Record<string, string>;
  selectedMetrics: string[];
  onMetricsChange: (
    metrics: string[],
    configurations: Record<string, any>
  ) => void;
  className?: string;
}

const AVAILABLE_METRICS: MetricConfig[] = [
  {
    id: "exact_match",
    name: "Exact Match",
    description:
      "Compares predictions to ground truth using exact string matching",
    type: "exact",
    icon: <Target className="w-5 h-5" />,
    useCases: ["qa", "rag", "custom"],
    dataRequirements: ["Clear, unambiguous answers", "Consistent formatting"],
    parameters: {
      case_sensitive: {
        type: "boolean",
        default: true,
        description: "Whether to perform case-sensitive matching",
      },
      strip_whitespace: {
        type: "boolean",
        default: true,
        description: "Whether to strip whitespace before comparing",
      },
    },
    examples: [
      {
        input: "What is the capital of France?",
        output: "Paris",
        score: "1.0 (Perfect match)",
      },
      {
        input: "What is the capital of France?",
        output: "paris",
        score: "0.0 (Case mismatch)",
      },
    ],
    pros: [
      "Fast and deterministic",
      "Easy to understand",
      "No API costs",
      "Perfect for factual answers",
    ],
    cons: [
      "Too strict for complex answers",
      "Misses semantically correct variations",
      "Sensitive to formatting differences",
    ],
    recommendedFor: [
      "Factual Q&A",
      "Classification tasks",
      "Exact value extraction",
    ],
  },
  {
    id: "semantic_similarity",
    name: "Semantic Similarity",
    description:
      "Uses AI to evaluate semantic similarity between prediction and ground truth",
    type: "semantic",
    icon: <Brain className="w-5 h-5" />,
    useCases: ["qa", "rag", "custom"],
    dataRequirements: [
      "Natural language answers",
      "Conceptual understanding needed",
    ],
    parameters: {
      score_range: {
        type: "select",
        default: "1-10",
        options: ["1-5", "1-10", "0-1"],
        description: "Score range for evaluation",
      },
      normalize_to: {
        type: "select",
        default: "0-1",
        options: ["0-1", "1-10"],
        description: "Range to normalize scores to",
      },
    },
    examples: [
      {
        input: "What is the capital of France?",
        output: "The capital city of France is Paris",
        score: "0.95 (High semantic similarity)",
      },
      {
        input: "What is the capital of France?",
        output: "It is located in Europe",
        score: "0.3 (Low semantic similarity)",
      },
    ],
    pros: [
      "Understands meaning, not just words",
      "Handles paraphrasing well",
      "Good for complex answers",
      "More human-like evaluation",
    ],
    cons: [
      "Requires AI model calls",
      "Can be inconsistent",
      "Slower than exact match",
      "API costs involved",
    ],
    recommendedFor: ["Complex Q&A", "Summary evaluation", "Creative tasks"],
  },
  {
    id: "correctness",
    name: "Correctness Evaluation",
    description:
      "AI-powered evaluation focusing on factual correctness rather than similarity",
    type: "semantic",
    icon: <Zap className="w-5 h-5" />,
    useCases: ["qa", "rag", "custom"],
    dataRequirements: ["Factual content", "Clear ground truth"],
    parameters: {
      score_range: {
        type: "select",
        default: "1-10",
        options: ["1-5", "1-10", "0-1"],
        description: "Score range for evaluation",
      },
    },
    examples: [
      {
        input: "When was World War II?",
        output: "1939-1945",
        score: "1.0 (Factually correct)",
      },
      {
        input: "When was World War II?",
        output: "It was a major global conflict",
        score: "0.2 (Correct but incomplete)",
      },
    ],
    pros: [
      "Focuses on factual accuracy",
      "Good for knowledge tasks",
      "Handles different phrasings",
      "Evaluates completeness",
    ],
    cons: [
      "Requires AI model calls",
      "May miss nuanced correctness",
      "API costs involved",
    ],
    recommendedFor: [
      "Factual Q&A",
      "Knowledge retrieval",
      "Educational content",
    ],
  },
  {
    id: "json_structured",
    name: "Structured JSON",
    description:
      "Evaluates structured JSON responses by comparing specific fields",
    type: "structured",
    icon: <FileText className="w-5 h-5" />,
    useCases: ["qa", "rag", "custom"],
    dataRequirements: ["JSON-formatted responses", "Structured data fields"],
    parameters: {
      evaluation_mode: {
        type: "select",
        default: "selected_fields_comparison",
        options: ["selected_fields_comparison", "full_json_comparison"],
        description: "How to evaluate the JSON structure",
      },
      strict_json: {
        type: "boolean",
        default: false,
        description: "Whether to require strict JSON parsing",
      },
      output_fields: {
        type: "array",
        default: [],
        arrayType: "string",
        description:
          "List of fields to evaluate (leave empty to evaluate all fields)",
      },
      required_fields: {
        type: "array",
        default: [],
        arrayType: "string",
        description: "Fields that must be present for a valid prediction",
      },
      field_weights: {
        type: "fieldMapping",
        default: {},
        description:
          "Weight for each field in the evaluation (field_name: weight)",
      },
      output_field: {
        type: "string",
        default: "answer",
        description: "Name of the field containing the ground truth output",
      },
    },
    examples: [
      {
        input: "Categorize this request",
        output: '{"category": "urgent", "sentiment": "negative"}',
        score: "1.0 (All fields match)",
      },
      {
        input: "Categorize this request",
        output: '{"category": "urgent", "sentiment": "positive"}',
        score: "0.5 (Partial field match)",
      },
    ],
    pros: [
      "Perfect for structured outputs",
      "Field-level granular scoring",
      "Fast evaluation",
      "Configurable field weights",
    ],
    cons: [
      "Only works with JSON",
      "Requires structured ground truth",
      "Less flexible for natural language",
    ],
    recommendedFor: [
      "Classification tasks",
      "Structured data extraction",
      "API response evaluation",
    ],
  },
  {
    id: "facility_metric",
    name: "Facility Categorization",
    description:
      "Specialized metric for facility support requests with urgency, sentiment, and categories",
    type: "custom",
    icon: <AlertCircle className="w-5 h-5" />,
    useCases: ["qa", "rag", "custom"],
    dataRequirements: [
      "JSON responses with urgency, sentiment, and categories fields",
      "Facility support request data",
    ],
    parameters: {
      output_field: {
        type: "string",
        default: "answer",
        description: "Name of the field containing the ground truth output",
      },
      strict_json: {
        type: "boolean",
        default: false,
        description:
          "Whether to require strict JSON parsing (no code block extraction)",
      },
    },
    examples: [
      {
        input: "Urgent HVAC issue in Building A",
        output:
          '{"urgency": "high", "sentiment": "frustrated", "categories": {"hvac": true, "maintenance": true}}',
        score: "1.0 (Perfect categorization)",
      },
      {
        input: "Request for new office supplies",
        output:
          '{"urgency": "low", "sentiment": "neutral", "categories": {"supplies": true, "administrative": true}}',
        score: "1.0 (Correct low-priority request)",
      },
    ],
    pros: [
      "Domain-specific for facility management",
      "Evaluates multiple dimensions (urgency, sentiment, categories)",
      "Handles boolean category mappings",
      "Fast, deterministic scoring",
    ],
    cons: [
      "Only works with facility-specific JSON format",
      "Limited to urgency/sentiment/categories structure",
      "Not suitable for other domains",
    ],
    recommendedFor: [
      "Facility support automation",
      "Maintenance request categorization",
      "Support ticket prioritization",
    ],
  },
];

const METRIC_TYPE_INFO = {
  exact: {
    name: "Exact Matching",
    description: "Fast, deterministic comparison",
    color: "bg-green-100 text-green-800",
  },
  semantic: {
    name: "AI-Powered",
    description: "Understands meaning and context",
    color: "bg-blue-100 text-blue-800",
  },
  structured: {
    name: "Structured Data",
    description: "Perfect for JSON and structured outputs",
    color: "bg-purple-100 text-purple-800",
  },
  custom: {
    name: "Custom Logic",
    description: "Domain-specific evaluation",
    color: "bg-orange-100 text-orange-800",
  },
};

export const MetricsSelector: React.FC<MetricsSelectorProps> = ({
  useCase,
  fieldMappings,
  selectedMetrics,
  onMetricsChange,
  className,
}) => {
  const [configurations, setConfigurations] = useState<Record<string, any>>({});
  const [expandedMetric, setExpandedMetric] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Filter metrics based on use case
  const availableMetrics = AVAILABLE_METRICS.filter(
    (metric) => metric.useCases.includes(useCase) || useCase === "custom"
  );

  // Get recommended metrics based on use case and field mappings
  const getRecommendedMetrics = () => {
    const hasStructuredFields = Object.keys(fieldMappings).length > 2;
    const hasJsonLikeFields = Object.keys(fieldMappings).some(
      (key) =>
        key.includes("category") ||
        key.includes("sentiment") ||
        key.includes("urgency")
    );

    const hasFacilityFields =
      Object.keys(fieldMappings).some(
        (key) =>
          key.includes("urgency") &&
          key.includes("sentiment") &&
          key.includes("categories")
      ) ||
      (Object.keys(fieldMappings).length >= 3 && hasJsonLikeFields);

    if (useCase === "qa") {
      return hasJsonLikeFields
        ? ["semantic_similarity", "json_structured"]
        : ["exact_match", "semantic_similarity"];
    } else if (useCase === "rag") {
      return ["correctness", "semantic_similarity"];
    } else {
      // Custom use case
      if (hasFacilityFields) {
        return ["facility_metric", "json_structured"];
      }
      return hasStructuredFields ? ["json_structured"] : ["exact_match"];
    }
  };

  const recommendedMetrics = getRecommendedMetrics();

  const handleMetricToggle = (metricId: string) => {
    const newSelectedMetrics = selectedMetrics.includes(metricId)
      ? selectedMetrics.filter((id) => id !== metricId)
      : [...selectedMetrics, metricId];

    onMetricsChange(newSelectedMetrics, configurations);
  };

  const handleParameterChange = (
    metricId: string,
    paramName: string,
    value: any
  ) => {
    const newConfigurations = {
      ...configurations,
      [metricId]: {
        ...configurations[metricId],
        [paramName]: value,
      },
    };
    setConfigurations(newConfigurations);
    onMetricsChange(selectedMetrics, newConfigurations);
  };

  const MetricCard = ({ metric }: { metric: MetricConfig }) => {
    const isSelected = selectedMetrics.includes(metric.id);
    const isRecommended = recommendedMetrics.includes(metric.id);
    const isExpanded = expandedMetric === metric.id;
    const typeInfo = METRIC_TYPE_INFO[metric.type];

    return (
      <div
        className={cn(
          "border rounded-xl p-6 transition-all duration-200",
          isSelected
            ? "border-facebook-blue bg-facebook-blue/5"
            : "border-gray-300 hover:border-gray-400"
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start space-x-3">
            <button
              onClick={() => handleMetricToggle(metric.id)}
              className={cn(
                "w-6 h-6 rounded-full border-2 flex items-center justify-center mt-1 transition-colors",
                isSelected
                  ? "border-facebook-blue bg-facebook-blue"
                  : "border-gray-300 hover:border-facebook-blue"
              )}
            >
              {isSelected && <Check className="w-3 h-3 text-white" />}
            </button>

            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-2">
                {metric.icon}
                <h3 className="font-semibold text-lg text-gray-900">
                  {metric.name}
                </h3>
                {isRecommended && (
                  <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                    Recommended
                  </span>
                )}
                <span
                  className={cn(
                    "text-xs px-2 py-1 rounded-full",
                    typeInfo.color
                  )}
                >
                  {typeInfo.name}
                </span>
              </div>
              <p className="text-gray-600 text-sm">{metric.description}</p>
            </div>
          </div>

          <button
            onClick={() => setExpandedMetric(isExpanded ? null : metric.id)}
            className="text-gray-400 hover:text-gray-600"
          >
            <HelpCircle className="w-5 h-5" />
          </button>
        </div>

        {/* Expanded Details */}
        {isExpanded && (
          <div className="space-y-4 border-t pt-4">
            {/* Examples */}
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Examples</h4>
              <div className="space-y-2">
                {metric.examples.map((example, index) => (
                  <div
                    key={index}
                    className="bg-gray-50 p-3 rounded-lg text-sm"
                  >
                    <div className="font-medium text-gray-700 mb-1">
                      Input: {example.input}
                    </div>
                    <div className="text-gray-600 mb-1">
                      Output: {example.output}
                    </div>
                    <div className="text-green-600 font-medium">
                      Score: {example.score}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Pros and Cons */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-green-800 mb-2">
                  ✓ Advantages
                </h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {metric.pros.map((pro, index) => (
                    <li key={index}>• {pro}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-red-800 mb-2">⚠ Limitations</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {metric.cons.map((con, index) => (
                    <li key={index}>• {con}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Data Requirements */}
            <div>
              <h4 className="font-medium text-gray-900 mb-2">
                Data Requirements
              </h4>
              <ul className="text-sm text-gray-600 space-y-1">
                {metric.dataRequirements.map((req, index) => (
                  <li key={index}>• {req}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Parameters Configuration */}
        {isSelected && metric.parameters && (
          <div className="mt-4 pt-4 border-t">
            <h4 className="font-medium text-gray-900 mb-3 flex items-center">
              <Settings className="w-4 h-4 mr-2" />
              Configuration
            </h4>
            <div className="space-y-3">
              {Object.entries(metric.parameters).map(([paramName, param]) => (
                <div key={paramName}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {paramName
                      .replace(/_/g, " ")
                      .replace(/\b\w/g, (l) => l.toUpperCase())}
                  </label>
                  <p className="text-xs text-gray-500 mb-2">
                    {param.description}
                  </p>

                  {param.type === "boolean" ? (
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={
                          configurations[metric.id]?.[paramName] ??
                          param.default
                        }
                        onChange={(e) =>
                          handleParameterChange(
                            metric.id,
                            paramName,
                            e.target.checked
                          )
                        }
                        className="rounded border-gray-300 text-facebook-blue focus:ring-facebook-blue"
                      />
                      <span className="ml-2 text-sm text-gray-600">
                        {configurations[metric.id]?.[paramName] ?? param.default
                          ? "Enabled"
                          : "Disabled"}
                      </span>
                    </label>
                  ) : param.type === "select" ? (
                    <select
                      value={
                        configurations[metric.id]?.[paramName] ?? param.default
                      }
                      onChange={(e) =>
                        handleParameterChange(
                          metric.id,
                          paramName,
                          e.target.value
                        )
                      }
                      className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-facebook-blue focus:border-transparent"
                    >
                      {param.options?.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  ) : param.type === "array" ? (
                    <ArrayInput
                      value={
                        configurations[metric.id]?.[paramName] ?? param.default
                      }
                      onChange={(value) =>
                        handleParameterChange(metric.id, paramName, value)
                      }
                      arrayType={param.arrayType || "string"}
                      placeholder={`Enter ${
                        param.arrayType || "string"
                      } values (comma-separated)`}
                    />
                  ) : param.type === "fieldMapping" ? (
                    <FieldMappingInput
                      value={
                        configurations[metric.id]?.[paramName] ?? param.default
                      }
                      onChange={(value) =>
                        handleParameterChange(metric.id, paramName, value)
                      }
                      placeholder="field_name: weight (e.g., urgency: 2.0, sentiment: 1.5)"
                    />
                  ) : (
                    <input
                      type={param.type === "number" ? "number" : "text"}
                      value={
                        configurations[metric.id]?.[paramName] ?? param.default
                      }
                      onChange={(e) =>
                        handleParameterChange(
                          metric.id,
                          paramName,
                          param.type === "number"
                            ? parseFloat(e.target.value)
                            : e.target.value
                        )
                      }
                      className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-facebook-blue focus:border-transparent"
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Success Metrics
        </h2>
        <p className="text-gray-600">
          Choose how to evaluate your optimized prompt's performance
        </p>
      </div>

      {/* Smart Recommendations */}
      {recommendedMetrics.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <div className="flex items-center mb-3">
            <BarChart3 className="w-5 h-5 text-blue-600 mr-2" />
            <h3 className="font-semibold text-blue-900">
              Smart Recommendations
            </h3>
          </div>
          <p className="text-blue-800 text-sm mb-3">
            Based on your {useCase} use case and field mappings, we recommend:
          </p>
          <div className="flex flex-wrap gap-2">
            {recommendedMetrics.map((metricId) => {
              const metric = AVAILABLE_METRICS.find((m) => m.id === metricId);
              return metric ? (
                <button
                  key={metricId}
                  onClick={() => handleMetricToggle(metricId)}
                  className={cn(
                    "px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    selectedMetrics.includes(metricId)
                      ? "bg-blue-600 text-white"
                      : "bg-blue-100 text-blue-800 hover:bg-blue-200"
                  )}
                >
                  {metric.name}
                </button>
              ) : null;
            })}
          </div>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="space-y-4">
        {availableMetrics.map((metric) => (
          <MetricCard key={metric.id} metric={metric} />
        ))}
      </div>

      {/* Selected Summary */}
      {selectedMetrics.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-6">
          <h3 className="font-semibold text-green-900 mb-3">
            Selected Metrics Summary
          </h3>
          <div className="space-y-2">
            {selectedMetrics.map((metricId) => {
              const metric = AVAILABLE_METRICS.find((m) => m.id === metricId);
              return metric ? (
                <div
                  key={metricId}
                  className="flex items-center text-sm text-green-800"
                >
                  <Check className="w-4 h-4 mr-2" />
                  <span className="font-medium">{metric.name}</span>
                  <span className="text-green-600 ml-2">
                    - {metric.description}
                  </span>
                </div>
              ) : null;
            })}
          </div>
        </div>
      )}
    </div>
  );
};
