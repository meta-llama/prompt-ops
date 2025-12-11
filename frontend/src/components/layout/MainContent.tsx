import React, { useContext, useEffect, useState } from 'react';
import { AppContext } from '../../context/AppContext';
import { apiUrl } from '@/lib/config';
import { PromptInput } from '../optimization/PromptInput';
import { DocsTab } from '../docs/DocsTab';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Lock, Folder, FileText, Database, Calendar } from 'lucide-react';

interface Project {
  name: string;
  path: string;
  hasConfig: boolean;
  hasPrompt: boolean;
  hasDataset: boolean;
  createdAt: number;
  modifiedAt: number;
}

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
          <h1 className="text-6xl md:text-7xl font-black text-facebook-text mb-8 tracking-tight leading-none">
            Optimize your
            <br />
            <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
              prompt
            </span>
          </h1>
        </div>

        {/* Projects List Section */}
        {!loadingProjects && projects.length > 0 && (
          <div className="mb-12">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-3xl font-bold text-facebook-text">
                Your Projects
              </h2>
              <Badge variant="outline" className="text-sm">
                {projects.length} {projects.length === 1 ? 'project' : 'projects'}
              </Badge>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {projects.map((project) => (
                <div
                  key={project.name}
                  className="bg-white/80 backdrop-blur-sm border border-facebook-border rounded-xl p-6 hover:shadow-lg transition-all duration-200 hover:border-facebook-blue/30"
                >
                  <div className="flex items-start gap-3 mb-4">
                    <div className="p-2 bg-facebook-blue/10 rounded-lg">
                      <Folder className="text-facebook-blue" size={24} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-lg text-facebook-text truncate">
                        {project.name}
                      </h3>
                      <div className="flex items-center gap-1 text-xs text-facebook-text/60 mt-1">
                        <Calendar size={12} />
                        <span>
                          {new Date(project.modifiedAt * 1000).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 mb-4">
                    {project.hasConfig && (
                      <Badge variant="secondary" className="text-xs bg-green-100 text-green-700 border-green-200">
                        <FileText size={12} className="mr-1" />
                        Config
                      </Badge>
                    )}
                    {project.hasPrompt && (
                      <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-700 border-blue-200">
                        <FileText size={12} className="mr-1" />
                        Prompt
                      </Badge>
                    )}
                    {project.hasDataset && (
                      <Badge variant="secondary" className="text-xs bg-purple-100 text-purple-700 border-purple-200">
                        <Database size={12} className="mr-1" />
                        Dataset
                      </Badge>
                    )}
                  </div>

                  <Button
                    variant="outline"
                    className="w-full text-sm"
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

        {!loadingProjects && projects.length === 0 && (
          <div className="mb-12 text-center p-12 bg-white/50 backdrop-blur-sm border border-facebook-border rounded-xl">
            <Folder className="mx-auto mb-4 text-facebook-text/30" size={48} />
            <h3 className="text-xl font-semibold text-facebook-text/60 mb-2">
              No projects yet
            </h3>
            <p className="text-facebook-text/40">
              Create your first project to get started!
            </p>
          </div>
        )}

        {/* Mode Toggle - Only Migrate and Enhance */}
        <div className="flex justify-center mb-8">
          <div className="bg-white p-1 rounded-xl shadow-lg border border-facebook-border relative">
            {/* Container using CSS Grid for equal button widths */}
            <div className="grid grid-cols-2 gap-1 relative">
              {/* Sliding indicator with Facebook blue gradient */}
              <div
                className={`absolute top-0 bottom-0 rounded-lg transition-all duration-300 ease-in-out ${
                  activeMode === 'migrate'
                    ? 'left-0 right-1/2 mr-0.5'
                    : 'left-1/2 right-0 ml-0.5'
                }`}
                style={{
                  background: 'linear-gradient(135deg, hsl(var(--facebook-blue)), hsl(var(--facebook-blue-light)))'
                }}
              />

              {/* Lock icon when mode is locked */}
              {isModeLocked && (
                <div className="absolute -top-2 -right-2 bg-facebook-text/80 rounded-full p-1 shadow-lg z-20">
                  <Lock size={14} className="text-white" />
                </div>
              )}

              <Button
                onClick={() => !isModeLocked && setActiveMode('migrate')}
                variant="ghost"
                disabled={isModeLocked}
                className={`relative w-full px-8 py-3 text-lg font-medium z-10 transition-all duration-300 rounded-lg hover:bg-transparent ${
                  activeMode === 'migrate'
                    ? 'text-white hover:text-white'
                    : 'text-facebook-text hover:text-facebook-text'
                } ${isModeLocked ? 'cursor-not-allowed' : ''}`}
              >
                Migrate
              </Button>

              <Button
                onClick={() => !isModeLocked && setActiveMode('enhance')}
                variant="ghost"
                disabled={isModeLocked}
                className={`relative w-full px-8 py-3 text-lg font-medium z-10 transition-all duration-300 rounded-lg hover:bg-transparent ${
                  activeMode === 'enhance'
                    ? 'text-white hover:text-white'
                    : 'text-facebook-text hover:text-facebook-text'
                } ${isModeLocked ? 'cursor-not-allowed' : ''}`}
              >
                <div className="flex items-center justify-center gap-2">
                  Enhance
                  <Badge
                    variant="secondary"
                    className="text-xs px-2 py-0.5 bg-orange-100 text-orange-600 border-orange-200 hover:bg-orange-100"
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
