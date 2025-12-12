import { useEffect, useContext } from 'react';
import { useLocation } from 'react-router-dom';
import { Sidebar } from '../components/layout/Sidebar';
import { MainContent } from '../components/layout/MainContent';
import { AppContext } from '../context/AppContext';

const Index = () => {
  const location = useLocation();
  const { setActiveMode } = useContext(AppContext)!;

  useEffect(() => {
    // Set active mode based on the current URL path
    if (location.pathname.startsWith('/docs')) {
      setActiveMode('docs');
    } else {
      // Default to migrate mode for home page
      setActiveMode('migrate');
    }
  }, [location.pathname, setActiveMode]);

  return (
    <div className="min-h-screen w-full bg-background relative overflow-hidden">
      {/* Clean background */}
      <div className="absolute inset-0 bg-meta-gray-100/50"></div>

      {/* Top Navigation */}
      <Sidebar />

      {/* Main Content */}
      <MainContent />
    </div>
  );
};

export default Index;
