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
import { ArrowUp, FileJson, Loader2, Plus, Trash2, Upload, Zap, X } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { AppContext } from '../context/AppContext';
import { Badge } from '@/components/ui/badge';
import { OptimizationProgress, OptimizationStep } from './OptimizationProgress';
import { OptimizationResults } from './OptimizationResults';
import { ConfigurationPanel } from './ConfigurationPanel';

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

  // Configuration state from ConfigurationPanel
  const [config, setConfig] = useState({
    model: 'Llama 3.3 70B',
    proposer: 'Llama 3.3 70B',
    strategy: 'MiPro',
    datasetAdapter: '',  // Changed from dataset to datasetAdapter
    metrics: 'Exact Match',  // Added metrics
    useLlamaTips: true,
    openrouterApiKey: undefined
  });

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

      // Only include configuration for migrate-prompt endpoint
      const requestBody = activeMode === 'enhance'
        ? { prompt }
        : {
            prompt,
            config: {
              // Use config from ConfigurationPanel
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
    <div className="relative max-w-4xl mx-auto">
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
          {/* Quick Start Demo Section - Only show in migrate mode when no demo loaded */}
          {activeMode === 'migrate' && !isDemoLoaded && !isDemoDismissed && uploadedDatasets.length === 0 && !prompt.trim() && (
            <div className="bg-gradient-to-br from-facebook-blue/5 via-white to-facebook-blue/10 backdrop-blur-xl rounded-2xl p-8 shadow-xl border-2 border-facebook-blue/20 mb-8 relative overflow-hidden">
              {/* Background decoration */}
              <div className="absolute top-0 right-0 w-32 h-32 bg-facebook-blue/5 rounded-full -translate-y-16 translate-x-16"></div>
              <div className="absolute bottom-0 left-0 w-24 h-24 bg-facebook-blue/5 rounded-full translate-y-12 -translate-x-12"></div>

              {/* Dismiss button - top right */}
              <button
                onClick={() => setIsDemoDismissed(true)}
                className="absolute top-4 right-4 z-20 w-8 h-8 rounded-full bg-facebook-text/10 hover:bg-facebook-text/20 flex items-center justify-center transition-all duration-200 group"
                title="Dismiss demo"
              >
                <X className="w-4 h-4 text-facebook-text/60 group-hover:text-facebook-text" />
              </button>

              <div className="relative z-10 text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-facebook-blue/10 rounded-full mb-6">
                  <Zap className="w-8 h-8 text-facebook-blue" />
                </div>

                <h2 className="text-3xl font-black text-facebook-text mb-4">Ready to Get Started?</h2>
                <p className="text-facebook-text/80 text-lg mb-6 max-w-2xl mx-auto">
                  Try our <strong>Facility Support Analyzer</strong> demo - a complete example with real data,
                  optimized configuration, and ready-to-run prompts. Perfect for testing the system!
                </p>

                <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                  <Button
                    onClick={handleQuickStartDemo}
                    disabled={isLoadingDemo}
                    className="bg-facebook-blue hover:bg-facebook-blue-dark text-white px-8 py-4 rounded-xl text-lg font-semibold shadow-lg hover:shadow-facebook-blue/25 transition-all duration-300 transform hover:scale-105 min-w-[200px]"
                  >
                    {isLoadingDemo ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        Loading Demo...
                      </>
                    ) : (
                      <>
                        <Zap className="w-5 h-5 mr-2" />
                        Quick Start Demo
                      </>
                    )}
                  </Button>

                  <button
                    onClick={() => setIsDemoDismissed(true)}
                    className="text-facebook-text/60 text-sm hover:text-facebook-text/80 transition-colors duration-200 underline decoration-dotted underline-offset-4"
                  >
                    Or manually upload your own dataset below
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8 text-left">
                  <div className="bg-white/50 rounded-lg p-4 border border-facebook-blue/10">
                    <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mb-3">
                      <FileJson className="w-4 h-4 text-green-600" />
                    </div>
                    <h3 className="font-semibold text-facebook-text mb-2">Sample Dataset</h3>
                    <p className="text-sm text-facebook-text/70">1,203 facility support emails with categories and sentiment</p>
                  </div>

                  <div className="bg-white/50 rounded-lg p-4 border border-facebook-blue/10">
                    <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mb-3">
                      <Zap className="w-4 h-4 text-blue-600" />
                    </div>
                    <h3 className="font-semibold text-facebook-text mb-2">Optimized Config</h3>
                    <p className="text-sm text-facebook-text/70">Llama 3.3 70B with facility-specific metrics</p>
                  </div>

                  <div className="bg-white/50 rounded-lg p-4 border border-facebook-blue/10">
                    <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mb-3">
                      <ArrowUp className="w-4 h-4 text-purple-600" />
                    </div>
                    <h3 className="font-semibold text-facebook-text mb-2">Ready to Run</h3>
                    <p className="text-sm text-facebook-text/70">Just click "Run" and see optimization in action</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Demo loaded success message */}
          {isDemoLoaded && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-8 flex items-center">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                <Zap className="w-4 h-4 text-green-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-green-800">Demo Loaded Successfully!</h3>
                <p className="text-sm text-green-700">Facility Support Analyzer is ready with sample data and optimal configuration.</p>
              </div>
            </div>
          )}

          <div className="relative bg-white/90 backdrop-blur-xl rounded-2xl p-6 shadow-xl border border-facebook-border mb-8">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Your prompt..."
              disabled={isOptimizing}
              className={`w-full h-28 p-0 text-xl text-facebook-text bg-transparent placeholder:text-facebook-text/50 border-none outline-none resize-none leading-relaxed ${isOptimizing ? 'opacity-75' : ''}`}
            />

            <div className="flex items-center justify-between mt-6">
              <div className="flex items-center gap-3">
                <Button
                  onClick={() => setShowDatasetDialog(true)}
                  className={`flex items-center px-4 py-2 rounded-xl text-sm font-medium backdrop-blur-sm transition-all ${
                    uploadedDatasets.length > 0
                      ? 'bg-green-50 text-green-700 hover:bg-green-100 border border-green-300'
                      : activeMode === 'migrate' && !config.datasetAdapter
                      ? 'bg-red-50 text-red-700 hover:bg-red-100 border-2 border-red-300 animate-pulse'
                      : 'bg-facebook-gray/50 text-facebook-text hover:bg-facebook-gray border border-facebook-border'
                  }`}
                >
                  {uploadedDatasets.length > 0 ? (
                    <>
                      <FileJson className="w-4 h-4 mr-2" />
                      {uploadedDatasets[0].filename} ({uploadedDatasets[0].total_records} records)
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4 mr-2" />
                      Add Dataset {activeMode === 'migrate' && <span className="text-red-600">* <span className="text-xs text-red-600 font-medium">Required</span></span>}
                    </>
                  )}
                </Button>
              </div>

              <div className="relative group">
                <button
                  onClick={handleOptimizePrompt}
                  disabled={isOptimizing || !prompt.trim() || (activeMode === 'migrate' && (uploadedDatasets.length === 0 || !config.datasetAdapter))}
                  className={`bg-facebook-blue hover:bg-facebook-blue-dark text-white p-3 rounded-xl shadow-lg hover:shadow-facebook-blue/25 transition-all duration-300 transform ${!isOptimizing && prompt.trim() && (activeMode !== 'migrate' || (uploadedDatasets.length > 0 && config.datasetAdapter)) ? 'hover:scale-110 hover:-translate-y-1' : 'opacity-75 cursor-not-allowed'}`}
                >
                  {isOptimizing ? <Loader2 size={20} className="animate-spin" /> : <ArrowUp size={20} />}
                </button>

                {/* Tooltip for disabled state */}
                {activeMode === 'migrate' && prompt.trim() && (uploadedDatasets.length === 0 || !config.datasetAdapter) && (
                  <div className="absolute bottom-full right-0 mb-2 px-3 py-1 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap">
                    {uploadedDatasets.length === 0
                      ? 'Dataset required for migration'
                      : 'Select dataset adapter type'
                    }
                    <div className="absolute top-full right-3 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Configuration panel - always rendered but hidden when not in migrate mode */}
          <div className={activeMode === 'migrate' ? 'block' : 'hidden'}>
            <ConfigurationPanel onConfigChange={setConfig} config={config} />
          </div>
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
                  : "Upload a JSON dataset file for custom training data."}
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
