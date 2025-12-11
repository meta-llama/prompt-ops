import React, { useState, useRef } from "react";
import {
  ArrowRight,
  CheckCircle,
  FileText,
  Lightbulb,
  Database,
  Target,
  Eye,
  Globe,
  Zap,
  Shield,
  Server,
  Brain,
  Key,
  Settings,
  BarChart3,
  Cpu,
  AlertCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { apiUrl, wsUrl } from "@/lib/config";
import { UseCaseSelector } from "./UseCaseSelector";
import { FieldMappingInterface } from "./FieldMappingInterface";
import { MetricsSelector } from "./MetricsSelector";
import { ModelProviderSelector } from "./ModelProviderSelector";
import { OptimizerSelector } from "./OptimizerSelector";

interface OnboardingWizardProps {
  activeMode: "enhance" | "migrate";
  onComplete: (config: any) => void;
}

export const OnboardingWizard: React.FC<OnboardingWizardProps> = ({
  activeMode,
  onComplete,
}) => {
  const [formData, setFormData] = useState({
    prompt: "",
    useCase: "",
    datasetPath: "",
    uploadedFile: null as File | null,
    fieldMappings: {} as Record<string, string>,
    datasetType: "standard_json",
    metrics: [] as string[],
    metricConfigurations: {} as Record<string, any>,
    modelConfigurations: [] as any[],
    modelProvider: "Llama 3.1 8B", // Keep for backward compatibility
    selectedOptimizer: "basic", // Default optimizer
    optimizerConfig: null as any,
    customOptimizerParams: null as any,
  });

  // Section collapse state
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({});

  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [creatingProject, setCreatingProject] = useState(false);
  const [projectCreationResult, setProjectCreationResult] = useState<any>(null);

  // Optimization streaming state
  const [optimizing, setOptimizing] = useState(false);
  const [optimizationLogs, setOptimizationLogs] = useState<any[]>([]);
  const [optimizationProgress, setOptimizationProgress] = useState({ phase: "", progress: 0, message: "" });
  const [optimizationResult, setOptimizationResult] = useState<any>(null);
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);

  // Refs for scrolling to sections
  const sectionRefs = {
    prompt: useRef<HTMLDivElement>(null),
    usecase: useRef<HTMLDivElement>(null),
    dataset: useRef<HTMLDivElement>(null),
    fieldmapping: useRef<HTMLDivElement>(null),
    metrics: useRef<HTMLDivElement>(null),
    models: useRef<HTMLDivElement>(null),
    optimizer: useRef<HTMLDivElement>(null),
  };

  const toggleSection = (sectionId: string) => {
    setCollapsedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  // Provider icon mapping
  const getProviderIcon = (providerId: string) => {
    switch (providerId) {
      case "openrouter":
        return <Globe className="w-5 h-5 text-blue-600" />;
      case "together":
        return <Zap className="w-5 h-5 text-purple-600" />;
      case "anthropic":
        return <Shield className="w-5 h-5 text-orange-600" />;
      case "openai":
        return <Brain className="w-5 h-5 text-green-600" />;
      case "vllm":
      case "ollama":
        return <Server className="w-5 h-5 text-gray-600" />;
      case "custom":
        return <Server className="w-5 h-5 text-indigo-600" />;
      default:
        return <Globe className="w-5 h-5 text-gray-600" />;
    }
  };

  // Provider name formatting
  const getProviderName = (providerId: string, customName?: string) => {
    if (providerId === "custom" && customName) {
      return customName;
    }

    const names: Record<string, string> = {
      openrouter: "OpenRouter",
      together: "Together AI",
      anthropic: "Anthropic",
      openai: "OpenAI",
      vllm: "vLLM",
      ollama: "Ollama",
      custom: "Custom Provider",
    };

    return names[providerId] || providerId.replace("_", " ");
  };

  // Role badge component for review page
  const ReviewRoleBadge = ({
    role,
  }: {
    role: "target" | "optimizer" | "both";
  }) => {
    const getRoleConfig = (role: string) => {
      switch (role) {
        case "target":
          return {
            icon: <Target className="w-3 h-3" />,
            label: "Target",
            className: "bg-green-100 text-green-800 border-green-200",
          };
        case "optimizer":
          return {
            icon: <Brain className="w-3 h-3" />,
            label: "Optimizer",
            className: "bg-purple-100 text-purple-800 border-purple-200",
          };
        case "both":
          return {
            icon: (
              <div className="flex items-center space-x-0.5">
                <Target className="w-2.5 h-2.5" />
                <Brain className="w-2.5 h-2.5" />
              </div>
            ),
            label: "Target + Optimizer",
            className: "bg-blue-100 text-blue-800 border-blue-200",
          };
        default:
          return {
            icon: <Globe className="w-3 h-3" />,
            label: role,
            className: "bg-gray-100 text-gray-800 border-gray-200",
          };
      }
    };

    const config = getRoleConfig(role);

    return (
      <div
        className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium border ${config.className}`}
      >
        {config.icon}
        <span>{config.label}</span>
      </div>
    );
  };

  // Generate dynamic project name
  const generateProjectName = () => {
    const now = new Date();
    const pad = (n: number) => n.toString().padStart(2, '0');
    const date = `${pad(now.getDate())}${pad(now.getMonth() + 1)}${now.getFullYear().toString().slice(-2)}`;
    const time = `${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
    const useCase = formData.useCase || 'custom';
    return `${useCase}-project-${date}-${time}`;
  };

  const handleCreateProject = async () => {
    setCreatingProject(true);
    setProjectCreationResult(null);

    try {
      // Create the project automatically
      const wizardData = {
        prompt: { text: formData.prompt, inputs: ["question"], outputs: ["answer"] },
        useCase: formData.useCase,
        dataset: {
          path: formData.datasetPath,
          fieldMappings: formData.fieldMappings,
          trainSize: 50,
          validationSize: 20
        },
        models: { selected: formData.modelConfigurations },
        metrics: formData.metrics,
        metricConfigurations: formData.metricConfigurations,
        optimizer: {
          selectedOptimizer: formData.selectedOptimizer,
          customParams: formData.customOptimizerParams
        }
      };

      const projectName = generateProjectName();
      const response = await fetch(apiUrl("/create-project"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          wizardData,
          projectName
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        setProjectCreationResult(result);
      } else {
        throw new Error(result.error || "Failed to create project");
      }

    } catch (error) {
      console.error("Error creating project:", error);
      setProjectCreationResult({
        success: false,
        error: error.message || "Failed to create project"
      });
    } finally {
      setCreatingProject(false);
    }
  };

  const handleComplete = () => {
    // Start optimization via WebSocket
    startOptimization();
  };

  const startOptimization = () => {
    if (!projectCreationResult || !projectCreationResult.actualProjectName) {
      console.error("No project created to optimize");
      return;
    }

    setOptimizing(true);
    setOptimizationLogs([]);
    setOptimizationProgress({ phase: "", progress: 0, message: "" });
    setOptimizationResult(null);

    // Create WebSocket connection
    const ws = new WebSocket(wsUrl(`/ws/optimize/${projectCreationResult.actualProjectName}`));
    setWebsocket(ws);

    ws.onopen = () => {
      console.log("WebSocket connected for optimization");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case "status":
          setOptimizationProgress(prev => ({
            ...prev,
            phase: data.phase,
            message: data.message
          }));
          break;

        case "progress":
          setOptimizationProgress({
            phase: data.phase,
            progress: data.progress,
            message: data.message
          });
          break;

        case "log":
          setOptimizationLogs(prev => [...prev, {
            id: Date.now() + Math.random(),
            level: data.level,
            logger: data.logger,
            message: data.message,
            timestamp: data.timestamp
          }]);
          break;

        case "complete":
          setOptimizationResult(data);
          setOptimizing(false);
          ws.close();
          break;

        case "error":
          setOptimizationResult({
            success: false,
            error: data.message
          });
          setOptimizing(false);
          ws.close();
          break;
      }
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed");
      setWebsocket(null);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setOptimizationResult({
        success: false,
        error: "WebSocket connection failed"
      });
      setOptimizing(false);
      setWebsocket(null);
    };
  };

  // Cleanup WebSocket on component unmount
  React.useEffect(() => {
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [websocket]);


  const updateFormData = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // Form validation
  const isFormValid = () => {
    // Check prompt
    if (formData.prompt.trim() === "") return false;

    // Check use case
    if (formData.useCase === "") return false;

    // Check dataset
    if (formData.datasetPath === "") return false;

    // Check field mappings
    if (formData.useCase !== "custom") {
      const requirements =
        formData.useCase === "qa"
          ? ["question", "answer"]
          : ["context", "query", "answer"];
      if (!requirements.every((field) => formData.fieldMappings[field])) return false;
    }

    // Check metrics
    if (formData.metrics.length === 0) return false;

    // Check model configurations
    if (formData.modelConfigurations.length === 0) return false;
    const modelsValid = formData.modelConfigurations.every((config) => {
      const hasModel = config.model_name && config.model_name.trim() !== "";
      const provider = config.provider_id;
      const needsApiKey = ["openrouter", "together"].includes(provider);
      const hasApiKey = !needsApiKey || (config.api_key && config.api_key.trim() !== "");
      const hasValidRole =
        formData.modelConfigurations.length === 1 ||
        config.role === "both" ||
        (formData.modelConfigurations.some((c) => c.role === "target" || c.role === "both") &&
          formData.modelConfigurations.some((c) => c.role === "optimizer" || c.role === "both"));
      return hasModel && hasApiKey && hasValidRole;
    });
    if (!modelsValid) return false;

    // Check optimizer
    if (formData.selectedOptimizer === "") return false;

    return true;
  };

  // Section completion status
  const getSectionStatus = (sectionId: string): 'complete' | 'incomplete' | 'empty' => {
    switch (sectionId) {
      case 'prompt':
        return formData.prompt.trim() !== "" ? 'complete' : 'empty';
      case 'usecase':
        return formData.useCase !== "" ? 'complete' : 'empty';
      case 'dataset':
        return formData.datasetPath !== "" ? 'complete' : 'empty';
      case 'fieldmapping':
        if (formData.useCase === "custom") return 'complete';
        if (formData.datasetPath === "") return 'empty';
        const requirements = formData.useCase === "qa" ? ["question", "answer"] : ["context", "query", "answer"];
        return requirements.every((field) => formData.fieldMappings[field]) ? 'complete' : 'incomplete';
      case 'metrics':
        return formData.metrics.length > 0 ? 'complete' : 'empty';
      case 'models':
        if (formData.modelConfigurations.length === 0) return 'empty';
        const modelsValid = formData.modelConfigurations.every((config) => {
          const hasModel = config.model_name && config.model_name.trim() !== "";
          const provider = config.provider_id;
          const needsApiKey = ["openrouter", "together"].includes(provider);
          const hasApiKey = !needsApiKey || (config.api_key && config.api_key.trim() !== "");
          return hasModel && hasApiKey;
        });
        return modelsValid ? 'complete' : 'incomplete';
      case 'optimizer':
        return formData.selectedOptimizer !== "" ? 'complete' : 'empty';
      default:
        return 'empty';
    }
  };

  const handleFileUpload = async (file: File) => {
    setUploadLoading(true);
    setUploadError(null);

    try {
      const formDataObj = new FormData();
      formDataObj.append("file", file);

      const response = await fetch(
        apiUrl("/api/datasets/upload"),
        {
          method: "POST",
          body: formDataObj,
        }
      );

      if (!response.ok) {
        throw new Error("Failed to upload dataset");
      }

      const data = await response.json();

      updateFormData("datasetPath", data.filename);
      updateFormData("uploadedFile", file);

      console.log("Dataset uploaded successfully:", data);
    } catch (error) {
      console.error("Error uploading dataset:", error);
      setUploadError(
        error instanceof Error ? error.message : "Failed to upload dataset"
      );
    } finally {
      setUploadLoading(false);
    }
  };

  const handleFieldMappingUpdate = (mappings: Record<string, string>) => {
    updateFormData("fieldMappings", mappings);
  };

  // Section header component
  const SectionHeader = ({
    id,
    title,
    icon: Icon,
    status
  }: {
    id: string;
    title: string;
    icon: any;
    status: 'complete' | 'incomplete' | 'empty';
  }) => (
    <button
      onClick={() => toggleSection(id)}
      className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-facebook-blue/5 to-facebook-blue-light/5 rounded-xl border border-facebook-border hover:border-facebook-blue/30 transition-all duration-200"
    >
      <div className="flex items-center space-x-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
          status === 'complete'
            ? 'bg-green-100 text-green-600'
            : status === 'incomplete'
            ? 'bg-yellow-100 text-yellow-600'
            : 'bg-facebook-blue/10 text-facebook-blue'
        }`}>
          {status === 'complete' ? <CheckCircle className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
        </div>
        <h3 className="text-lg font-bold text-facebook-text">{title}</h3>
        {status === 'complete' && (
          <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
            Complete
          </span>
        )}
        {status === 'incomplete' && (
          <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full font-medium">
            In Progress
          </span>
        )}
      </div>
      {collapsedSections[id] ? (
        <ChevronDown className="w-5 h-5 text-facebook-text/50" />
      ) : (
        <ChevronUp className="w-5 h-5 text-facebook-text/50" />
      )}
    </button>
  );

  const renderRequirementsHeader = () => (
    <div className="text-center mb-8 pt-4">
      <h1 className="text-4xl md:text-5xl font-black text-facebook-text mb-4 tracking-tight">
        Prompt
        <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
          {" "}Optimization
        </span>
      </h1>
      <p className="text-facebook-text/70 text-lg max-w-2xl mx-auto">
        Complete the form below to configure and optimize your prompt. Fill out each section, then click "Create & Optimize" at the bottom.
      </p>

      {/* Quick requirements reminder */}
      <div className="flex flex-wrap justify-center gap-4 mt-6">
        <div className="flex items-center space-x-2 bg-facebook-blue/10 px-4 py-2 rounded-full">
          <FileText className="w-4 h-4 text-facebook-blue" />
          <span className="text-sm text-facebook-text/80">Your Prompt</span>
        </div>
        <div className="flex items-center space-x-2 bg-facebook-blue/10 px-4 py-2 rounded-full">
          <Database className="w-4 h-4 text-facebook-blue" />
          <span className="text-sm text-facebook-text/80">Dataset (JSON)</span>
        </div>
        <div className="flex items-center space-x-2 bg-facebook-blue/10 px-4 py-2 rounded-full">
          <Target className="w-4 h-4 text-facebook-blue" />
          <span className="text-sm text-facebook-text/80">Success Metrics</span>
        </div>
      </div>
    </div>
  );

  const renderPromptSection = () => (
    <div ref={sectionRefs.prompt} className="space-y-4">
      <SectionHeader id="prompt" title="1. Your Prompt" icon={FileText} status={getSectionStatus('prompt')} />

      {!collapsedSections.prompt && (
        <div className="pl-4 space-y-4">
          <p className="text-facebook-text/70 text-sm">
            Enter the prompt you want to optimize. This is the instruction or system prompt that guides AI behavior.
          </p>

          <div className="space-y-3">
            <label className="block text-sm font-medium text-facebook-text">
              Current Prompt
            </label>
            <textarea
              value={formData.prompt}
              onChange={(e) => updateFormData("prompt", e.target.value)}
              placeholder="Enter your prompt here..."
              className="w-full h-32 p-4 border border-facebook-border rounded-xl focus:ring-2 focus:ring-facebook-blue focus:border-transparent resize-none bg-facebook-white/50 text-facebook-text placeholder-facebook-text/50"
            />
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium text-facebook-text/70">
              Quick Examples:
            </p>
            <div className="flex flex-wrap gap-2">
              {[
                "Analyze the sentiment of this text:",
                "Summarize this document in 3 bullet points:",
                "Answer this question based on the context:",
                "Classify this text into categories:",
              ].map((example) => (
                <button
                  key={example}
                  onClick={() => updateFormData("prompt", example)}
                  className="text-xs bg-facebook-blue/10 hover:bg-facebook-blue/20 text-facebook-blue px-3 py-1.5 rounded-full border border-facebook-blue/30 transition-colors duration-200"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderUseCaseSection = () => (
    <div ref={sectionRefs.usecase} className="space-y-4">
      <SectionHeader id="usecase" title="2. Use Case" icon={Lightbulb} status={getSectionStatus('usecase')} />

      {!collapsedSections.usecase && (
        <div className="pl-4 space-y-4">
          <p className="text-facebook-text/70 text-sm">
            Choose the type that best matches your project to get relevant options for field mapping and metrics.
          </p>

          <UseCaseSelector
            selectedUseCase={formData.useCase}
            onSelectUseCase={(useCaseId) => updateFormData("useCase", useCaseId)}
          />
        </div>
      )}
    </div>
  );

  const renderDatasetSection = () => (
    <div ref={sectionRefs.dataset} className="space-y-4">
      <SectionHeader id="dataset" title="3. Dataset" icon={Database} status={getSectionStatus('dataset')} />

      {!collapsedSections.dataset && (
        <div className="pl-4 space-y-4">
          <p className="text-facebook-text/70 text-sm">
            Upload a JSON file containing your evaluation examples.
          </p>

          <div
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${
              formData.datasetPath
                ? "border-green-400 bg-green-50/80"
                : uploadError
                ? "border-red-400 bg-red-50/80"
                : "border-facebook-border bg-white/50 hover:border-facebook-blue"
            }`}
          >
            {uploadLoading ? (
              <div className="space-y-3">
                <div className="w-12 h-12 bg-facebook-blue/10 rounded-full flex items-center justify-center mx-auto">
                  <div className="w-6 h-6 border-2 border-facebook-blue border-t-transparent rounded-full animate-spin"></div>
                </div>
                <p className="text-facebook-text">Uploading dataset...</p>
              </div>
            ) : formData.datasetPath ? (
              <div className="space-y-3">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <p className="font-semibold text-facebook-text">
                    {formData.datasetPath}
                  </p>
                  <p className="text-sm text-facebook-text/70">
                    {formData.uploadedFile
                      ? (formData.uploadedFile.size / 1024).toFixed(2)
                      : "0"}{" "}
                    KB
                  </p>
                </div>
                <button
                  onClick={() => {
                    updateFormData("datasetPath", "");
                    updateFormData("uploadedFile", null);
                    setUploadError(null);
                  }}
                  className="text-sm text-red-600 hover:underline"
                >
                  Remove file
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <Database className="w-10 h-10 text-facebook-text/40 mx-auto" />
                <div>
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <span className="text-facebook-blue hover:underline font-semibold">
                      Click to upload
                    </span>
                    <span className="text-facebook-text/70"> or drag and drop</span>
                  </label>
                  <input
                    id="file-upload"
                    type="file"
                    accept=".json"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        handleFileUpload(file);
                      }
                    }}
                  />
                </div>
                <p className="text-xs text-facebook-text/60">
                  JSON files only, max 10MB
                </p>
                {uploadError && (
                  <p className="text-sm text-red-600 bg-red-50 p-2 rounded">
                    {uploadError}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Dataset format helper */}
          {formData.useCase && formData.useCase !== "custom" && (
            <div className="bg-facebook-blue/5 border border-facebook-blue/20 rounded-xl p-4">
              <p className="text-xs font-semibold text-facebook-text mb-2">
                Expected format for {formData.useCase.toUpperCase()}:
              </p>
              <pre className="text-xs bg-white/90 p-3 rounded-lg border border-facebook-border overflow-x-auto text-facebook-text/80">
                {formData.useCase === "qa"
                  ? JSON.stringify(
                      [
                        {
                          question: "What is the capital of France?",
                          answer: "Paris",
                        },
                      ],
                      null,
                      2
                    )
                  : JSON.stringify(
                      [
                        {
                          query: "What are the key terms in this contract?",
                          context: [
                            "Document 1 content text...",
                            "Document 2 content text...",
                          ],
                          answer: "The key terms include...",
                        },
                      ],
                      null,
                      2
                    )}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderFieldMappingSection = () => (
    <div ref={sectionRefs.fieldmapping} className="space-y-4">
      <SectionHeader id="fieldmapping" title="4. Field Mapping" icon={ArrowRight} status={getSectionStatus('fieldmapping')} />

      {!collapsedSections.fieldmapping && (
        <div className="pl-4 space-y-4">
          {formData.datasetPath ? (
            <FieldMappingInterface
              filename={formData.datasetPath}
              useCase={formData.useCase}
              onMappingUpdate={handleFieldMappingUpdate}
              existingMappings={formData.fieldMappings}
            />
          ) : (
            <div className="text-center py-8 text-facebook-text/50">
              <ArrowRight className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>Upload a dataset first to configure field mappings</p>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const handleMetricsChange = (
    selectedMetrics: string[],
    configurations: Record<string, any>
  ) => {
    updateFormData("metrics", selectedMetrics);
    updateFormData("metricConfigurations", configurations);
  };

  const renderMetricsSection = () => (
    <div ref={sectionRefs.metrics} className="space-y-4">
      <SectionHeader id="metrics" title="5. Success Metrics" icon={Target} status={getSectionStatus('metrics')} />

      {!collapsedSections.metrics && (
        <div className="pl-4 space-y-4">
          <MetricsSelector
            useCase={formData.useCase}
            fieldMappings={formData.fieldMappings}
            selectedMetrics={formData.metrics}
            onMetricsChange={handleMetricsChange}
          />
        </div>
      )}
    </div>
  );

  const renderModelsSection = () => (
    <div ref={sectionRefs.models} className="space-y-4">
      <SectionHeader id="models" title="6. AI Models" icon={Brain} status={getSectionStatus('models')} />

      {!collapsedSections.models && (
        <div className="pl-4 space-y-4">
          <ModelProviderSelector
            useCase={formData.useCase}
            fieldMappings={formData.fieldMappings}
            onConfigurationChange={(configs) =>
              setFormData((prev) => ({ ...prev, modelConfigurations: configs }))
            }
          />
        </div>
      )}
    </div>
  );

  const handleOptimizerChange = (optimizer: string, config: any, customParams?: any) => {
    updateFormData("selectedOptimizer", optimizer);
    updateFormData("optimizerConfig", config);
    if (customParams) {
      // Store custom parameters separately if needed
      updateFormData("customOptimizerParams", customParams);
    }
  };

  // Helper function to get optimizer parameters with fallbacks
  const getOptimizerParameters = () => {
    // First try to get from saved config
    if (formData.optimizerConfig?.parameters) {
      return formData.optimizerConfig.parameters;
    }

    // Fallback to default parameters based on selected optimizer
    const defaultParams = {
      basic: {
        num_candidates: 10,
        num_threads: 18,
        max_labeled_demos: 5,
        auto_mode: "basic"
      },
      llama: {
        num_candidates: 10,
        num_threads: 18,
        max_labeled_demos: 5,
        auto_mode: "intermediate"
      }
    };

    // Return parameters based on selected optimizer, fallback to basic if none selected
    const selectedOptimizer = formData.selectedOptimizer || "basic";
    return defaultParams[selectedOptimizer as keyof typeof defaultParams] || defaultParams.basic;
  };

  const renderOptimizerSection = () => (
    <div ref={sectionRefs.optimizer} className="space-y-4">
      <SectionHeader id="optimizer" title="7. Optimizer" icon={Zap} status={getSectionStatus('optimizer')} />

      {!collapsedSections.optimizer && (
        <div className="pl-4 space-y-4">
          <OptimizerSelector
            selectedOptimizer={formData.selectedOptimizer}
            onOptimizerChange={handleOptimizerChange}
            modelCount={formData.modelConfigurations.length}
            useCase={formData.useCase}
          />
        </div>
      )}
    </div>
  );

  return (
    <div className="w-full">
      {/* Main Form Container */}
      <div className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-xl border border-facebook-border p-6 md:p-8">
        {/* Header */}
        {renderRequirementsHeader()}

        {/* All Form Sections */}
        <div className="space-y-6">
          {renderPromptSection()}
          {renderUseCaseSection()}
          {renderDatasetSection()}
          {renderFieldMappingSection()}
          {renderMetricsSection()}
          {renderModelsSection()}
          {renderOptimizerSection()}
        </div>

        {/* Action Section */}
        <div className="mt-10 pt-8 border-t border-facebook-border">
          {/* Form Validation Summary */}
          {!isFormValid() && !projectCreationResult && (
            <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-xl">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium text-yellow-800">Complete all sections to continue</p>
                  <ul className="mt-2 text-sm text-yellow-700 space-y-1">
                    {formData.prompt.trim() === "" && <li>• Enter your prompt</li>}
                    {formData.useCase === "" && <li>• Select a use case</li>}
                    {formData.datasetPath === "" && <li>• Upload a dataset</li>}
                    {formData.useCase !== "custom" && formData.datasetPath !== "" && !(() => {
                      const reqs = formData.useCase === "qa" ? ["question", "answer"] : ["context", "query", "answer"];
                      return reqs.every(f => formData.fieldMappings[f]);
                    })() && <li>• Complete field mappings</li>}
                    {formData.metrics.length === 0 && <li>• Select at least one metric</li>}
                    {formData.modelConfigurations.length === 0 && <li>• Configure at least one model</li>}
                    {formData.selectedOptimizer === "" && <li>• Select an optimizer</li>}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Project Creation Results */}
          {projectCreationResult && (
            <div className={`mb-6 p-4 rounded-xl border ${
              projectCreationResult.success
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}>
              <div className="flex items-center space-x-3 mb-3">
                {projectCreationResult.success ? (
                  <CheckCircle className="w-6 h-6 text-green-600" />
                ) : (
                  <AlertCircle className="w-6 h-6 text-red-600" />
                )}
                <h3 className="font-bold text-lg">
                  {projectCreationResult.success ? 'Project Created Successfully!' : 'Project Creation Failed'}
                </h3>
              </div>

              {projectCreationResult.success ? (
                <div className="space-y-3">
                  <p className="text-green-700">{projectCreationResult.message}</p>

                  {projectCreationResult.actualProjectName !== projectCreationResult.requestedProjectName && (
                    <div className="bg-blue-50 p-3 rounded border border-blue-200">
                      <p className="text-sm font-medium text-blue-800 mb-1">Project Name Updated:</p>
                      <p className="text-sm text-blue-700">
                        A project with the name "{projectCreationResult.requestedProjectName}" already existed,
                        so your project was created as "{projectCreationResult.actualProjectName}" instead.
                      </p>
                    </div>
                  )}

                  <div className="bg-white p-3 rounded border">
                    <p className="text-sm font-medium text-gray-700 mb-1">Project Location:</p>
                    <p className="text-sm font-mono text-gray-600 bg-gray-50 p-2 rounded">
                      {projectCreationResult.projectPath}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-red-700">{projectCreationResult.error}</p>
              )}
            </div>
          )}

          {/* Optimization Progress */}
          {optimizing && (
            <div className="mb-6 space-y-4">
              <div className="text-center">
                <h3 className="text-xl font-bold text-facebook-text mb-2">
                  🚀 Optimizing Your Prompt...
                </h3>
                <p className="text-facebook-text/70">
                  This may take a few minutes. Real-time progress is shown below.
                </p>
              </div>

              {/* Progress Bar */}
              <div className="bg-white p-4 rounded-xl border border-facebook-border shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-facebook-text">
                    {optimizationProgress.phase || "Initializing..."}
                  </span>
                  <span className="text-sm text-facebook-text/70">
                    {Math.round(optimizationProgress.progress)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-facebook-blue h-2 rounded-full transition-all duration-300"
                    style={{ width: `${optimizationProgress.progress}%` }}
                  ></div>
                </div>
                <p className="text-sm text-facebook-text/70 mt-2">
                  {optimizationProgress.message}
                </p>
              </div>

              {/* Live Logs */}
              <div className="bg-gray-900 rounded-xl p-4 max-h-64 overflow-y-auto">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-white font-medium">Live Optimization Logs</h4>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="text-green-400 text-sm">Live</span>
                  </div>
                </div>
                <div className="space-y-1 font-mono text-sm">
                  {optimizationLogs.map((log) => (
                    <div
                      key={log.id}
                      className={`${
                        log.level === "ERROR"
                          ? "text-red-400"
                          : log.level === "WARNING"
                          ? "text-yellow-400"
                          : log.level === "INFO"
                          ? "text-blue-400"
                          : "text-gray-300"
                      }`}
                    >
                      {log.message}
                    </div>
                  ))}
                  {optimizationLogs.length === 0 && (
                    <div className="text-gray-500 italic">Waiting for logs...</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Optimization Results */}
          {optimizationResult && (
            <div className="mb-6">
              {optimizationResult.success ? (
                <div className="bg-green-50 border border-green-200 rounded-xl p-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <CheckCircle className="w-8 h-8 text-green-600" />
                    <h3 className="text-xl font-bold text-green-800">
                      🎉 {optimizationResult.message || "Optimization Complete!"}
                    </h3>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-white rounded-lg p-4 border border-green-200">
                      <h4 className="font-semibold text-gray-800 mb-2 flex items-center">
                        <FileText className="w-4 h-4 mr-2" />
                        Original Prompt
                      </h4>
                      <div className="bg-gray-50 rounded p-3 max-h-48 overflow-y-auto">
                        <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                          {optimizationResult.originalPrompt || "No original prompt"}
                        </pre>
                      </div>
                    </div>

                    <div className="bg-white rounded-lg p-4 border border-green-200">
                      <h4 className="font-semibold text-gray-800 mb-2 flex items-center">
                        <Zap className="w-4 h-4 mr-2 text-green-600" />
                        Optimized Prompt
                      </h4>
                      <div className="bg-green-50 rounded p-3 max-h-48 overflow-y-auto">
                        <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                          {optimizationResult.optimizedPrompt}
                        </pre>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-sm text-blue-800">
                      <strong>Next Steps:</strong> Your optimized prompt has been saved to the project directory.
                      You can now use this improved prompt in your applications!
                    </p>
                  </div>
                </div>
              ) : (
                <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                  <div className="flex items-center space-x-3 mb-3">
                    <AlertCircle className="w-6 h-6 text-red-600" />
                    <h3 className="font-bold text-red-800">Optimization Failed</h3>
                  </div>
                  <p className="text-red-700">{optimizationResult.error}</p>
                </div>
              )}
            </div>
          )}

          {/* Action Buttons */}
          {!optimizing && !optimizationResult && (
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              {!projectCreationResult?.success ? (
                <Button
                  onClick={handleCreateProject}
                  disabled={!isFormValid() || creatingProject}
                  className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark hover:opacity-90 text-white px-8 py-4 rounded-2xl text-lg font-bold shadow-lg shadow-facebook-blue/25 transform hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                >
                  {creatingProject ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      Creating Project...
                    </>
                  ) : (
                    <>
                      <Settings className="w-5 h-5 mr-2" />
                      Create & Configure Project
                    </>
                  )}
                </Button>
              ) : (
                <Button
                  onClick={handleComplete}
                  className="bg-gradient-to-r from-green-500 to-green-600 hover:opacity-90 text-white px-8 py-4 rounded-2xl text-lg font-bold shadow-lg shadow-green-500/25 transform hover:scale-105 transition-all duration-300"
                >
                  <Zap className="w-5 h-5 mr-2" />
                  Start Optimization
                </Button>
              )}
            </div>
          )}

          {/* Reset button after completion */}
          {optimizationResult && (
            <div className="flex justify-center mt-4">
              <Button
                onClick={() => {
                  setProjectCreationResult(null);
                  setOptimizationResult(null);
                  setOptimizationLogs([]);
                }}
                variant="outline"
                className="border-facebook-border text-facebook-text hover:bg-facebook-white rounded-xl px-6 py-3 font-semibold"
              >
                Start New Optimization
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
