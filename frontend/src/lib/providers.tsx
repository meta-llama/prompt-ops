import React from "react";
import { Globe, Zap, Shield, Server, Brain, Settings } from "lucide-react";

export interface ProviderInfo {
  id: string;
  name: string;
  icon: React.ReactNode;
}

/**
 * Provider configuration for consistent icon and name display across the app.
 */
export const PROVIDERS: Record<string, ProviderInfo> = {
  openrouter: {
    id: "openrouter",
    name: "OpenRouter",
    icon: <Globe className="w-5 h-5 text-blue-600" />,
  },
  together: {
    id: "together",
    name: "Together AI",
    icon: <Zap className="w-5 h-5 text-purple-600" />,
  },
  anthropic: {
    id: "anthropic",
    name: "Anthropic",
    icon: <Shield className="w-5 h-5 text-orange-600" />,
  },
  openai: {
    id: "openai",
    name: "OpenAI",
    icon: <Brain className="w-5 h-5 text-meta-teal" />,
  },
  vllm: {
    id: "vllm",
    name: "vLLM",
    icon: <Server className="w-5 h-5 text-gray-600" />,
  },
  ollama: {
    id: "ollama",
    name: "Ollama",
    icon: <Server className="w-5 h-5 text-gray-600" />,
  },
  nvidia_nim: {
    id: "nvidia_nim",
    name: "NVIDIA NIM",
    icon: <Shield className="w-5 h-5 text-green-600" />,
  },
  custom: {
    id: "custom",
    name: "Custom Provider",
    icon: <Settings className="w-5 h-5 text-indigo-600" />,
  },
};

/**
 * Get the icon for a provider by ID.
 */
export const getProviderIcon = (providerId: string): React.ReactNode => {
  return PROVIDERS[providerId]?.icon ?? <Globe className="w-5 h-5 text-gray-600" />;
};

/**
 * Get the display name for a provider by ID.
 * Optionally pass a custom name for custom providers.
 */
export const getProviderName = (providerId: string, customName?: string): string => {
  if (providerId === "custom" && customName) {
    return customName;
  }
  return PROVIDERS[providerId]?.name ?? providerId.replace("_", " ");
};
