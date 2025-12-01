import React, { useState, useRef, useEffect, useContext } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ArrowUp, FileJson, Loader2, Plus, Trash2, Upload, Zap, X, Settings, ChevronDown, ChevronUp, Eye, EyeOff } from 'lucide-react';
import { useToast } from '../../hooks/use-toast';
import { AppContext } from '../../context/AppContext';
import { Badge } from '@/components/ui/badge';
import { OptimizationProgress, OptimizationStep } from './OptimizationProgress';
import { OptimizationResults } from './OptimizationResults';
import { OnboardingWizard } from '../onboarding/OnboardingWizard';

export const PromptInput = () => {
  const { toast } = useToast();
  const [prompt, setPrompt] = useState('');
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizedPrompt, setOptimizedPrompt] = useState('');
  const [originalPrompt, setOriginalPrompt] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const { activeMode, setIsModeLocked } = useContext(AppContext);

  // Add state for quick start demo
  const [isLoadingDemo, setIsLoadingDemo] = useState(false);
  const [isDemoLoaded, setIsDemoLoaded] = useState(false);
  const [isDemoDismissed, setIsDemoDismissed] = useState(false);

  // Dataset upload state
  const [showDatasetDialog, setShowDatasetDialog] = useState(false);
  const [isUploadingDataset, setIsUploadingDataset] = useState(false);
  const [uploadedDatasets, setUploadedDatasets] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Configuration state from OnboardingWizard
  const [config, setConfig] = useState({
    model: 'Llama 3.3 70B',
    proposer: 'Llama 3.3 70B',
    strategy: 'MiPro',
    datasetAdapter: '',  // Changed from dataset to datasetAdapter
    metrics: 'Exact Match',  // Added metrics
    useLlamaTips: true,
    openrouterApiKey: undefined
  });

  // Enhance mode settings state
  const [showEnhanceSettings, setShowEnhanceSettings] = useState(false);
  const [enhanceSettings, setEnhanceSettings] = useState({
    apiBaseUrl: '',  // Empty means use backend default
    apiFormat: 'openai',  // Default to OpenAI-compatible format
    apiKey: '',  // Empty means use backend default
    model: '',  // Empty means use backend default
  });
  const [showApiKey, setShowApiKey] = useState(false);

  // Load enhance settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('enhanceSettings');
    if (savedSettings) {
      try {
        setEnhanceSettings(JSON.parse(savedSettings));
      } catch (e) {
        console.error('Failed to load saved enhance settings:', e);
      }
    }
  }, []);

  // Save enhance settings to localStorage when changed
  useEffect(() => {
    if (enhanceSettings.apiBaseUrl || enhanceSettings.apiKey || enhanceSettings.model) {
      localStorage.setItem('enhanceSettings', JSON.stringify(enhanceSettings));
    }
  }, [enhanceSettings]);
  const [showWizard, setShowWizard] = useState(true);
  const [wizardCompleted, setWizardCompleted] = useState(false);

  // Fetch uploaded datasets on component mount
  useEffect(() => {
    fetchUploadedDatasets();
  }, []);

  const fetchUploadedDatasets = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/datasets');
      if (response.ok) {
        const data = await response.json();
        setUploadedDatasets(data.datasets || []);
      }
    } catch (error) {
      console.error('Error fetching datasets:', error);
    }
  };

  const handleWizardComplete = (wizardConfig: any) => {
    console.log('Wizard completed with config:', wizardConfig);

    // Extract configuration from wizard and update local config state
    setConfig({
      model: wizardConfig.models?.selected?.[0]?.taskModel || 'Llama 3.3 70B',
      proposer: wizardConfig.models?.selected?.[0]?.proposerModel || 'Llama 3.3 70B',
      strategy: wizardConfig.optimizer || 'MiPro',
      datasetAdapter: wizardConfig.datasetType || '',
      metrics: Array.isArray(wizardConfig.metrics) ? wizardConfig.metrics.join(', ') : wizardConfig.metrics || 'Exact Match',
      useLlamaTips: wizardConfig.useLlamaTips !== false,
      openrouterApiKey: wizardConfig.apiKey
    });

    setWizardCompleted(true);
    setShowWizard(false);

    toast({
      title: "Configuration Complete",
      description: "Your optimization settings have been configured successfully.",
    });
  };

  const handleDatasetUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Check if there's already an uploaded dataset
    if (uploadedDatasets.length > 0) {
      // Ask for confirmation before replacing the existing dataset
      if (!window.confirm('You already have an uploaded dataset. Replace it with the new one?')) {
        // Clear file input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        return;
      }

      // Delete the existing dataset
      await handleDatasetDelete(uploadedDatasets[0].filename);
    }

    setIsUploadingDataset(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/datasets/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload dataset');
      }

      const data = await response.json();

      // Refresh dataset list
      await fetchUploadedDatasets();

      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      console.log('Dataset uploaded successfully:', data);
    } catch (error) {
      console.error('Error uploading dataset:', error);
    } finally {
      setIsUploadingDataset(false);
    }
  };

  const handleDatasetDelete = async (filename: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/datasets/${filename}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete dataset');
      }

      // Refresh dataset list
      await fetchUploadedDatasets();
    } catch (error) {
      console.error('Error deleting dataset:', error);
    }
  };

  const handleQuickStartDemo = async () => {
    setIsLoadingDemo(true);

    try {
      const response = await fetch('http://localhost:8000/api/quick-start-demo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load quick start demo');
      }

      const data = await response.json();

      // Update the prompt with demo prompt
      setPrompt(data.prompt);

      // Refresh uploaded datasets to show the demo dataset first
      await fetchUploadedDatasets();

      // Add a small delay to ensure the datasets are loaded, then update configuration
      setTimeout(() => {
        setConfig(data.config);
      }, 100);

      // Mark demo as loaded
      setIsDemoLoaded(true);

      toast({
        title: "Demo Loaded Successfully! 🚀",
        description: data.message,
        duration: 5000,
      });

    } catch (error) {
      console.error('Error loading quick start demo:', error);
      toast({
        title: "Failed to Load Demo",
        description: error instanceof Error ? error.message : "An unexpected error occurred",
        variant: "destructive",
      });
    } finally {
      setIsLoadingDemo(false);
    }
  };

  const optimizationSteps: OptimizationStep[] = [
    {
      id: 'analyze',
      label: 'Analyzing original prompt',
      completed: currentStep > 0,
      inProgress: currentStep === 0 && isOptimizing
    },
    {
      id: 'process',
      label: 'Processing dataset',
      completed: currentStep > 1,
      inProgress: currentStep === 1 && isOptimizing
    },
    {
      id: 'generate',
      label: 'Generating optimized versions...',
      completed: currentStep > 2,
      inProgress: currentStep === 2 && isOptimizing
    },
    {
      id: 'evaluate',
      label: 'Evaluating performance',
      completed: currentStep > 3,
      inProgress: currentStep === 3 && isOptimizing
    }
  ];

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(optimizedPrompt);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  const resetOptimization = () => {
    setIsOptimizing(false);
    setShowResults(false);
    setCurrentStep(0);
  };

  const handleOptimizePrompt = async () => {
    if (!prompt.trim() || isOptimizing) return;

    // Check if dataset is uploaded and adapter is selected for migrate mode
    if (activeMode === 'migrate') {
      if (uploadedDatasets.length === 0) {
        alert('Please upload a dataset before optimizing.');
        return;
      }
      if (!config.datasetAdapter) {
        alert('Please select a dataset adapter type before optimizing.');
        return;
      }
    }

    // Lock the mode selection when optimization starts
    setIsModeLocked(true);
    setIsOptimizing(true);
    setShowResults(false);
    setOriginalPrompt(prompt);
    setCurrentStep(0);

    // Simulate the optimization steps with delays
    const simulateSteps = async () => {
      // Step 1: Analyzing original prompt
      await new Promise(resolve => setTimeout(resolve, 1500));
      setCurrentStep(1);

      // Step 2: Processing dataset
      await new Promise(resolve => setTimeout(resolve, 1500));
      setCurrentStep(2);

      // Step 3: Generating optimized versions
      await new Promise(resolve => setTimeout(resolve, 2000));
      setCurrentStep(3);

      // Step 4: Evaluating performance
      await new Promise(resolve => setTimeout(resolve, 1500));
    };

    try {
      // Start the simulation
      await simulateSteps();

      // Connect to FastAPI backend with the appropriate endpoint based on mode
      const endpoint = activeMode === 'enhance' ? 'enhance-prompt' : 'migrate-prompt';

      // Build request body with configuration
      const requestBody = activeMode === 'enhance'
        ? {
            prompt,
            config: {
              // Only include non-empty enhance settings
              ...(enhanceSettings.apiBaseUrl && { apiBaseUrl: enhanceSettings.apiBaseUrl }),
              ...(enhanceSettings.apiFormat && { apiFormat: enhanceSettings.apiFormat }),
              ...(enhanceSettings.apiKey && { apiKey: enhanceSettings.apiKey }),
              ...(enhanceSettings.model && { model: enhanceSettings.model }),
            }
          }
        : {
            prompt,
            config: {
              // Use config from OnboardingWizard
              provider: "openrouter",
              ...config
            }
          };

      const response = await fetch(`http://localhost:8000/api/${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error('Failed to optimize prompt');
      }

      const data = await response.json();
      setOptimizedPrompt(data.optimizedPrompt);

      // Show results instead of updating the prompt directly
      setShowResults(true);
    } catch (error) {
      console.error('Error optimizing prompt:', error);
      toast({
        title: "Optimization Failed",
        description: error instanceof Error ? error.message : "An unexpected error occurred during optimization. Please check your configuration and try again.",
        variant: "destructive",
      });
    } finally {
      setIsOptimizing(false);
      setCurrentStep(0);
    }
  };

  return (
    <div className="relative max-w-6xl mx-auto">
      {showResults ? (
        <div className="mt-8">
          <OptimizationResults
            originalPrompt={originalPrompt}
            optimizedPrompt={optimizedPrompt}
            onCopy={handleCopyToClipboard}
          />
          <div className="flex justify-center mt-8 gap-4">
            <button
              onClick={() => {
                setPrompt('');
                setOptimizedPrompt('');
                setShowResults(false);
                setIsModeLocked(false); // Unlock mode selection when starting new
              }}
              className="bg-facebook-gray hover:bg-facebook-border text-facebook-text border border-facebook-border px-8 py-3 rounded-xl font-medium transition-all duration-300 shadow-lg transform hover:scale-105"
            >
              Start New
            </button>
          </div>
        </div>
      ) : isOptimizing ? (
        <div className="bg-white/90 backdrop-blur-xl rounded-2xl p-8 shadow-xl border border-facebook-border text-center">
          <h2 className="text-3xl font-bold mb-2 text-facebook-text">Run Optimization</h2>
          <p className="text-facebook-text/70 mb-8">Ready to optimize your prompt for Llama models. This process typically takes 5-10 minutes.</p>

          <div className="flex justify-center mb-8">
            <div className="w-20 h-20">
              <div className="w-full h-full rounded-full animate-spin"
                style={{
                  background: 'conic-gradient(from 0deg, transparent, hsl(var(--facebook-blue) / 0) 10%, hsl(var(--facebook-blue) / 0.2) 20%, hsl(var(--facebook-blue) / 0.4) 30%, hsl(var(--facebook-blue) / 0.8) 40%, hsl(var(--facebook-blue)) 50%, hsl(var(--facebook-blue) / 0) 60%)',
                  borderRadius: '50%',
                  boxShadow: '0 0 20px hsl(var(--facebook-blue) / 0.3)'
                }}>
              </div>
            </div>
          </div>

          <h3 className="text-2xl font-semibold mb-2 text-facebook-text">Optimizing Prompt...</h3>
          <p className="text-facebook-text/70 mb-8">This may take several minutes. Please don't close this window.</p>

          <OptimizationProgress steps={optimizationSteps} />
        </div>
      ) : (
        <>
          {/* Prompt input - only show in enhance mode */}
          {activeMode === 'enhance' && (
            <div className="relative bg-white/90 backdrop-blur-xl rounded-2xl p-6 shadow-xl border border-facebook-border mb-8">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Your prompt..."
                disabled={isOptimizing}
                className={`w-full h-28 p-0 text-xl text-facebook-text bg-transparent placeholder:text-facebook-text/50 border-none outline-none resize-none leading-relaxed ${isOptimizing ? 'opacity-75' : ''}`}
              />

              {/* Collapsible settings panel */}
              <div className="mt-4 border-t border-facebook-border/30 pt-4">
                <button
                  onClick={() => setShowEnhanceSettings(!showEnhanceSettings)}
                  className="flex items-center gap-2 text-sm text-facebook-text/70 hover:text-facebook-text transition-colors"
                >
                  <Settings size={16} />
                  <span>API Settings</span>
                  {showEnhanceSettings ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  {(enhanceSettings.apiBaseUrl || enhanceSettings.apiKey || enhanceSettings.model) && (
                    <Badge variant="secondary" className="ml-2 text-xs">Configured</Badge>
                  )}
                </button>

                {showEnhanceSettings && (
                  <div className="mt-4 space-y-4 p-4 bg-gray-50 rounded-lg">
                    <div className="text-xs text-facebook-text/60 mb-3">
                      Leave fields empty to use backend defaults from .env file
                    </div>

                    {/* API Base URL */}
                    <div>
                      <Label className="text-sm text-facebook-text/80 mb-1.5">API Base URL</Label>
                      <input
                        type="text"
                        value={enhanceSettings.apiBaseUrl}
                        onChange={(e) => setEnhanceSettings({ ...enhanceSettings, apiBaseUrl: e.target.value })}
                        placeholder="e.g., https://api.llama.com/compat/v1"
                        className="w-full px-3 py-2 text-sm border border-facebook-border rounded-lg focus:ring-2 focus:ring-facebook-blue focus:border-transparent"
                        disabled={isOptimizing}
                      />
                      <div className="text-xs text-facebook-text/50 mt-1">
                        The base URL for your API endpoint
                      </div>
                    </div>

                    {/* API Format */}
                    <div>
                      <Label className="text-sm text-facebook-text/80 mb-1.5">API Format</Label>
                      <select
                        value={enhanceSettings.apiFormat}
                        onChange={(e) => setEnhanceSettings({ ...enhanceSettings, apiFormat: e.target.value })}
                        className="w-full px-3 py-2 text-sm border border-facebook-border rounded-lg focus:ring-2 focus:ring-facebook-blue focus:border-transparent"
                        disabled={true}
                      >
                        <option value="openai">OpenAI-compatible</option>
                      </select>
                      <div className="text-xs text-facebook-text/50 mt-1">
                        Most APIs are OpenAI-compatible
                      </div>
                    </div>

                    {/* API Key input */}
                    <div>
                      <Label className="text-sm text-facebook-text/80 mb-1.5">API Key</Label>
                      <div className="relative">
                        <input
                          type={showApiKey ? "text" : "password"}
                          value={enhanceSettings.apiKey}
                          onChange={(e) => setEnhanceSettings({ ...enhanceSettings, apiKey: e.target.value })}
                          placeholder="Your API key"
                          className="w-full px-3 py-2 pr-10 text-sm border border-facebook-border rounded-lg focus:ring-2 focus:ring-facebook-blue focus:border-transparent"
                          disabled={isOptimizing}
                        />
                        <button
                          type="button"
                          onClick={() => setShowApiKey(!showApiKey)}
                          className="absolute right-2 top-1/2 -translate-y-1/2 text-facebook-text/50 hover:text-facebook-text"
                        >
                          {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>
                      <div className="text-xs text-facebook-text/50 mt-1">
                        Required if not set in backend .env
                      </div>
                    </div>

                    {/* Model name input */}
                    <div>
                      <Label className="text-sm text-facebook-text/80 mb-1.5">Model Name</Label>
                      <input
                        type="text"
                        value={enhanceSettings.model}
                        onChange={(e) => setEnhanceSettings({ ...enhanceSettings, model: e.target.value })}
                        placeholder="e.g., Llama-4-Maverick-17B-128E-Instruct-FP8"
                        className="w-full px-3 py-2 text-sm border border-facebook-border rounded-lg focus:ring-2 focus:ring-facebook-blue focus:border-transparent"
                        disabled={isOptimizing}
                      />
                      <div className="text-xs text-facebook-text/50 mt-1">
                        The exact model name as expected by your API
                      </div>
                    </div>

                    {/* Clear settings button */}
                    {(enhanceSettings.apiBaseUrl || enhanceSettings.apiKey || enhanceSettings.model) && (
                      <button
                        onClick={() => {
                          setEnhanceSettings({ apiBaseUrl: '', apiFormat: 'openai', apiKey: '', model: '' });
                          localStorage.removeItem('enhanceSettings');
                        }}
                        className="text-xs text-red-600 hover:text-red-700 flex items-center gap-1"
                      >
                        <X size={14} />
                        Clear all settings
                      </button>
                    )}
                  </div>
                )}
              </div>

              <div className="flex items-center justify-end mt-6">
                <div className="relative group">
                  <button
                    onClick={handleOptimizePrompt}
                    disabled={isOptimizing || !prompt.trim()}
                    className={`bg-facebook-blue hover:bg-facebook-blue-dark text-white p-3 rounded-xl shadow-lg hover:shadow-facebook-blue/25 transition-all duration-300 transform ${!isOptimizing && prompt.trim() ? 'hover:scale-110 hover:-translate-y-1' : 'opacity-75 cursor-not-allowed'}`}
                  >
                    {isOptimizing ? <Loader2 size={20} className="animate-spin" /> : <ArrowUp size={20} />}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Onboarding wizard - always rendered but hidden when not in migrate mode or when completed */}
          <div className={activeMode === 'migrate' && showWizard ? 'block' : 'hidden'}>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <OnboardingWizard
                activeMode={activeMode as "migrate" | "enhance"}
                onComplete={handleWizardComplete}
              />
            </div>
          </div>

          {/* Configuration summary - shown after wizard completion */}
          {activeMode === 'migrate' && wizardCompleted && !showWizard && (
            <div className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-xl border border-facebook-border p-6 max-w-4xl mx-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-2xl font-bold text-facebook-text">Configuration Summary</h3>
                <Button
                  onClick={() => setShowWizard(true)}
                  variant="outline"
                  className="text-facebook-blue border-facebook-blue hover:bg-facebook-blue hover:text-white"
                >
                  Reconfigure
                </Button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="font-medium text-facebook-text/70">Dataset Adapter:</span>
                  <p className="text-facebook-text">{config.datasetAdapter || 'Not selected'}</p>
                </div>
                <div>
                  <span className="font-medium text-facebook-text/70">Metrics:</span>
                  <p className="text-facebook-text">{config.metrics}</p>
                </div>
                <div>
                  <span className="font-medium text-facebook-text/70">Optimizer:</span>
                  <p className="text-facebook-text">{config.strategy}</p>
                </div>
                <div>
                  <span className="font-medium text-facebook-text/70">Model:</span>
                  <p className="text-facebook-text">{config.model}</p>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Dataset Upload Dialog */}
      <Dialog open={showDatasetDialog} onOpenChange={setShowDatasetDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Manage Dataset</DialogTitle>
            <DialogDescription>
              {uploadedDatasets.length > 0
                ? "View or replace your current dataset."
                : "Upload a JSON dataset file for optimization."}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* Current Dataset Section */}
            {uploadedDatasets.length > 0 && (
              <div className="border border-green-200 bg-green-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-green-800 mb-2">Current Dataset</h3>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <FileJson className="w-5 h-5 mr-2 text-green-700" />
                    <div>
                      <span className="font-medium text-green-800">{uploadedDatasets[0].filename}</span>
                      <span className="text-sm text-green-700 ml-2">
                        ({uploadedDatasets[0].total_records} records)
                      </span>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDatasetDelete(uploadedDatasets[0].filename)}
                    className="text-red-500 hover:text-red-600 hover:bg-red-50 border-red-200"
                  >
                    <Trash2 className="w-4 h-4 mr-1" />
                    Remove
                  </Button>
                </div>

                {/* Dataset Preview */}
                {uploadedDatasets[0].preview && uploadedDatasets[0].preview.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-semibold text-green-800 mb-2">Preview:</h4>
                    <div className="bg-white border border-green-200 rounded-md p-3 max-h-40 overflow-y-auto">
                      <pre className="text-xs text-green-900 whitespace-pre-wrap">
                        {JSON.stringify(uploadedDatasets[0].preview[0], null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Upload Section */}
            <div>
              <h3 className="text-lg font-semibold mb-3">
                {uploadedDatasets.length > 0 ? "Replace Dataset" : "Upload Dataset"}
              </h3>
              <div className="flex gap-3">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json"
                  onChange={handleDatasetUpload}
                  className="hidden"
                  disabled={isUploadingDataset}
                />
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  className={`w-full ${
                    uploadedDatasets.length > 0
                      ? "bg-white hover:bg-gray-50 text-gray-700 border border-gray-300"
                      : "bg-white hover:bg-facebook-gray text-facebook-text border-2 border-dashed border-facebook-border"
                  }`}
                  disabled={isUploadingDataset}
                >
                  {isUploadingDataset ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      {uploadedDatasets.length > 0 ? "Choose New Dataset" : "Choose JSON File"}
                    </>
                  )}
                </Button>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                {uploadedDatasets.length > 0
                  ? "Uploading a new dataset will replace the current one."
                  : "Upload a JSON dataset file for evaluation examples."}
              </p>
            </div>

            {/* No Dataset Message */}
            {uploadedDatasets.length === 0 && (
              <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg border border-gray-200">
                <FileJson className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No dataset uploaded yet</p>
                <p className="text-sm mt-1">You need a dataset to optimize prompts</p>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Force module reload - 2025-01-06
