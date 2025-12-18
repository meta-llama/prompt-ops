import React, { useState, useRef, useMemo } from "react";
import {
  ArrowRight,
  CheckCircle,
  FileText,
  Lightbulb,
  Database,
  Target,
  Zap,
  Brain,
  Settings,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
} from "lucide-react";
import { diffWords } from "diff";
import { Button } from "@/components/ui/button";
import { apiUrl, wsUrl } from "@/lib/config";
import { WizardSection } from "@/components/ui/wizard-section";
import { InfoBox } from "@/components/ui/info-box";
import { getProviderIcon, getProviderName } from "@/lib/providers";
import { UseCaseSelector } from "./UseCaseSelector";
import { FieldMappingInterface } from "./FieldMappingInterface";
import { MetricsSelector } from "./MetricsSelector";
import { ModelProviderSelector } from "./ModelProviderSelector";
import { OptimizerSelector } from "./OptimizerSelector";
import { DatasetUploader } from "./DatasetUploader";

// Diff view component for comparing original and optimized prompts
const DiffView: React.FC<{
  original: string;
  optimized: string;
  showOriginal: boolean;
}> = ({ original, optimized, showOriginal }) => {
  const diffResult = useMemo(() => diffWords(original, optimized), [original, optimized]);

  return (
    <div className="whitespace-pre-wrap text-foreground text-sm leading-relaxed">
      {diffResult.map((part, index) => {
        // For the "original" side, show removed parts highlighted, skip added parts
        if (showOriginal) {
          if (part.added) return null;
          if (part.removed) {
            return (
              <span
                key={index}
                className="bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 px-0.5 rounded line-through decoration-red-400"
              >
                {part.value}
              </span>
            );
          }
          return <span key={index}>{part.value}</span>;
        }

        // For the "optimized" side, show added parts highlighted, skip removed parts
        if (part.removed) return null;
        if (part.added) {
          return (
            <span
              key={index}
              className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 px-0.5 rounded"
            >
              {part.value}
            </span>
          );
        }
        return <span key={index}>{part.value}</span>;
      })}
    </div>
  );
};

interface OnboardingWizardProps {
  activeMode: "enhance" | "migrate";
  onComplete: (config: any) => void;
}

