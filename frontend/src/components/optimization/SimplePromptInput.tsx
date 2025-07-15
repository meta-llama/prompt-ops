import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ExpandableSection } from '../shared/ExpandableSection';
import { FileText, Database, Target, Info } from 'lucide-react';

interface SimplePromptInputProps {
  onOptimize: (prompt: string) => void;
  isOptimizing: boolean;
}

export const SimplePromptInput: React.FC<SimplePromptInputProps> = ({ onOptimize, isOptimizing }) => {
  const [prompt, setPrompt] = useState('');
  const [config, setConfig] = useState({
    datasetPath: '',
    datasetType: 'json',
    metrics: ['accuracy'],
    modelProvider: 'openai',
    temperature: 0.7,
    maxTokens: 1000,
  });

  const canOptimize = prompt.trim() !== '';

  const handleOptimize = () => {
    if (canOptimize) {
      onOptimize(prompt);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Requirements Section */}
      <Card className="bg-facebook-blue/10 border border-facebook-blue/20 shadow-lg backdrop-blur-xl rounded-2xl">
        <CardHeader>
          <div className="flex items-center gap-3">
            <Info className="h-6 w-6 text-facebook-blue" />
            <CardTitle className="text-facebook-text font-bold text-xl">What You Need to Get Started</CardTitle>
          </div>
          <CardDescription className="text-facebook-text/80 text-base">
            Make sure you have these three items ready before optimizing your prompt
          </CardDescription>
        </CardHeader>
        <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Prompt Requirement */}
            <div className="p-4 rounded-xl border border-facebook-border bg-white/90 backdrop-blur-xl shadow-md hover:shadow-lg transition-all duration-300">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark">
                  <FileText className="h-4 w-4 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-sm mb-2 text-facebook-text">Your Prompt</h3>
                  <p className="text-xs text-facebook-text/70 mb-2">
                    The text you want to optimize
                  </p>
                  <div className="text-xs text-facebook-text/60">
                    Example: "Answer questions based on context..."
                  </div>
                </div>
              </div>
            </div>

            {/* Dataset Requirement */}
            <div className="p-4 rounded-xl border border-facebook-border bg-white/90 backdrop-blur-xl shadow-md hover:shadow-lg transition-all duration-300">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark">
                  <Database className="h-4 w-4 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-sm mb-2 text-facebook-text">Your Dataset</h3>
                  <p className="text-xs text-facebook-text/70 mb-2">
                    Test data for evaluation
                  </p>
                  <div className="text-xs text-facebook-text/60">
                    10-50 examples (JSON/CSV)
                  </div>
                </div>
              </div>
            </div>

            {/* Metrics Requirement */}
            <div className="p-4 rounded-xl border border-facebook-border bg-white/90 backdrop-blur-xl shadow-md hover:shadow-lg transition-all duration-300">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark">
                  <Target className="h-4 w-4 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-sm mb-2 text-facebook-text">Success Metrics</h3>
                  <p className="text-xs text-facebook-text/70 mb-2">
                    How to measure success
                  </p>
                  <div className="text-xs text-facebook-text/60">
                    Accuracy, relevance, etc.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Prompt Input */}
      <Card className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-xl border border-facebook-border">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-facebook-text">Enter Your Prompt</CardTitle>
          <CardDescription className="text-facebook-text/70 text-base">
            Paste or type the prompt you want to optimize
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="prompt" className="text-facebook-text font-semibold">Your Prompt</Label>
                         <Textarea
               id="prompt"
               placeholder="Enter your prompt here..."
               value={prompt}
               onChange={(e) => setPrompt(e.target.value)}
               className="min-h-[120px] text-sm bg-facebook-gray border-facebook-border rounded-xl focus:border-facebook-blue text-facebook-text placeholder:text-facebook-text/50"
             />
                         <div className="flex justify-between items-center text-sm text-facebook-text/70">
               <span>{prompt.length} characters</span>
               <span className="flex items-center gap-1 text-facebook-blue">
                 <Info className="h-3 w-3" />
                 Remember to prepare your dataset and metrics
               </span>
             </div>
          </div>

          {/* Quick Examples */}
          <div className="space-y-3">
            <Label className="text-sm font-semibold text-facebook-text">Quick Examples:</Label>
            <div className="grid grid-cols-1 gap-3">
              {[
                "Answer the following question based on the provided context. Be concise and accurate.",
                "Summarize the key points from the following document in 3-5 bullet points.",
                "Generate a helpful response that addresses the user's question while being informative and clear."
              ].map((example, index) => (
                                 <button
                   key={index}
                   onClick={() => setPrompt(example)}
                   className="p-3 text-left text-sm bg-facebook-gray hover:bg-facebook-blue hover:text-white rounded-xl border border-facebook-border transition-all duration-300 transform hover:scale-105 shadow-md text-facebook-text"
                 >
                  {example}
                </button>
              ))}
            </div>
          </div>

          {/* Configuration Section */}
          <ExpandableSection
            title="Configuration"
            defaultExpanded={false}
          >
            <div className="space-y-4 pt-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="dataset-path">Dataset Path</Label>
                  <Input
                    id="dataset-path"
                    placeholder="path/to/your/dataset.json"
                    value={config.datasetPath}
                    onChange={(e) => setConfig({...config, datasetPath: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="dataset-type">Dataset Type</Label>
                  <Select value={config.datasetType} onValueChange={(value) => setConfig({...config, datasetType: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="json">JSON</SelectItem>
                      <SelectItem value="csv">CSV</SelectItem>
                      <SelectItem value="jsonl">JSONL</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Metrics</Label>
                <div className="flex flex-wrap gap-2">
                  {['accuracy', 'relevance', 'completeness', 'consistency'].map((metric) => (
                    <Badge
                      key={metric}
                      variant={config.metrics.includes(metric) ? 'default' : 'outline'}
                      className="cursor-pointer"
                      onClick={() => {
                        const newMetrics = config.metrics.includes(metric)
                          ? config.metrics.filter(m => m !== metric)
                          : [...config.metrics, metric];
                        setConfig({...config, metrics: newMetrics});
                      }}
                    >
                      {metric}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="model-provider">Model Provider</Label>
                  <Select value={config.modelProvider} onValueChange={(value) => setConfig({...config, modelProvider: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="openai">OpenAI</SelectItem>
                      <SelectItem value="anthropic">Anthropic</SelectItem>
                      <SelectItem value="google">Google</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="temperature">Temperature: {config.temperature}</Label>
                  <input
                    id="temperature"
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={config.temperature}
                    onChange={(e) => setConfig({...config, temperature: parseFloat(e.target.value)})}
                    className="w-full"
                  />
                </div>
              </div>
            </div>
          </ExpandableSection>

          {/* Optimize Button */}
          <div className="flex justify-center pt-4">
            <Button
              onClick={handleOptimize}
              disabled={!canOptimize || isOptimizing}
              className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark hover:opacity-90 text-white px-8 py-4 text-lg font-bold rounded-2xl shadow-lg shadow-facebook-blue/25 transform hover:scale-105 transition-all duration-300"
            >
              {isOptimizing ? 'Optimizing...' : 'Optimize Prompt'}
            </Button>
          </div>

                               <Alert className="bg-facebook-blue/10 border-facebook-blue/20 shadow-lg rounded-xl">
            <Info className="h-4 w-4 text-facebook-blue" />
            <AlertDescription className="text-facebook-text font-medium">
              For best results, make sure you have your dataset and success metrics ready before optimizing your prompt.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  );
};
