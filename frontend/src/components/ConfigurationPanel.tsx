import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';

export const ConfigurationPanel = () => {
  const [dataset, setDataset] = useState('Q&A');
  const [metrics, setMetrics] = useState('Exact Match');
  const [optimizer, setOptimizer] = useState('MiPro');
  const [taskModel, setTaskModel] = useState('Llama 3.3 70B');
  const [proposerModel, setProposerModel] = useState('Llama 3.3 70B');
  const [apiKey, setApiKey] = useState('');

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

  return (
    <Card className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-xl border border-facebook-border p-10 max-w-4xl mx-auto">
      <h2 className="text-3xl font-black text-facebook-text mb-10 text-center">Configuration</h2>

      <ToggleGroup
        title="Dataset"
        options={['Q&A', 'RAG', 'Custom']}
        selected={dataset}
        onSelect={setDataset}
      />

      <ToggleGroup
        title="Metrics"
        options={['Exact Match', 'Standard JSON', 'Custom']}
        selected={metrics}
        onSelect={setMetrics}
      />

      <ToggleGroup
        title="Optimizer"
        options={['MiPro', 'GEPA', 'Infer']}
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
              <SelectItem value="Llama 3.3 70B" className="text-facebook-text hover:bg-facebook-gray">Llama 3.3 70B</SelectItem>
              <SelectItem value="Llama 3.1 8B" className="text-facebook-text hover:bg-facebook-gray">Llama 3.1 8B</SelectItem>
              <SelectItem value="Llama 2 13B" className="text-facebook-text hover:bg-facebook-gray">Llama 2 13B</SelectItem>
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
              <SelectItem value="Llama 3.3 70B" className="text-facebook-text hover:bg-facebook-gray">Llama 3.3 70B</SelectItem>
              <SelectItem value="Llama 3.1 8B" className="text-facebook-text hover:bg-facebook-gray">Llama 3.1 8B</SelectItem>
              <SelectItem value="Llama 2 13B" className="text-facebook-text hover:bg-facebook-gray">Llama 2 13B</SelectItem>
            </SelectContent>
          </Select>
        </div>
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
      </div>
    </Card>
  );
};
