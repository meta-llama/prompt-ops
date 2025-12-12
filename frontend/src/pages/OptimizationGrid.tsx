import React, { useState } from "react";
import {
  Database,
  Target,
  BarChart3,
  Server,
  Zap,
  Lightbulb,
  Play,
} from "lucide-react";
import {
  StepCard,
  GridLayout,
  StepDialog,
  PromptCard,
  StepStatus,
} from "@/components/optimization-grid";
import { UseCaseSelector } from "@/components/onboarding/UseCaseSelector";
import { FieldMappingInterface } from "@/components/onboarding/FieldMappingInterface";
import { MetricsSelector } from "@/components/onboarding/MetricsSelector";
import { ModelProviderSelector } from "@/components/onboarding/ModelProviderSelector";
import { OptimizerSelector } from "@/components/onboarding/OptimizerSelector";
import { Button } from "@/components/ui/button";
import { Sidebar } from "@/components/layout/Sidebar";

const OptimizationGrid = () => {
  // Mode state
  const [activeMode, setActiveMode] = useState<"enhance" | "migrate">(
    "enhance"
  );

  // Navigation state
  const [activeStep, setActiveStep] = useState<string | null>(null);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());

  // Form data (matching OnboardingWizard structure)
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
    selectedOptimizer: "basic",
    optimizerConfig: null as any,
  });

  // Validation errors
  const [errors, setErrors] = useState<Record<string, string[]>>({});

  // Upload state
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Testing helper
  const toggleMockData = () => {
    if (isFormValid()) {
      // Clear all data
      setFormData({
        prompt: "",
        useCase: "",
        datasetPath: "",
        uploadedFile: null,
        fieldMappings: {},
        datasetType: "standard_json",
        metrics: [],
        metricConfigurations: {},
        modelConfigurations: [],
        selectedOptimizer: "basic",
        optimizerConfig: null,
      });
      setCompletedSteps(new Set());
    } else {
      // Fill with mock data
      setFormData({
        prompt: "Test prompt for optimization",
        useCase: "qa",
        datasetPath: "test-dataset.json",
        uploadedFile: null,
        fieldMappings: { question: "question", answer: "answer" },
        datasetType: "standard_json",
        metrics: ["accuracy", "f1_score"],
        metricConfigurations: {},
        modelConfigurations: [
          {
            provider: "OpenAI",
            model: "gpt-4",
            apiKey: "test-key",
          },
        ],
        selectedOptimizer: "basic",
        optimizerConfig: null,
      });
      setCompletedSteps(
        new Set(["usecase", "dataset", "fieldmapping", "metrics", "models"])
      );
    }
  };

  // Step definitions
  const steps = [
    {
      id: "usecase",
      title: "Use Case",
      icon: <Lightbulb className="w-6 h-6" />,
      required: true,
    },
    {
      id: "dataset",
      title: "Dataset",
      icon: <Database className="w-6 h-6" />,
      required: true,
      aspectRatio: "4/5",
    },
    {
      id: "fieldmapping",
      title: "Field Mapping",
      icon: <Target className="w-6 h-6" />,
      required: true,
    },
    {
      id: "metrics",
      title: "Success Metrics",
      icon: <BarChart3 className="w-6 h-6" />,
      required: true,
    },
    {
      id: "models",
      title: "AI Models",
      icon: <Server className="w-6 h-6" />,
      required: true,
    },
    {
      id: "optimizer",
      title: "Optimizer",
      icon: <Zap className="w-6 h-6" />,
      required: false,
    },
  ];

  // Helper: Update form data
  const updateFormData = (updates: Partial<typeof formData>) => {
    setFormData((prev) => ({ ...prev, ...updates }));
  };

  // Helper: Mark step as completed
  const markStepComplete = (stepId: string) => {
    setCompletedSteps((prev) => new Set([...prev, stepId]));
  };

  // Helper: Get step status
  const getStepStatus = (stepId: string): StepStatus => {
    if (errors[stepId]?.length > 0) return "error";
    if (completedSteps.has(stepId)) return "completed";
    if (activeStep === stepId) return "active";
    return "empty";
  };

  // Helper: Validate step
  const validateStep = (stepId: string): string[] => {
    const stepErrors: string[] = [];

    switch (stepId) {
      case "prompt":
        if (!formData.prompt.trim()) {
          stepErrors.push("Prompt is required");
        }
        break;
      case "usecase":
        if (!formData.useCase) {
          stepErrors.push("Use case is required");
        }
        break;
      case "dataset":
        if (!formData.uploadedFile && !formData.datasetPath) {
          stepErrors.push("Dataset is required");
        }
        break;
      case "fieldmapping":
        if (Object.keys(formData.fieldMappings).length === 0) {
          stepErrors.push("At least one field mapping is required");
        }
        break;
      case "metrics":
        if (formData.metrics.length === 0) {
          stepErrors.push("At least one metric is required");
        }
        break;
      case "models":
        if (formData.modelConfigurations.length === 0) {
          stepErrors.push("At least one model is required");
        }
        break;
    }

    return stepErrors;
  };

  // Helper: Check if all required fields are filled
  const isFormValid = (): boolean => {
    // Check prompt
    if (!formData.prompt.trim()) return false;

    // Check use case
    if (!formData.useCase) return false;

    // Check dataset (either uploaded file or path)
    if (!formData.uploadedFile && !formData.datasetPath) return false;

    // Check field mappings
    if (Object.keys(formData.fieldMappings).length === 0) return false;

    // Check metrics
    if (formData.metrics.length === 0) return false;

    // Check models
    if (formData.modelConfigurations.length === 0) return false;

    return true;
  };

  // Handler: Open step
  const openStep = (stepId: string) => {
    setActiveStep(stepId);
  };

  // Handler: Close step
  const closeStep = () => {
    setActiveStep(null);
  };

  // Handler: Save step
  const saveStep = (stepId: string) => {
    const stepErrors = validateStep(stepId);

    if (stepErrors.length === 0) {
      markStepComplete(stepId);
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[stepId];
        return newErrors;
      });
      closeStep();
    } else {
      setErrors((prev) => ({ ...prev, [stepId]: stepErrors }));
    }
  };

  // Handler: Validate all and start optimization
  const handleStartOptimization = () => {
    // Validate prompt
    const promptErrors = formData.prompt.trim() ? [] : ["Prompt is required"];

    // Validate all required steps
    const allErrors: Record<string, string[]> = {};
    if (promptErrors.length > 0) allErrors.prompt = promptErrors;

    steps.forEach((step) => {
      if (step.required) {
        const stepErrors = validateStep(step.id);
        if (stepErrors.length > 0) {
          allErrors[step.id] = stepErrors;
        }
      }
    });

    setErrors(allErrors);

    if (Object.keys(allErrors).length === 0) {
      // All valid - proceed with optimization
      console.log("Starting optimization with config:", formData);
      // TODO: Implement optimization start logic
      alert("Configuration is valid! Ready to start optimization.");
    } else {
      // Has errors - scroll to first error
      const firstErrorStep = steps.find((step) => allErrors[step.id]);
      if (firstErrorStep) {
        document.getElementById(`step-${firstErrorStep.id}`)?.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }
    }
  };

  return (
    <div className="min-h-screen w-full bg-background relative overflow-hidden">
      {/* Background styling */}
      <div className="absolute inset-0 bg-meta-gray-100/50"></div>
      <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(circle_at_50%_50%,hsl(var(--meta-gray))_1px,transparent_1px)] bg-[length:24px_24px]"></div>

      {/* Navigation */}
      <Sidebar />

      {/* Content */}
      <div className="relative z-10 pt-6 pb-12">
        <GridLayout maxWidth="max-w-4xl">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="flex items-center justify-center gap-4 mb-4">
              <h1 className="text-2xl md:text-3xl font-normal text-meta-gray tracking-tight">
                Optimize your prompt
              </h1>
              {/* Testing Toggle Button */}
              <Button
                onClick={toggleMockData}
                variant="outlinedGray"
                size="medium"
              >
                {isFormValid() ? "Clear All" : "Fill All"}
              </Button>
            </div>
            <p className="text-sm text-meta-gray/60">
              Configure your optimization workflow visually
            </p>
          </div>

          {/* Mode Selector - Matching MainContent style */}
          <div className="flex justify-center mb-6">
            <div className="bg-white p-1 rounded-xl shadow-lg border border-meta-gray-300 relative">
              <div className="grid grid-cols-2 gap-1 relative">
                {/* Sliding indicator */}
                <div
                  className={`absolute top-0 bottom-0 rounded-lg transition-all duration-300 ease-in-out bg-meta-blue ${
                    activeMode === "migrate"
                      ? "left-0 right-1/2 mr-0.5"
                      : "left-1/2 right-0 ml-0.5"
                  }`}
                />

                <Button
                  onClick={() => setActiveMode("migrate")}
                  variant="ghost"
                  className={`relative w-full px-8 py-3 text-lg font-medium z-10 transition-all duration-300 rounded-lg hover:bg-transparent ${
                    activeMode === "migrate"
                      ? "text-white hover:text-white"
                      : "text-meta-gray hover:text-meta-gray"
                  }`}
                >
                  Optimize
                </Button>

                <Button
                  onClick={() => setActiveMode("enhance")}
                  variant="ghost"
                  className={`relative w-full px-8 py-3 text-lg font-medium z-10 transition-all duration-300 rounded-lg hover:bg-transparent ${
                    activeMode === "enhance"
                      ? "text-white hover:text-white"
                      : "text-meta-gray hover:text-meta-gray"
                  }`}
                >
                  Enhance
                </Button>
              </div>
            </div>
          </div>

          {/* Prompt Card */}
          <PromptCard
            value={formData.prompt}
            onChange={(value) => {
              updateFormData({ prompt: value });
              if (value.trim()) {
                setErrors((prev) => {
                  const newErrors = { ...prev };
                  delete newErrors.prompt;
                  return newErrors;
                });
              }
            }}
            hasError={!!errors.prompt}
          />

          {/* Dataset & Use Case Row */}
          <div className="grid grid-cols-1 md:grid-cols-[1.6fr_1fr] gap-2">
            {/* Dataset Card - Left side with 4:5 aspect ratio */}
            <div className="w-full">
              <StepCard
                id="dataset"
                icon={<Database className="w-6 h-6" />}
                title="Dataset"
                subtitle="Upload your data"
                status={getStepStatus("dataset")}
                required={true}
                aspectRatio="4/5"
                onClick={() => openStep("dataset")}
                errorCount={errors.dataset?.length}
              />
            </div>

            {/* Use Case & Field Mapping - Right side stack */}
            <div className="flex flex-col gap-2 h-full">
              <div className="flex-[35]">
                <StepCard
                  id="usecase"
                  icon={<Lightbulb className="w-6 h-6" />}
                  title="Use Case"
                  subtitle="Type of task"
                  status={getStepStatus("usecase")}
                  required={true}
                  onClick={() => openStep("usecase")}
                  errorCount={errors.usecase?.length}
                  className="h-full min-h-[100px]"
                />
              </div>
              <div className="flex-[65]">
                <StepCard
                  id="fieldmapping"
                  icon={<Target className="w-6 h-6" />}
                  title="Field Mapping"
                  subtitle="Map fields"
                  status={getStepStatus("fieldmapping")}
                  required={true}
                  onClick={() => openStep("fieldmapping")}
                  errorCount={errors.fieldmapping?.length}
                  className="h-full min-h-[160px]"
                />
              </div>
            </div>
          </div>

          {/* Success Metrics - Full Width */}
          <StepCard
            id="metrics"
            icon={<BarChart3 className="w-6 h-6" />}
            title="Success Metrics"
            subtitle="How to measure success"
            status={getStepStatus("metrics")}
            required={true}
            onClick={() => openStep("metrics")}
            errorCount={errors.metrics?.length}
            className="min-h-[120px]"
          />

          {/* AI Models & Optimizer Row - Equal Split */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <StepCard
              id="models"
              icon={<Server className="w-6 h-6" />}
              title="AI Models"
              subtitle="Inference providers"
              status={getStepStatus("models")}
              required={true}
              onClick={() => openStep("models")}
              errorCount={errors.models?.length}
              className="min-h-[140px]"
            />
            <StepCard
              id="optimizer"
              icon={<Zap className="w-6 h-6" />}
              title="Optimizer"
              subtitle="Strategy"
              status={getStepStatus("optimizer")}
              required={false}
              onClick={() => openStep("optimizer")}
              className="min-h-[140px]"
            />
          </div>

          {/* Review & Start Button */}
          <div className="mt-6">
            {isFormValid() ? (
              <Button
                onClick={handleStartOptimization}
                className="w-full h-12 text-lg font-medium text-white bg-meta-blue hover:bg-meta-blue-800 transition-colors rounded-full"
                size="lg"
              >
                <Play className="w-6 h-6 mr-2" />
                Optimize
              </Button>
            ) : (
              <Button
                onClick={handleStartOptimization}
                disabled={true}
                className="w-full h-12 text-lg font-medium text-white bg-meta-gray-300 opacity-50 cursor-not-allowed rounded-xl"
                size="lg"
              >
                <Play className="w-6 h-6 mr-2" />
                Optimize
              </Button>
            )}
            {!isFormValid() && (
              <p className="text-sm text-meta-gray/60 text-center mt-2">
                Complete all required fields to start optimization
              </p>
            )}
          </div>

        </GridLayout>
      </div>

      {/* Step Dialogs */}
      <StepDialog
        open={activeStep === "usecase"}
        onOpenChange={closeStep}
        title="Select Use Case"
        description="Choose the type of application you're optimizing for"
        onSave={() => saveStep("usecase")}
      >
        <UseCaseSelector
          selectedUseCase={formData.useCase}
          onSelectUseCase={(useCaseId) =>
            updateFormData({ useCase: useCaseId })
          }
        />
      </StepDialog>

      <StepDialog
        open={activeStep === "dataset"}
        onOpenChange={closeStep}
        title="Upload Dataset & Field Mapping"
        description="Upload your evaluation dataset and map the fields"
        hideSaveButton={true}
      >
        <FieldMappingInterface
          filename={formData.datasetPath}
          useCase={formData.useCase}
          onMappingUpdate={(mappings) => {
            updateFormData({ fieldMappings: mappings });
            markStepComplete("dataset");
            markStepComplete("fieldmapping");
          }}
          existingMappings={formData.fieldMappings}
        />
      </StepDialog>

      <StepDialog
        open={activeStep === "fieldmapping"}
        onOpenChange={closeStep}
        title="Field Mapping"
        description="Map your dataset fields"
        hideSaveButton={true}
      >
        <FieldMappingInterface
          filename={formData.datasetPath}
          useCase={formData.useCase}
          onMappingUpdate={(mappings) => {
            updateFormData({ fieldMappings: mappings });
            markStepComplete("fieldmapping");
          }}
          existingMappings={formData.fieldMappings}
        />
      </StepDialog>

      <StepDialog
        open={activeStep === "metrics"}
        onOpenChange={closeStep}
        title="Success Metrics"
        description="Choose how to measure optimization success"
        onSave={() => saveStep("metrics")}
      >
        <MetricsSelector
          useCase={formData.useCase}
          fieldMappings={formData.fieldMappings}
          selectedMetrics={formData.metrics}
          onMetricsChange={(metrics) => updateFormData({ metrics })}
        />
      </StepDialog>

      <StepDialog
        open={activeStep === "models"}
        onOpenChange={closeStep}
        title="AI Models"
        description="Select inference providers and configure models"
        onSave={() => saveStep("models")}
      >
        <ModelProviderSelector
          useCase={formData.useCase}
          fieldMappings={formData.fieldMappings}
          onConfigurationChange={(configs) =>
            updateFormData({ modelConfigurations: configs })
          }
        />
      </StepDialog>

      <StepDialog
        open={activeStep === "optimizer"}
        onOpenChange={closeStep}
        title="Optimizer Strategy"
        description="Choose your optimization strategy"
        onSave={() => saveStep("optimizer")}
      >
        <OptimizerSelector
          selectedOptimizer={formData.selectedOptimizer}
          onOptimizerChange={(optimizer) =>
            updateFormData({ selectedOptimizer: optimizer })
          }
          modelCount={formData.modelConfigurations.length}
          useCase={formData.useCase}
        />
      </StepDialog>
    </div>
  );
};

export default OptimizationGrid;
