import React from 'react';
import { Sidebar } from '../components/layout/Sidebar';
import { MainContent } from '../components/layout/MainContent';

const Index = () => {
  return (
    <div className="min-h-screen w-full bg-background relative overflow-hidden">
      {/* Clean gradient overlay with Meta's color palette */}
      <div className="absolute inset-0 bg-gradient-to-br from-white via-facebook-gray/30 to-facebook-blue/5"></div>

      {/* Subtle dot pattern for texture */}
      <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(circle_at_50%_50%,hsl(var(--facebook-text))_1px,transparent_1px)] bg-[length:24px_24px]"></div>

      {/* Top Navigation */}
      <Sidebar />

      {/* Main Content */}
      <MainContent />
    </div>
  );
};

export default Index;