// Step definitions
const WIZARD_STEPS = [
  { id: "prompt", title: "Your Prompt", icon: FileText },
  { id: "usecase", title: "Use Case", icon: Lightbulb },
  { id: "dataset", title: "Dataset", icon: Database },
  { id: "fieldmapping", title: "Field Mapping", icon: ArrowRight },
  { id: "metrics", title: "Success Metrics", icon: Target },
  { id: "models", title: "AI Models", icon: Brain },
  { id: "optimizer", title: "Optimizer", icon: Zap },
];

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
    selectedOptimizer: "", // Will be selected by user
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

  // Step navigation
  const goToNextStep = () => {
    if (currentStep < WIZARD_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const goToPreviousStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const goToStep = (stepIndex: number) => {
    setCurrentStep(stepIndex);
  };

  // Check if current step is valid
  const isCurrentStepValid = () => {
    const stepId = WIZARD_STEPS[currentStep].id;
    const status = getSectionStatus(stepId);
    return status === 'complete';
  };

  // Form validation (all steps)
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

  // Render progress stepper
  const renderStepper = () => (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        {WIZARD_STEPS.map((step, index) => {
          const Icon = step.icon;
          const isActive = index === currentStep;
          const isComplete = getSectionStatus(step.id) === 'complete';
          const isAccessible = index <= currentStep || isComplete;

          return (
            <React.Fragment key={step.id}>
              <div className="flex flex-col items-center flex-1">
                <button
                  onClick={() => isAccessible && goToStep(index)}
                  disabled={!isAccessible}
                  className={`w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all ${
                    isComplete
                      ? "bg-meta-teal border-meta-teal text-white"
                      : isActive
                      ? "bg-meta-blue border-meta-blue text-white"
                      : isAccessible
                      ? "border-border bg-panel text-muted-foreground hover:border-meta-blue/50"
                      : "border-border bg-muted text-muted-foreground/50 cursor-not-allowed"
                  }`}
                >
                  {isComplete ? (
                    <CheckCircle className="w-6 h-6" />
                  ) : (
                    <Icon className="w-5 h-5" />
                  )}
                </button>
                <span
                  className={`mt-2 text-xs text-center ${
                    isActive
                      ? "text-foreground font-medium"
                      : isComplete
                      ? "text-meta-teal"
                      : "text-muted-foreground"
                  }`}
                >
                  {step.title}
                </span>
              </div>

              {index < WIZARD_STEPS.length - 1 && (
                <div
                  className={`h-0.5 flex-1 mx-2 mt-[-32px] transition-colors ${
                    getSectionStatus(WIZARD_STEPS[index + 1].id) === 'complete'
                      ? "bg-meta-teal"
                      : "bg-border"
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );

  const renderRequirementsHeader = () => (
    <div className="text-center mb-8 pt-4">
      <h1 className="text-2xl md:text-3xl font-normal text-foreground mb-4 tracking-tight">
        Prompt Optimization Wizard
      </h1>
      <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
        Step {currentStep + 1} of {WIZARD_STEPS.length}: {WIZARD_STEPS[currentStep].title}
      </p>
    </div>
  );

  const renderPromptSection = () => (
    <div>
      <WizardSection
        id="prompt"
        title="Your Prompt"
        icon={<FileText className="w-5 h-5" />}
        status={getSectionStatus('prompt')}
        collapsed={false}
        onToggle={() => {}}
      >
        <p className="text-muted-foreground text-sm">
          Enter the prompt you want to optimize. This is the instruction or system prompt that guides AI behavior.
        </p>

        <div className="space-y-3">
          <label className="block text-sm font-medium text-foreground">
            Current Prompt
          </label>
          <textarea
            value={formData.prompt}
            onChange={(e) => updateFormData("prompt", e.target.value)}
            placeholder="Enter your prompt here..."
            className="w-full h-32 p-4 border border-border rounded-xl focus:ring-2 focus:ring-ring focus:border-transparent resize-none bg-panel text-foreground placeholder:text-muted-foreground"
          />
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">
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
                className="text-xs bg-meta-blue/10 hover:bg-meta-blue/20 text-meta-blue dark:text-meta-blue-light px-3 py-1.5 rounded-full border border-meta-blue/30 dark:border-meta-blue-light/50 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </WizardSection>
    </div>
  );

  const renderUseCaseSection = () => (
    <div>
      <WizardSection
        id="usecase"
        title="Use Case"
        icon={<Lightbulb className="w-5 h-5" />}
        status={getSectionStatus('usecase')}
        collapsed={false}
        onToggle={() => {}}
      >
        <p className="text-muted-foreground text-sm">
          Choose the type that best matches your project to get relevant options for field mapping and metrics.
        </p>

        <UseCaseSelector
          selectedUseCase={formData.useCase}
          onSelectUseCase={(useCaseId) => updateFormData("useCase", useCaseId)}
        />
      </WizardSection>
    </div>
  );

  const renderDatasetSection = () => (
    <div>
      <WizardSection
        id="dataset"
        title="Dataset"
        icon={<Database className="w-5 h-5" />}
        status={getSectionStatus('dataset')}
        collapsed={false}
        onToggle={() => {}}
      >
        <DatasetUploader
          datasetPath={formData.datasetPath}
          uploadedFile={formData.uploadedFile}
          useCase={formData.useCase}
          onUpload={handleFileUpload}
          onRemove={() => {
            updateFormData("datasetPath", "");
            updateFormData("uploadedFile", null);
            setUploadError(null);
          }}
          loading={uploadLoading}
          error={uploadError}
        />
      </WizardSection>
    </div>
  );

  const renderFieldMappingSection = () => (
    <div>
      <WizardSection
        id="fieldmapping"
        title="Field Mapping"
        icon={<ArrowRight className="w-5 h-5" />}
        status={getSectionStatus('fieldmapping')}
        collapsed={false}
        onToggle={() => {}}
      >
        {formData.datasetPath ? (
          <FieldMappingInterface
            filename={formData.datasetPath}
            useCase={formData.useCase}
            onMappingUpdate={handleFieldMappingUpdate}
            existingMappings={formData.fieldMappings}
          />
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <ArrowRight className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>Upload a dataset first to configure field mappings</p>
          </div>
        )}
      </WizardSection>
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
    <div>
      <WizardSection
        id="metrics"
        title="Success Metrics"
        icon={<Target className="w-5 h-5" />}
        status={getSectionStatus('metrics')}
        collapsed={false}
        onToggle={() => {}}
      >
        <MetricsSelector
          useCase={formData.useCase}
          fieldMappings={formData.fieldMappings}
          selectedMetrics={formData.metrics}
          onMetricsChange={handleMetricsChange}
        />
      </WizardSection>
    </div>
  );

  const renderModelsSection = () => (
    <div>
      <WizardSection
        id="models"
        title="AI Models"
        icon={<Brain className="w-5 h-5" />}
        status={getSectionStatus('models')}
        collapsed={false}
        onToggle={() => {}}
      >
        <ModelProviderSelector
          useCase={formData.useCase}
          fieldMappings={formData.fieldMappings}
          onConfigurationChange={(configs) =>
            setFormData((prev) => ({ ...prev, modelConfigurations: configs }))
          }
        />
      </WizardSection>
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
    <div>
      <WizardSection
        id="optimizer"
        title="Optimizer"
        icon={<Zap className="w-5 h-5" />}
        status={getSectionStatus('optimizer')}
        collapsed={false}
        onToggle={() => {}}
      >
        <OptimizerSelector
          selectedOptimizer={formData.selectedOptimizer}
          onOptimizerChange={handleOptimizerChange}
          modelCount={formData.modelConfigurations.length}
          useCase={formData.useCase}
        />
      </WizardSection>
    </div>
  );

  // Render current step content
  const renderCurrentStep = () => {
    const stepId = WIZARD_STEPS[currentStep].id;
    switch (stepId) {
      case "prompt":
        return renderPromptSection();
      case "usecase":
        return renderUseCaseSection();
      case "dataset":
        return renderDatasetSection();
      case "fieldmapping":
        return renderFieldMappingSection();
      case "metrics":
        return renderMetricsSection();
      case "models":
        return renderModelsSection();
      case "optimizer":
        return renderOptimizerSection();
      default:
        return null;
    }
  };

  return (
    <div className="w-full">
      {/* Main Form Container */}
      <div className="bg-panel rounded-3xl border border-border p-6 md:p-8">
        {/* Header */}
        {renderRequirementsHeader()}

        {/* Progress Stepper */}
        {renderStepper()}

        {/* Current Step Content */}
        <div className="mb-8">
          {renderCurrentStep()}
        </div>

        {/* Step Navigation */}
        <div className="flex justify-between items-center mb-8 pt-6 border-t border-border">
          {currentStep > 0 ? (
            <Button
              onClick={goToPreviousStep}
              variant="outlined"
              size="medium"
            >
              <ChevronLeft className="w-5 h-5" />
              Previous
            </Button>
          ) : (
            <div />
          )}

          <div className="text-sm text-muted-foreground">
            Step {currentStep + 1} of {WIZARD_STEPS.length}
          </div>

          {currentStep < WIZARD_STEPS.length - 1 ? (
            <Button
              onClick={goToNextStep}
              disabled={!isCurrentStepValid()}
              variant="filled"
              size="medium"
            >
              Next
              <ChevronRight className="w-5 h-5" />
            </Button>
          ) : (
            <Button
              onClick={handleCreateProject}
              disabled={!isFormValid() || creatingProject || projectCreationResult?.success}
              variant="filledTeal"
              size="medium"
            >
              {creatingProject ? (
                <>
                  Creating Project...
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                </>
              ) : projectCreationResult?.success ? (
                <>
                  Project Created
                  <CheckCircle />
                </>
              ) : (
                <>
                  Create Project
                  <CheckCircle />
                </>
              )}
            </Button>
          )}
        </div>

        {/* Final Action Section - Show results when available */}
        {currentStep === WIZARD_STEPS.length - 1 && (
          <div className="mt-6">

          {/* Project Creation Results */}
          {projectCreationResult && (
            <div className={`mb-6 p-4 rounded-xl border ${
              projectCreationResult.success
                ? 'bg-meta-teal/5 border-meta-teal/30'
                : 'bg-red-500/5 border-red-500/30 dark:bg-red-400/5 dark:border-red-400/30'
            }`}>
              <div className="flex items-center space-x-3 mb-3">
                {projectCreationResult.success ? (
                  <CheckCircle className="w-6 h-6 text-meta-teal" />
                ) : (
                  <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
                )}
                <h3 className="font-bold text-lg text-foreground">
                  {projectCreationResult.success ? 'Project Created Successfully!' : 'Project Creation Failed'}
                </h3>
              </div>

              {projectCreationResult.success ? (
                <div className="space-y-3">
                  <p className="text-meta-teal">{projectCreationResult.message}</p>

                  {projectCreationResult.actualProjectName !== projectCreationResult.requestedProjectName && (
                    <div className="bg-meta-blue/5 p-3 rounded border border-meta-blue/30">
                      <p className="text-sm font-medium text-meta-blue mb-1">Project Name Updated:</p>
                      <p className="text-sm text-meta-blue/80">
                        A project with the name "{projectCreationResult.requestedProjectName}" already existed,
                        so your project was created as "{projectCreationResult.actualProjectName}" instead.
                      </p>
                    </div>
                  )}

                  <div className="bg-panel p-3 rounded border border-border">
                    <p className="text-sm font-medium text-foreground mb-1">Project Location:</p>
                    <p className="text-sm font-mono text-muted-foreground bg-muted p-2 rounded">
                      {projectCreationResult.projectPath}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-red-600 dark:text-red-400">{projectCreationResult.error}</p>
              )}
            </div>
          )}

          {/* Start Optimization Button */}
          {projectCreationResult?.success && !optimizing && !optimizationResult && (
            <div className="flex justify-center mb-6">
              <Button
                onClick={handleComplete}
                variant="filledTeal"
                size="large"
              >
                Start Optimization
                <Zap />
              </Button>
            </div>
          )}

          {/* Optimization Progress */}
          {optimizing && (
            <div className="mb-6 space-y-4">
              <div className="text-center">
                <h3 className="text-xl font-bold text-foreground mb-2">
                  🚀 Optimizing Your Prompt...
                </h3>
                <p className="text-muted-foreground">
                  This may take a few minutes. Real-time progress is shown below.
                </p>
              </div>

              {/* Progress Bar */}
              <div className="bg-panel p-4 rounded-xl border border-border shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-foreground">
                    {optimizationProgress.phase || "Initializing..."}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {Math.round(optimizationProgress.progress)}%
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-meta-blue h-2 rounded-full transition-all duration-300"
                    style={{ width: `${optimizationProgress.progress}%` }}
                  ></div>
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  {optimizationProgress.message}
                </p>
              </div>

              {/* Live Logs */}
              <div className="bg-gray-900 rounded-xl p-4 max-h-64 overflow-y-auto">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-white font-medium">Live Optimization Logs</h4>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-meta-teal rounded-full animate-pulse"></div>
                    <span className="text-meta-teal text-sm">Live</span>
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
                <div className="bg-meta-teal/5 border border-meta-teal/30 rounded-xl p-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <CheckCircle className="w-8 h-8 text-meta-teal" />
                    <h3 className="text-xl font-bold text-meta-teal-800">
                      🎉 {optimizationResult.message || "Optimization Complete!"}
                    </h3>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    {/* Before panel */}
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-3 h-3 rounded-full bg-red-400"></div>
                        <span className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                          Original
                        </span>
                      </div>
                      <div className="flex-1 border border-border bg-panel rounded-xl p-4 max-h-64 overflow-y-auto">
                        <DiffView
                          original={optimizationResult.originalPrompt || ""}
                          optimized={optimizationResult.optimizedPrompt || ""}
                          showOriginal={true}
                        />
                      </div>
                    </div>

                    {/* After panel */}
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-3 h-3 rounded-full bg-emerald-400"></div>
                        <span className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                          Optimized
                        </span>
                      </div>
                      <div className="flex-1 border border-border bg-panel rounded-xl p-4 max-h-64 overflow-y-auto">
                        <DiffView
                          original={optimizationResult.originalPrompt || ""}
                          optimized={optimizationResult.optimizedPrompt || ""}
                          showOriginal={false}
                        />
                      </div>
                    </div>
                  </div>

                  <InfoBox variant="info" title="Next Steps" className="mt-4">
                    Your optimized prompt has been saved to the project directory.
                    You can now use this improved prompt in your applications!
                  </InfoBox>
                </div>
              ) : (
                <InfoBox variant="error" title="Optimization Failed">
                  {optimizationResult.error}
                </InfoBox>
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
                    setCurrentStep(0);
                  }}
                  variant="outlined"
                  size="medium"
                >
                  Start New Optimization
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
