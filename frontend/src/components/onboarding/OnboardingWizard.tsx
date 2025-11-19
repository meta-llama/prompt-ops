import React, { useState } from "react";
import {
  ArrowLeft,
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
  Clock,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { StepIndicator } from "./StepIndicator";
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
  const [currentStep, setCurrentStep] = useState(0);
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

  const steps = [
    {
      id: "requirements",
      title: "What you need",
      description: "Before you begin",
    },
    { id: "prompt", title: "Your Prompt", description: "What to optimize" },
    { id: "usecase", title: "Use Case", description: "Type of application" },
    { id: "dataset", title: "Dataset", description: "Upload your data" },
    {
      id: "fieldmapping",
      title: "Field Mapping",
      description: "Map your fields",
    },
    {
      id: "metrics",
      title: "Success Metrics",
      description: "How to measure success",
    },
    {
      id: "models",
      title: "AI Models",
      description: "Select inference providers",
    },
    {
      id: "optimizer",
      title: "Optimizer",
      description: "Choose optimization strategy",
    },
    { id: "review", title: "Review & Optimize", description: "Final review" },
  ];

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

  // Helper functions for dynamic button behavior
  const getNextButtonText = () => {
    if (currentStep === 7) { // Optimizer step
      return "Create Configuration";
    }
    return "Next";
  };

  const getNextButtonIcon = () => {
    if (currentStep === 7) { // Optimizer step
      return <Settings className="w-4 h-4" />; // Configuration icon
    }
    return <ArrowRight className="w-4 h-4" />; // Arrow icon
  };

  // Generate dynamic project name
  const generateProjectName = () => {
    const timestamp = new Date().toISOString().slice(0, 10);
    const useCase = formData.useCase || 'custom';
    return `${useCase}-project-${timestamp}`;
  };

  const handleNext = async () => {
    // Special handling for optimizer step (step 7) -> review step (step 8)
    if (currentStep === 7) {
      await handleCreateProjectAndNext();
    } else if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleCreateProjectAndNext = async () => {
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
      const response = await fetch("http://localhost:8000/create-project", {
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
        // Move to review step to show results
        setCurrentStep(currentStep + 1);
      } else {
        throw new Error(result.error || "Failed to create project");
      }

    } catch (error) {
      console.error("Error creating project:", error);
      // Still proceed to review step but show error
      setProjectCreationResult({
        success: false,
        error: error.message || "Failed to create project"
      });
      setCurrentStep(currentStep + 1);
    } finally {
      setCreatingProject(false);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
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
    const ws = new WebSocket(`ws://localhost:8000/ws/optimize/${projectCreationResult.actualProjectName}`);
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

  const isStepValid = () => {
    switch (currentStep) {
      case 0:
        return true; // Requirements step
      case 1:
        return formData.prompt.trim() !== ""; // Prompt step
      case 2:
        return formData.useCase !== ""; // Use case step
      case 3:
        return formData.datasetPath !== ""; // Dataset upload step
      case 4: // Field mapping step
        if (formData.useCase === "custom") return true;
        const requirements =
          formData.useCase === "qa"
            ? ["question", "answer"]
            : ["context", "query", "answer"];
        return requirements.every((field) => formData.fieldMappings[field]);
      case 5:
        return formData.metrics.length > 0; // Metrics step - require at least one metric
      case 6:
        return (
          formData.modelConfigurations.length > 0 &&
          formData.modelConfigurations.every((config) => {
            // At minimum, each config should have a model name
            const hasModel =
              config.model_name && config.model_name.trim() !== "";
            // If provider requires API key, ensure it's provided
            const provider = config.provider_id;
            const needsApiKey = ["openrouter", "together"].includes(provider);
            const hasApiKey =
              !needsApiKey || (config.api_key && config.api_key.trim() !== "");

            // Ensure we have at least one target and one optimizer if multiple configs
            const hasValidRole =
              formData.modelConfigurations.length === 1 ||
              config.role === "both" ||
              (formData.modelConfigurations.some(
                (c) => c.role === "target" || c.role === "both"
              ) &&
                formData.modelConfigurations.some(
                  (c) => c.role === "optimizer" || c.role === "both"
                ));

            return hasModel && hasApiKey && hasValidRole;
          })
        ); // Model configuration step
      case 7:
        return formData.selectedOptimizer !== ""; // Optimizer step
      case 8:
        return true; // Review step - final step
      default:
        return false;
    }
  };

  const handleFileUpload = async (file: File) => {
    setUploadLoading(true);
    setUploadError(null);

    try {
      const formDataObj = new FormData();
      formDataObj.append("file", file);

      const response = await fetch(
        "http://localhost:8000/api/datasets/upload",
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

  const renderRequirementsStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-4xl md:text-5xl font-black text-facebook-text mb-4 tracking-tight">
          What You
          <br />
          <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
            Need
          </span>
        </h2>
        <p className="text-facebook-text/70 text-lg">
          Before we begin, make sure you have these 3 essential items ready:
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white/90 backdrop-blur-xl p-6 rounded-2xl border border-facebook-border shadow-xl">
          <div className="flex flex-col items-center text-center">
            <div className="w-16 h-16 bg-gradient-to-r from-facebook-blue to-facebook-blue-light rounded-full flex items-center justify-center mb-4">
              <FileText className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-bold text-facebook-text mb-2">
              A Prompt
            </h3>
            <p className="text-sm text-facebook-text/70 mb-3">
              Your current prompt or instruction
            </p>
            <p className="text-sm text-facebook-text/60 leading-relaxed">
              The text you want to optimize for better performance. This could
              be a system prompt, user instruction, or any text that guides AI
              behavior. Even rough drafts work - we'll help make them better.
            </p>
          </div>
        </div>

        <div className="bg-white/90 backdrop-blur-xl p-6 rounded-2xl border border-facebook-border shadow-xl">
          <div className="flex flex-col items-center text-center">
            <div className="w-16 h-16 bg-gradient-to-r from-facebook-blue to-facebook-blue-light rounded-full flex items-center justify-center mb-4">
              <Database className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-bold text-facebook-text mb-2">
              A Dataset
            </h3>
            <p className="text-sm text-facebook-text/70 mb-3">
              JSON file with examples
            </p>
            <p className="text-sm text-facebook-text/60 leading-relaxed">
              Evaluation examples to optimize your prompt against. Include
              input-output pairs that represent your real use cases. Quality
              matters more than quantity - 20-50 good examples often work better
              than hundreds of poor ones.
            </p>
          </div>
        </div>

        <div className="bg-white/90 backdrop-blur-xl p-6 rounded-2xl border border-facebook-border shadow-xl">
          <div className="flex flex-col items-center text-center">
            <div className="w-16 h-16 bg-gradient-to-r from-facebook-blue to-facebook-blue-light rounded-full flex items-center justify-center mb-4">
              <Target className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-bold text-facebook-text mb-2">
              Success Metrics
            </h3>
            <p className="text-sm text-facebook-text/70 mb-3">
              How to measure improvement
            </p>
            <p className="text-sm text-facebook-text/60 leading-relaxed">
              Define what makes a good output for your use case. This could be
              accuracy, relevance, tone, format compliance, or custom criteria.
              Clear metrics help us optimize toward your specific goals and
              measure real improvement.
            </p>
          </div>
        </div>
      </div>

      <div className="bg-facebook-blue/10 border border-facebook-blue/20 rounded-2xl p-6 shadow-lg backdrop-blur-xl">
        <div className="flex items-center mb-3">
          <Lightbulb className="w-5 h-5 text-facebook-blue mr-2" />
          <h3 className="font-bold text-facebook-text">Pro Tip</h3>
        </div>
        <p className="text-facebook-text/70 text-sm">
          The more specific your examples and success criteria, the better your
          optimized prompt will be. Start with your real-world use cases and be
          specific about what "good" looks like for your application.
        </p>
      </div>
    </div>
  );

  const renderPromptStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-4xl md:text-5xl font-black text-facebook-text mb-4 tracking-tight">
          Your
          <br />
          <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
            Prompt
          </span>
        </h2>
        <p className="text-facebook-text/70 text-lg">
          Enter the prompt you want to optimize:
        </p>
      </div>

      <div className="bg-white/90 backdrop-blur-xl p-6 rounded-2xl border border-facebook-border shadow-xl">
        <div className="mb-4">
          <label className="block text-sm font-medium text-facebook-text mb-2">
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
          <p className="text-sm font-medium text-facebook-text">
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
                className="text-xs bg-facebook-blue/10 hover:bg-facebook-blue/20 text-facebook-blue px-3 py-1 rounded-full border border-facebook-blue/30 transition-colors duration-200 transform hover:scale-105"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderUseCaseStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-4xl md:text-5xl font-black text-facebook-text mb-4 tracking-tight">
          Use
          <br />
          <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
            Case
          </span>
        </h2>
        <p className="text-facebook-text/70 text-lg">
          Choose the type that best matches your project to get relevant options
          in the next steps.
        </p>
      </div>

      <UseCaseSelector
        selectedUseCase={formData.useCase}
        onSelectUseCase={(useCaseId) => updateFormData("useCase", useCaseId)}
      />
    </div>
  );

  const renderDatasetStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-4xl md:text-5xl font-black text-facebook-text mb-4 tracking-tight">
          Upload Your
          <br />
          <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
            Dataset
          </span>
        </h2>
        <p className="text-facebook-text/70 text-lg">
          Upload a JSON file containing your evaluation examples.
        </p>
      </div>

      <div
        className={`border-2 border-dashed rounded-2xl p-12 text-center shadow-lg transition-all duration-300 ${
          formData.datasetPath
            ? "border-green-400 bg-green-50/80 backdrop-blur-xl"
            : uploadError
            ? "border-red-400 bg-red-50/80 backdrop-blur-xl"
            : "border-facebook-border bg-white/90 backdrop-blur-xl hover:border-facebook-blue hover:shadow-xl"
        }`}
      >
        {uploadLoading ? (
          <div className="space-y-4">
            <div className="w-16 h-16 bg-facebook-blue/10 rounded-full flex items-center justify-center mx-auto">
              <div className="w-8 h-8 border-2 border-facebook-blue border-t-transparent rounded-full animate-spin"></div>
            </div>
            <p className="text-facebook-text">Uploading dataset...</p>
          </div>
        ) : formData.datasetPath ? (
          <div className="space-y-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle className="w-8 h-8 text-green-600" />
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
          <div className="space-y-4">
            <FileText className="w-12 h-12 text-facebook-text/40 mx-auto" />
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
            <p className="text-sm text-facebook-text/60">
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
        <div className="bg-facebook-blue/10 border border-facebook-blue/20 rounded-2xl p-6 shadow-lg backdrop-blur-xl">
          <p className="text-sm font-semibold text-facebook-text mb-3">
            Expected format for {formData.useCase.toUpperCase()}:
          </p>
          <pre className="text-xs bg-white/90 p-4 rounded-xl border border-facebook-border overflow-x-auto text-facebook-text/80">
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
  );

  const renderFieldMappingStep = () => {
    return (
      <FieldMappingInterface
        filename={formData.datasetPath}
        useCase={formData.useCase}
        onMappingUpdate={handleFieldMappingUpdate}
        existingMappings={formData.fieldMappings}
      />
    );
  };

  const handleMetricsChange = (
    selectedMetrics: string[],
    configurations: Record<string, any>
  ) => {
    updateFormData("metrics", selectedMetrics);
    updateFormData("metricConfigurations", configurations);
  };

  const renderMetricsStep = () => (
    <MetricsSelector
      useCase={formData.useCase}
      fieldMappings={formData.fieldMappings}
      selectedMetrics={formData.metrics}
      onMetricsChange={handleMetricsChange}
    />
  );

  const renderModelProviderStep = () => (
    <ModelProviderSelector
      useCase={formData.useCase}
      fieldMappings={formData.fieldMappings}
      onConfigurationChange={(configs) =>
        setFormData((prev) => ({ ...prev, modelConfigurations: configs }))
      }
    />
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

  const renderOptimizerStep = () => (
    <OptimizerSelector
      selectedOptimizer={formData.selectedOptimizer}
      onOptimizerChange={handleOptimizerChange}
      modelCount={formData.modelConfigurations.length}
      useCase={formData.useCase}
    />
  );

  const renderReviewStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-4xl md:text-5xl font-black text-facebook-text mb-4 tracking-tight">
          Review &
          <br />
          <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
            Optimize
          </span>
        </h2>
        <p className="text-facebook-text/70 text-lg">
          Finalize your setup and launch your prompt optimization workflow
        </p>
      </div>

      {/* Project Creation Results */}
      {projectCreationResult && (
        <div className={`p-4 rounded-xl border ${
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

              {/* Show name change notification if project name was modified */}
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
              <div className="bg-white p-3 rounded border">
                <p className="text-sm font-medium text-gray-700 mb-2">Files Created:</p>
                <ul className="text-sm text-gray-600 space-y-1">
                  {Object.entries(projectCreationResult.createdFiles || {}).map(([type, path]) => (
                    <li key={type} className="flex items-center space-x-2">
                      <FileText className="w-3 h-3 text-gray-400" />
                      <span className="font-mono">{String(path)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <p className="text-red-700">{projectCreationResult.error}</p>
          )}
        </div>
      )}

      <div className="bg-white/90 backdrop-blur-xl p-6 rounded-2xl border border-facebook-border shadow-xl space-y-4">
        <div>
          <h3 className="font-bold text-facebook-text mb-3 text-lg">Prompt:</h3>
          <p className="text-facebook-text bg-facebook-white p-4 rounded-xl border border-facebook-border font-medium">
            {formData.prompt}
          </p>
        </div>

        {activeMode === "migrate" && (
          <>
            <div>
              <h3 className="font-bold text-facebook-text mb-3 text-lg">
                Configuration:
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                <div className="bg-facebook-white p-3 rounded-xl border border-facebook-border">
                  <span className="text-facebook-text/70">Use Case:</span>{" "}
                  <span className="font-medium text-facebook-text">
                    {formData.useCase}
                  </span>
                </div>
                <div className="bg-facebook-white p-3 rounded-xl border border-facebook-border">
                  <span className="text-facebook-text/70">Dataset:</span>{" "}
                  <span className="font-medium text-facebook-text">
                    {formData.datasetPath}
                  </span>
                </div>
              </div>
            </div>

            {Object.keys(formData.fieldMappings).length > 0 && (
              <div>
                <h3 className="font-bold text-facebook-text mb-3 text-lg">
                  Field Mappings:
                </h3>
                <div className="bg-white p-4 rounded-xl border border-facebook-border shadow-sm">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {Object.entries(formData.fieldMappings).map(([standardField, datasetField]) => (
                      <div key={standardField} className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-3 bg-facebook-white rounded-lg border border-facebook-border gap-2 sm:gap-0">
                        <div className="flex flex-col">
                          <span className="text-xs text-facebook-text/70 uppercase tracking-wide font-medium">
                            Standard Field
                          </span>
                          <span className="font-medium text-facebook-text capitalize">
                            {standardField}
                          </span>
                        </div>
                        <div className="flex items-center justify-center sm:space-x-2">
                          <ArrowRight className="w-4 h-4 text-facebook-text/50 rotate-90 sm:rotate-0" />
                        </div>
                        <div className="flex flex-col sm:text-right">
                          <span className="text-xs text-facebook-text/70 uppercase tracking-wide font-medium">
                            Dataset Field
                          </span>
                          <span className="font-medium text-facebook-text">
                            {datasetField as string}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {formData.metrics.length > 0 && (
              <div>
                <h3 className="font-bold text-facebook-text mb-3 text-lg">
                  Selected Metrics:
                </h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {formData.metrics.map((metric, index) => (
                    <div
                      key={index}
                      className="bg-white p-4 rounded-xl border border-facebook-border shadow-sm hover:shadow-md transition-shadow duration-200"
                    >
                      <div className="flex items-center space-x-3 mb-3">
                        <div className="p-2 rounded-lg bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark">
                          <Target className="w-4 h-4 text-white" />
                        </div>
                        <div>
                          <h4 className="font-semibold text-facebook-text">
                            {metric}
                          </h4>
                          <p className="text-xs text-facebook-text/60 capitalize">
                            Evaluation Metric
                          </p>
                        </div>
                      </div>
                      {formData.metricConfigurations[metric] && (
                        <div className="bg-facebook-white/50 p-3 rounded-lg border border-facebook-border">
                          <p className="text-xs text-facebook-text/70 uppercase tracking-wide font-medium mb-2">
                            Configuration:
                          </p>
                          <div className="space-y-1">
                            {Object.entries(formData.metricConfigurations[metric] as Record<string, any>).map(([configKey, configValue]) => (
                              <div key={configKey} className="flex justify-between items-center">
                                <span className="text-xs text-facebook-text/70">
                                  {configKey}:
                                </span>
                                <span className="text-xs font-medium text-facebook-text">
                                  {typeof configValue === 'object' ? JSON.stringify(configValue) : String(configValue)}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {formData.modelConfigurations.length > 0 && (
              <div>
                <h3 className="font-bold text-facebook-text mb-3 text-lg">
                  Model Configurations:
                </h3>
                <div className="space-y-4">
                  {formData.modelConfigurations.map((config, index) => (
                    <div
                      key={index}
                      className="bg-white p-4 rounded-xl border border-facebook-border shadow-sm"
                    >
                      {/* Header with provider icon and role badge */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          {getProviderIcon(config.provider_id)}
                          <div>
                            <h4 className="font-semibold text-facebook-text">
                              {getProviderName(
                                config.provider_id,
                                config.custom_provider_name
                              )}
                            </h4>
                            <p className="text-sm text-facebook-text/60">
                              {config.provider_id === "custom"
                                ? "Custom Provider"
                                : "Cloud Provider"}
                            </p>
                          </div>
                        </div>
                        <ReviewRoleBadge role={config.role} />
                      </div>

                      {/* Configuration details */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div className="flex items-center space-x-2">
                          <Brain className="w-4 h-4 text-facebook-text/50" />
                          <div>
                            <p className="text-xs text-facebook-text/70 uppercase tracking-wide font-medium">
                              Model
                            </p>
                            <p className="font-medium text-facebook-text">
                              {config.model_name.split("/").pop() ||
                                config.model_name}
                            </p>
                          </div>
                        </div>

                        {config.api_key && (
                          <div className="flex items-center space-x-2">
                            <Key className="w-4 h-4 text-facebook-text/50" />
                            <div>
                              <p className="text-xs text-facebook-text/70 uppercase tracking-wide font-medium">
                                Authentication
                              </p>
                              <div className="flex items-center space-x-2">
                                <span className="font-medium text-facebook-text font-mono">
                                  ••••••••{config.api_key.slice(-4)}
                                </span>
                                <CheckCircle className="w-4 h-4 text-green-500" />
                              </div>
                            </div>
                          </div>
                        )}

                        {config.api_base && config.provider_id === "custom" && (
                          <div className="flex items-center space-x-2 sm:col-span-2">
                            <Globe className="w-4 h-4 text-facebook-text/50" />
                            <div>
                              <p className="text-xs text-facebook-text/70 uppercase tracking-wide font-medium">
                                Endpoint
                              </p>
                              <p className="font-medium text-facebook-text text-sm truncate">
                                {config.api_base}
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Optimizer Configuration */}
            {formData.selectedOptimizer && (
              <div>
                <h3 className="font-bold text-facebook-text mb-3 text-lg">
                  Optimization Strategy:
                </h3>
                <div className="bg-white p-4 rounded-xl border border-facebook-border shadow-sm">
                  <div className="flex items-center space-x-3 mb-3">
                    {formData.optimizerConfig?.icon}
                    <div>
                      <h4 className="font-semibold text-facebook-text">
                        {formData.optimizerConfig?.name || formData.selectedOptimizer}
                      </h4>
                      <p className="text-sm text-facebook-text/60 capitalize">
                        {formData.optimizerConfig?.category} • {formData.optimizerConfig?.execution_time} execution • {formData.optimizerConfig?.optimization_quality} quality
                      </p>
                    </div>
                  </div>
                  <p className="text-sm text-facebook-text/70 mb-3">
                    {formData.optimizerConfig?.description}
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    <div className="flex items-center space-x-2">
                      <BarChart3 className="w-4 h-4 text-facebook-text/50" />
                      <div>
                        <p className="text-xs text-facebook-text/70 uppercase tracking-wide font-medium">
                          Candidates
                        </p>
                        <p className="font-medium text-facebook-text">
                          {getOptimizerParameters().num_candidates}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Cpu className="w-4 h-4 text-facebook-text/50" />
                      <div>
                        <p className="text-xs text-facebook-text/70 uppercase tracking-wide font-medium">
                          Threads
                        </p>
                        <p className="font-medium text-facebook-text">
                          {getOptimizerParameters().num_threads}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Target className="w-4 h-4 text-facebook-text/50" />
                      <div>
                        <p className="text-xs text-facebook-text/70 uppercase tracking-wide font-medium">
                          Max Demos
                        </p>
                        <p className="font-medium text-facebook-text">
                          {getOptimizerParameters().max_labeled_demos}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Settings className="w-4 h-4 text-facebook-text/50" />
                      <div>
                        <p className="text-xs text-facebook-text/70 uppercase tracking-wide font-medium">
                          Auto Mode
                        </p>
                        <p className="font-medium text-facebook-text capitalize">
                          {getOptimizerParameters().auto_mode}
                        </p>
                      </div>
                    </div>
                    {formData.customOptimizerParams && (
                      <>
                        {formData.customOptimizerParams?.verbose && (
                          <div className="flex items-center space-x-2">
                            <Eye className="w-4 h-4 text-facebook-text/50" />
                            <div>
                              <p className="text-xs text-facebook-text/70 uppercase tracking-wide font-medium">
                                Verbose Mode
                              </p>
                              <p className="font-medium text-facebook-text text-green-600">
                                Enabled
                              </p>
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Optimization Section */}
      {!optimizing && !optimizationResult && (
        <div className="text-center space-y-4">
          <Button
            onClick={handleComplete}
            disabled={!projectCreationResult?.success}
            className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark hover:opacity-90 text-white px-8 py-4 rounded-2xl text-lg font-bold shadow-lg shadow-facebook-blue/25 transform hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Zap className="w-5 h-5 mr-2" />
            Optimize
          </Button>
          {!projectCreationResult?.success && (
            <p className="text-sm text-red-600">Please create a project first by clicking "Create Configuration" on the optimizer step.</p>
          )}
        </div>
      )}

      {/* Optimization Progress */}
      {optimizing && (
        <div className="space-y-6">
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
          <div className="bg-gray-900 rounded-xl p-4 max-h-96 overflow-y-auto">
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
        <div className="space-y-6">
          {optimizationResult.success ? (
            <div className="bg-green-50 border border-green-200 rounded-xl p-6">
              <div className="flex items-center space-x-3 mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
                <h3 className="text-xl font-bold text-green-800">
                  🎉 {optimizationResult.message || "Optimization Complete!"}
                </h3>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Original Prompt */}
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

                {/* Optimized Prompt */}
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
                <p className="text-sm text-blue-800">
                  {optimizationResult.projectName} : {optimizationResult.projectPath}
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
    </div>
  );


  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // Requirements
        return renderRequirementsStep();
      case 1: // Prompt
        return renderPromptStep();
      case 2: // Use case
        return renderUseCaseStep();
      case 3: // Dataset
        return renderDatasetStep();
      case 4: // Field Mapping
        return renderFieldMappingStep();
      case 5: // Metrics
        return renderMetricsStep();
      case 6: // Models
        return renderModelProviderStep();
      case 7: // Optimizer
        return renderOptimizerStep();
      case 8: // Review
        return renderReviewStep();
      default:
        return null;
    }
  };

  return (
    <div className="w-full">
      {/* Progress Indicator */}
      <div className="mb-8">
        <StepIndicator
          steps={steps}
          currentStep={currentStep}
          className="justify-center"
        />
      </div>

      {/* Step Content */}
      <div className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-xl border border-facebook-border p-8">
        {renderStepContent()}
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between mt-6">
        <Button
          onClick={handleBack}
          disabled={currentStep === 0}
          variant="outline"
          className="flex items-center gap-2 border-facebook-border text-facebook-text hover:bg-facebook-white rounded-xl px-6 py-3 font-semibold shadow-md transition-all duration-300"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </Button>

        {currentStep < steps.length - 1 && (
          <Button
            onClick={handleNext}
            disabled={!isStepValid() || creatingProject}
            className="flex items-center gap-2 rounded-xl px-6 py-3 font-bold shadow-lg transition-all duration-300 transform hover:scale-105 bg-facebook-blue hover:bg-facebook-blue-dark text-white shadow-facebook-blue/25"
          >
            {creatingProject ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Creating Project...
              </>
            ) : (
              <>
                {getNextButtonText()}
                {getNextButtonIcon()}
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
};
