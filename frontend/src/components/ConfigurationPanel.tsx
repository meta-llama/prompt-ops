import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Loader2, Eye } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';

// Define types for the configuration
interface Configurations {
  models: Record<string, string>;
  metrics: Record<string, any>;
  dataset_adapters: Record<string, any>;  // Changed from datasets to dataset_adapters
  strategies: Record<string, string>;
}

interface DatasetInfo {
  name: string;
  preview?: any[];
  total_records?: number;
  is_uploaded?: boolean;
}

export const ConfigurationPanel = ({ onConfigChange = null }) => {
  const [datasetAdapter, setDatasetAdapter] = useState('');  // Changed from dataset to datasetAdapter
  const [metrics, setMetrics] = useState('Exact Match');
  const [optimizer, setOptimizer] = useState('MiPro');
  const [taskModel, setTaskModel] = useState('Llama 3.3 70B');
  const [proposerModel, setProposerModel] = useState('Llama 3.3 70B');
  const [apiKey, setApiKey] = useState('');
  const [useLlamaTips, setUseLlamaTips] = useState(true);

  // Add state for configurations
  const [configurations, setConfigurations] = useState<Configurations | null>(null);
  const [isLoadingConfigs, setIsLoadingConfigs] = useState(false);
  const [configError, setConfigError] = useState<string | null>(null);

  // Add state for dataset preview
  const [showDatasetPreview, setShowDatasetPreview] = useState(false);
  const [selectedDatasetInfo, setSelectedDatasetInfo] = useState<DatasetInfo | null>(null);

  // Notify parent component when configuration changes
  useEffect(() => {
    if (onConfigChange) {
      onConfigChange({
        datasetAdapter,  // Send as datasetAdapter
        metrics,
        strategy: optimizer,
        model: taskModel,
        proposer: proposerModel,
        openrouterApiKey: apiKey || undefined,
        useLlamaTips
      });
    }
  }, [datasetAdapter, metrics, optimizer, taskModel, proposerModel, apiKey, useLlamaTips, onConfigChange]);

  // Handle dataset preview
  const handleDatasetPreview = (datasetName: string) => {
    const datasetInfo = configurations?.dataset_adapters[datasetName];
    if (datasetInfo) {
      setSelectedDatasetInfo({
        name: datasetName,
        preview: datasetInfo.preview || [],
        total_records: datasetInfo.total_records || 0,
        is_uploaded: datasetInfo.is_uploaded || false,
      });
      setShowDatasetPreview(true);
    }
  };

  const fetchConfigurations = async () => {
    setIsLoadingConfigs(true);
    setConfigError(null);

    try {
      const response = await fetch('http://localhost:8000/api/configurations');

      if (!response.ok) {
        throw new Error(`Failed to fetch configurations: ${response.statusText}`);
      }

      const data = await response.json();
      setConfigurations(data);

      // Set defaults based on available options
      if (data.models && Object.keys(data.models).length > 0) {
        const modelOptions = Object.keys(data.models);
        if (!modelOptions.includes(taskModel)) {
          setTaskModel(modelOptions[0]);
        }
        if (!modelOptions.includes(proposerModel)) {
          setProposerModel(modelOptions[0]);
        }
      }

      if (data.strategies && Object.keys(data.strategies).length > 0) {
        const strategyOptions = Object.keys(data.strategies);
        if (!strategyOptions.includes(optimizer)) {
          setOptimizer(strategyOptions[0]);
        }
      }

      if (data.dataset_adapters && Object.keys(data.dataset_adapters).length > 0) {
        const datasetOptions = Object.keys(data.dataset_adapters);
        if (!datasetOptions.includes(datasetAdapter)) { // Changed from dataset to datasetAdapter
          setDatasetAdapter(datasetOptions[0]); // Changed from dataset to datasetAdapter
        }
      }

      if (data.metrics && Object.keys(data.metrics).length > 0) {
        const metricOptions = Object.keys(data.metrics);
        if (!metricOptions.includes(metrics)) {
          setMetrics(metricOptions[0]);
        }
      }
    } catch (error) {
      console.error('Error fetching configurations:', error);
      setConfigError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setIsLoadingConfigs(false);
    }
  };

  // Fetch configurations from backend
  useEffect(() => {
    fetchConfigurations();
  }, []);

  const ToggleGroup = ({ title, options, selected, onSelect }) => (
    <div className="mb-8">
      <h3 className="text-facebook-text font-bold mb-4 text-xl">{title}</h3>
      <div className="flex gap-3 flex-wrap">
        {options.map((option) => (
          <Button
            key={option}
            onClick={() => onSelect(option)}
            className={`px-6 py-3 rounded-xl font-semibold transition-all duration-300 transform hover:scale-105 ${
              selected === option
                ? 'bg-facebook-blue hover:bg-facebook-blue-dark text-white shadow-lg shadow-facebook-blue/25'
                : 'bg-facebook-gray text-facebook-text hover:bg-facebook-border border border-facebook-border'
            }`}
          >
            {option}
          </Button>
        ))}
      </div>
    </div>
  );

  if (isLoadingConfigs) {
    return (
      <Card className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-xl border border-facebook-border p-10 max-w-4xl mx-auto flex items-center justify-center">
        <div className="text-center">
          <Loader2 size={40} className="animate-spin mx-auto mb-4 text-facebook-blue" />
          <p className="text-facebook-text text-lg">Loading configurations...</p>
        </div>
      </Card>
    );
  }

  if (configError) {
    return (
      <Card className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-xl border border-facebook-border p-10 max-w-4xl mx-auto">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Configuration Error</h2>
          <p className="text-facebook-text mb-4">{configError}</p>
          <Button
            onClick={() => window.location.reload()}
            className="bg-facebook-blue hover:bg-facebook-blue-dark text-white"
          >
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-xl border border-facebook-border p-10 max-w-4xl mx-auto">
      <h2 className="text-3xl font-black text-facebook-text mb-10 text-center">Configuration</h2>

      {configurations && (
        <>
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-facebook-text font-bold text-xl">Dataset Adapter Type</h3>
            </div>

            {/* Dataset adapter selection warning */}
            {!datasetAdapter && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-600 text-sm">
                  Please select a dataset adapter type that matches your uploaded dataset structure.
                </p>
              </div>
            )}

            {/* Dataset Adapter Types as Toggle Group */}
            {configurations.dataset_adapters && Object.keys(configurations.dataset_adapters).length > 0 && (
              <div className="flex gap-3 flex-wrap">
                {Object.entries(configurations.dataset_adapters).map(([adapterName, adapterInfo]) => (
                  <Button
                    key={adapterName}
                    onClick={() => setDatasetAdapter(adapterName)}
                    className={`px-6 py-3 rounded-xl font-semibold transition-all duration-300 transform hover:scale-105 ${
                      datasetAdapter === adapterName
                        ? 'bg-facebook-blue hover:bg-facebook-blue-dark text-white shadow-lg shadow-facebook-blue/25'
                        : 'bg-facebook-gray text-facebook-text hover:bg-facebook-border border border-facebook-border'
                    }`}
                  >
                    {adapterName}
                  </Button>
                ))}
              </div>
            )}
          </div>

          <ToggleGroup
            title="Metrics"
            options={Object.keys(configurations.metrics || {'Exact Match': {}})}
            selected={metrics}
            onSelect={setMetrics}
          />

          <ToggleGroup
            title="Optimizer"
            options={Object.keys(configurations.strategies || {'MiPro': 'basic'})}
            selected={optimizer}
            onSelect={setOptimizer}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
            <div>
              <h3 className="text-facebook-text font-bold mb-4 text-xl">Task Model</h3>
              <Select value={taskModel} onValueChange={setTaskModel}>
                <SelectTrigger className="w-full h-14 rounded-xl bg-facebook-gray border-facebook-border text-facebook-text text-lg">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white border-facebook-border rounded-xl">
                  {configurations.models && Object.keys(configurations.models).map(model => (
                    <SelectItem key={model} value={model} className="text-facebook-text hover:bg-facebook-gray">
                      {model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <h3 className="text-facebook-text font-bold mb-4 text-xl">Proposer Model</h3>
              <Select value={proposerModel} onValueChange={setProposerModel}>
                <SelectTrigger className="w-full h-14 rounded-xl bg-facebook-gray border-facebook-border text-facebook-text text-lg">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white border-facebook-border rounded-xl">
                  {configurations.models && Object.keys(configurations.models).map(model => (
                    <SelectItem key={model} value={model} className="text-facebook-text hover:bg-facebook-gray">
                      {model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="mb-8">
            <div className="flex items-center mb-4">
              <input
                type="checkbox"
                id="useLlamaTips"
                checked={useLlamaTips}
                onChange={(e) => setUseLlamaTips(e.target.checked)}
                className="mr-2 h-5 w-5"
              />
              <label htmlFor="useLlamaTips" className="text-facebook-text font-bold text-xl">
                Use Llama Tips
              </label>
            </div>
            <p className="text-facebook-text/70">
              Include Llama-specific best practices in the optimization process
            </p>
          </div>

          <div>
            <h3 className="text-facebook-text font-bold mb-4 text-xl">Openrouter API Key</h3>
            <Input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your Openrouter API key..."
              className="w-full h-14 rounded-xl bg-facebook-gray border-facebook-border text-facebook-text placeholder:text-facebook-text/50 text-lg"
            />
            <p className="text-facebook-text/70 mt-2">
              Optional: If not provided, the system will use the API key configured on the server
            </p>
          </div>
        </>
      )}

      {/* Dataset Preview Dialog */}
      <Dialog open={showDatasetPreview} onOpenChange={setShowDatasetPreview}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Dataset Preview: {selectedDatasetInfo?.name}</DialogTitle>
            <DialogDescription>
              {selectedDatasetInfo?.is_uploaded
                ? `Showing first ${Math.min(selectedDatasetInfo.preview?.length || 0, selectedDatasetInfo.total_records || 0)} of ${selectedDatasetInfo.total_records} records`
                : `Built-in dataset type - ${configurations?.dataset_adapters[selectedDatasetInfo?.name]?.description || 'No description available'}`
              }
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="h-[500px] w-full rounded-md border p-4">
            {selectedDatasetInfo?.is_uploaded ? (
              // Show actual data preview for uploaded datasets
              selectedDatasetInfo.preview && selectedDatasetInfo.preview.length > 0 ? (
                <div className="space-y-4">
                  {selectedDatasetInfo.preview.map((record, index) => (
                    <div key={index} className="p-4 bg-facebook-gray rounded-lg border border-facebook-border">
                      <div className="font-medium text-facebook-text mb-2">Record {index + 1}</div>
                      <pre className="text-sm text-facebook-text/80 whitespace-pre-wrap overflow-x-auto">
                        {JSON.stringify(record, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-facebook-text/70 py-8">
                  No preview available for this dataset
                </div>
              )
            ) : (
              // Show information about built-in dataset types
              <div className="space-y-6">
                <div className="p-4 bg-facebook-blue/10 rounded-lg border border-facebook-blue/20">
                  <h3 className="font-semibold text-facebook-text mb-2">Dataset Type Information</h3>
                  <p className="text-facebook-text/80 mb-4">
                    {configurations?.dataset_adapters[selectedDatasetInfo?.name]?.description}
                  </p>
                  <div className="space-y-2">
                    <h4 className="font-medium text-facebook-text">Expected Fields:</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {Object.entries(configurations?.dataset_adapters[selectedDatasetInfo?.name]?.example_fields || {}).map(([field, type]) => (
                        <div key={field} className="flex justify-between p-2 bg-white rounded border">
                          <span className="font-mono text-sm">{field}</span>
                          <span className="text-sm text-facebook-text/60">{String(type)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                  <h4 className="font-medium text-yellow-800 mb-2">📋 To Use This Dataset Type:</h4>
                  <ol className="text-sm text-yellow-700 space-y-1 list-decimal list-inside">
                    <li>Upload a JSON file with the expected fields shown above</li>
                    <li>Ensure your data matches the field structure</li>
                    <li>Select this dataset type for optimization</li>
                  </ol>
                </div>

                <div className="p-4 bg-facebook-gray/30 rounded-lg border border-facebook-border">
                  <h4 className="font-medium text-facebook-text mb-2">Example JSON Structure:</h4>
                  <pre className="text-sm text-facebook-text/80 whitespace-pre-wrap overflow-x-auto bg-white p-3 rounded border">
                    {(() => {
                      const exampleData = [
                        Object.fromEntries(
                          Object.entries(configurations?.dataset_adapters[selectedDatasetInfo?.name]?.example_fields || {})
                            .map(([field, type]) => [field, `<${type as string}>`])
                        )
                      ];
                      return JSON.stringify(exampleData, null, 2);
                    })()}
                  </pre>
                </div>
              </div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </Card>
  );
};
