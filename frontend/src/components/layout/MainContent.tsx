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
          <h1 className="text-3xl md:text-4xl font-normal text-foreground mb-8 tracking-tight">
            Optimize your prompt
          </h1>
        </div>

        {/* Projects List Section - TEMPORARILY HIDDEN */}
        {/* Will be re-enabled later with project management features */}
        {false && !loadingProjects && projects.length > 0 && (
          <div className="mb-12">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl md:text-3xl font-normal text-foreground tracking-tight">
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
                  className="bg-panel border border-border rounded-2xl p-6 hover:border-meta-blue/30 transition-colors"
                >
                  <div className="flex items-start gap-3 mb-4">
                    <div className="p-2 bg-meta-blue/10 rounded-xl">
                      <Folder className="text-meta-blue" size={24} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-lg text-foreground truncate">
                        {project.name}
                      </h3>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
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
          <div className="mb-12 text-center p-12 bg-panel border border-border rounded-3xl">
            <Folder className="mx-auto mb-4 text-muted-foreground/50" size={48} />
            <h3 className="text-xl font-semibold text-muted-foreground mb-2">
              No projects yet
            </h3>
            <p className="text-muted-foreground/70">
              Create your first project to get started!
            </p>
          </div>
        )}

        {/* Mode Toggle - Optimize and Enhance */}
        <div className="flex justify-center mb-8">
          <div className="bg-muted p-1 rounded-full border border-border relative">
            {/* Container using CSS Grid for equal button widths */}
            <div className="grid grid-cols-2 gap-1 relative">
              {/* Sliding indicator */}
              <div
                className={`absolute top-0 bottom-0 rounded-full transition-all duration-300 ease-in-out bg-meta-blue ${
                  activeMode === 'migrate'
                    ? 'left-0 right-1/2 mr-0.5'
                    : 'left-1/2 right-0 ml-0.5'
                }`}
              />

              {/* Lock icon when mode is locked */}
              {isModeLocked && (
                <div className="absolute -top-2 -right-2 bg-foreground rounded-full p-1 z-20">
                  <Lock size={14} className="text-background" />
                </div>
              )}

              <Button
                onClick={() => !isModeLocked && setActiveMode('migrate')}
                variant="ghost"
                disabled={isModeLocked}
                className={`relative w-full px-8 py-3 text-lg font-medium z-10 transition-colors rounded-full hover:bg-transparent ${
                  activeMode === 'migrate'
                    ? 'text-white hover:text-white dark:text-meta-gray-900 dark:hover:text-meta-gray-900'
                    : 'text-foreground hover:text-foreground'
                } ${isModeLocked ? 'cursor-not-allowed' : ''}`}
              >
                Optimize
              </Button>

              <Button
                onClick={() => !isModeLocked && setActiveMode('enhance')}
                variant="ghost"
                disabled={isModeLocked}
                className={`relative w-full px-8 py-3 text-lg font-medium z-10 transition-colors rounded-full hover:bg-transparent ${
                  activeMode === 'enhance'
                    ? 'text-white hover:text-white dark:text-meta-gray-900 dark:hover:text-meta-gray-900'
                    : 'text-foreground hover:text-foreground'
                } ${isModeLocked ? 'cursor-not-allowed' : ''}`}
              >
                <div className="flex items-center justify-center gap-2">
                  Enhance
                  <Badge
                    variant="warning"
                    className="bg-meta-orange text-white border-meta-orange"
                  >
                    Experimental
                  </Badge>
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
