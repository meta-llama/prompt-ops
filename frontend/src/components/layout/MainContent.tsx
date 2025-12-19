import React, { useContext, useEffect, useState } from 'react';
import { AppContext } from '../../context/AppContext';
import { apiUrl } from '@/lib/config';
import { PromptInput } from '../optimization/PromptInput';
import { DocsTab } from '../docs/DocsTab';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Lock, Folder, FileText, Database, Calendar } from 'lucide-react';
import type { Project } from '@/types';

export const MainContent = () => {
  const { activeMode, setActiveMode, isModeLocked } = useContext(AppContext)!;
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(true);

  // Fetch projects on component mount
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await fetch(apiUrl('/api/projects'));
        const data = await response.json();
        if (data.success) {
          setProjects(data.projects);
        }
      } catch (error) {
        console.error('Failed to fetch projects:', error);
      } finally {
        setLoadingProjects(false);
      }
    };

    fetchProjects();
  }, []);

  // If in docs mode, show only the docs content
  if (activeMode === 'docs') {
    return (
      <div className="relative z-10 flex-1 px-8 py-8">
        <DocsTab />
      </div>
    );
  }

  return (
    <div className="relative z-10 flex-1 px-8">
      <div className="max-w-5xl mx-auto">
        {/* Hero Section - Centered */}
        <div className="text-center mb-16 pt-12">
          <h1 className="text-3xl md:text-4xl font-normal text-white mb-8 tracking-tight">
            Optimize your prompt
          </h1>
        </div>

        {/* Projects List Section - TEMPORARILY HIDDEN */}
        {/* Will be re-enabled later with project management features */}
        {false && !loadingProjects && projects.length > 0 && (
          <div className="mb-12">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl md:text-3xl font-normal text-white tracking-tight">
                Your Projects
              </h2>
              <Badge variant="outline">
                {projects.length} {projects.length === 1 ? 'project' : 'projects'}
              </Badge>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {projects.map((project) => (
                <div
                  key={project.name}
                  className="bg-white/[0.03] border border-white/[0.1] rounded-2xl p-6 hover:border-[#4da3ff]/30 transition-colors"
                >
                  <div className="flex items-start gap-3 mb-4">
                    <div className="p-2 bg-[#4da3ff]/10 rounded-xl">
                      <Folder className="text-[#4da3ff]" size={24} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-lg text-white truncate">
                        {project.name}
                      </h3>
                      <div className="flex items-center gap-1 text-xs text-white/60 mt-1">
                        <Calendar size={12} />
                        <span>
                          {new Date(project.modifiedAt * 1000).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 mb-4">
                    {project.hasConfig && (
                      <Badge variant="success">
                        <FileText size={12} className="mr-1" />
                        Config
                      </Badge>
                    )}
                    {project.hasPrompt && (
                      <Badge variant="info">
                        <FileText size={12} className="mr-1" />
                        Prompt
                      </Badge>
                    )}
                    {project.hasDataset && (
                      <Badge variant="purple">
                        <Database size={12} className="mr-1" />
                        Dataset
                      </Badge>
                    )}
                  </div>

                  <Button
                    variant="outlined"
                    size="medium"
                    onClick={() => {
                      // TODO: Add project opening functionality
                      console.log('Open project:', project.name);
                    }}
                  >
                    Open Project
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {false && !loadingProjects && projects.length === 0 && (
          <div className="mb-12 text-center p-12 bg-white/[0.03] border border-white/[0.1] rounded-3xl">
            <Folder className="mx-auto mb-4 text-white/30" size={48} />
            <h3 className="text-xl font-semibold text-white/60 mb-2">
              No projects yet
            </h3>
            <p className="text-white/40">
              Create your first project to get started!
            </p>
          </div>
        )}

        {/* Mode Toggle - Optimize and Enhance (Glassmorphism) */}
        <div className="flex justify-center mb-8">
          <div className="bg-white/[0.08] backdrop-blur-xl p-1.5 rounded-full border border-white/[0.15] relative shadow-[0_8px_32px_rgba(0,0,0,0.12)] ring-1 ring-white/[0.05] ring-inset">
            {/* Container using CSS Grid for equal button widths */}
            <div className="grid grid-cols-2 gap-1 relative">
              {/* Sliding indicator - frosted glass style */}
              <div
                className={`absolute top-0.5 bottom-0.5 rounded-full transition-all duration-300 ease-out bg-white/[0.15] backdrop-blur-md border border-white/[0.2] shadow-[inset_0_1px_1px_rgba(255,255,255,0.1)] ${
                  activeMode === 'migrate'
                    ? 'left-0.5 right-1/2 mr-0.5'
                    : 'left-1/2 right-0 mr-0.5'
                }`}
              />

              {/* Lock icon when mode is locked */}
              {isModeLocked && (
                <div className="absolute -top-2 -right-2 bg-white/90 backdrop-blur-sm rounded-full p-1 z-20 shadow-lg">
                  <Lock size={14} className="text-[#0a0c10]" />
                </div>
              )}

              <Button
                onClick={() => !isModeLocked && setActiveMode('migrate')}
                variant="ghost"
                disabled={isModeLocked}
                className={`relative w-full px-8 py-2.5 text-sm font-medium z-10 transition-all duration-200 rounded-full hover:bg-transparent ${
                  activeMode === 'migrate'
                    ? 'text-white hover:text-white'
                    : 'text-white/50 hover:text-white/80'
                } ${isModeLocked ? 'cursor-not-allowed' : ''}`}
              >
                Optimize
              </Button>

              <Button
                onClick={() => !isModeLocked && setActiveMode('enhance')}
                variant="ghost"
                disabled={isModeLocked}
                className={`relative w-full px-8 py-2.5 text-sm font-medium z-10 transition-all duration-200 rounded-full hover:bg-transparent ${
                  activeMode === 'enhance'
                    ? 'text-white hover:text-white'
                    : 'text-white/50 hover:text-white/80'
                } ${isModeLocked ? 'cursor-not-allowed' : ''}`}
              >
                <div className="flex items-center justify-center gap-2">
                  Enhance
                  <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-white/[0.1] text-white/60 border border-white/[0.1]">
                    Beta
                  </span>
                </div>
              </Button>
            </div>
          </div>
        </div>

        {/* Prompt Input - Elevated and Centered */}
        <div className="mb-8">
          <PromptInput />
        </div>
      </div>
    </div>
  );
};
