import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Github, Sun, Moon, Monitor, Play, Book, ArrowRight } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

// Video files to cycle through (clean, URL-safe naming)
const videoFiles = [
  '/hero-video-1.mp4',
  '/hero-video-2.mp4',
  '/hero-video-3.mp4',
  '/hero-video-4.mp4',
  '/hero-video-5.mp4',
  '/hero-video-6.mp4',
  '/hero-video-7.mp4',
];

const Home = () => {
  const { theme, setTheme } = useTheme();
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const preloadRef = useRef<HTMLVideoElement>(null);

  // Set page title and meta description
  useEffect(() => {
    document.title = 'prompt-ops | AI-Powered Prompt Optimization';
    
    // Update or create meta description
    let metaDescription = document.querySelector('meta[name="description"]');
    if (!metaDescription) {
      metaDescription = document.createElement('meta');
      metaDescription.setAttribute('name', 'description');
      document.head.appendChild(metaDescription);
    }
    metaDescription.setAttribute('content', 'Optimize your prompts with AI-powered strategies. prompt-ops helps you enhance LLM prompts for better results.');

    return () => {
      document.title = 'prompt-ops';
    };
  }, []);

  // Cycle to next video when current one ends
  const handleVideoEnded = () => {
    setCurrentVideoIndex((prev) => (prev + 1) % videoFiles.length);
  };

  // Update video source when index changes
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.load();
      videoRef.current.play().catch(() => {
        // Autoplay may be blocked, that's okay
      });
    }
  }, [currentVideoIndex]);

  // Preload next video for smooth transitions
  useEffect(() => {
    const nextIndex = (currentVideoIndex + 1) % videoFiles.length;
    if (preloadRef.current) {
      preloadRef.current.src = videoFiles[nextIndex];
      preloadRef.current.load();
    }
  }, [currentVideoIndex]);

  return (
    <div className="fixed inset-0 w-screen h-screen overflow-hidden bg-black">
      {/* Hidden video element for preloading next video */}
      <video
        ref={preloadRef}
        className="hidden"
        muted
        playsInline
        preload="auto"
      />

      {/* Background Video */}
      <video
        ref={videoRef}
        className="absolute inset-0 w-full h-full object-cover animate-fade-in"
        autoPlay
        muted
        playsInline
        onEnded={handleVideoEnded}
      >
        <source src={videoFiles[currentVideoIndex]} type="video/mp4" />
      </video>

      {/* Dark Overlay */}
      <div className="absolute inset-0 video-overlay" />

      {/* Top Navigation */}
      <nav className="absolute top-0 left-0 right-0 z-20 px-8 py-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo */}
          <Link
            to="/"
            className="text-white font-bold text-2xl tracking-tight hover:text-meta-blue transition-colors duration-200"
          >
            prompt-ops
          </Link>

          {/* Right Nav */}
          <div className="flex items-center gap-4">
            <Link
              to="/playground"
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-base font-medium text-white/80 hover:text-white hover:bg-white/10 transition-all duration-200"
            >
              <Play size={18} />
              <span>Playground</span>
            </Link>

            <Link
              to="/docs"
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-base font-medium text-white/80 hover:text-white hover:bg-white/10 transition-all duration-200"
            >
              <Book size={18} />
              <span>Docs</span>
            </Link>

            <a
              href="https://github.com/meta-llama/prompt-ops"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-base font-medium text-white/80 hover:text-white hover:bg-white/10 transition-all duration-200"
            >
              <Github size={18} />
              <span>GitHub</span>
            </a>

            {/* Theme Toggle */}
            <div className="flex items-center gap-1 bg-white/10 backdrop-blur-sm p-1 rounded-full border border-white/20">
              <button
                onClick={() => setTheme('light')}
                className={`p-2 rounded-full transition-colors ${
                  theme === 'light'
                    ? 'bg-white/20 text-white'
                    : 'text-white/60 hover:text-white'
                }`}
                title="Light mode"
              >
                <Sun size={16} />
              </button>
              <button
                onClick={() => setTheme('dark')}
                className={`p-2 rounded-full transition-colors ${
                  theme === 'dark'
                    ? 'bg-white/20 text-white'
                    : 'text-white/60 hover:text-white'
                }`}
                title="Dark mode"
              >
                <Moon size={16} />
              </button>
              <button
                onClick={() => setTheme('system')}
                className={`p-2 rounded-full transition-colors ${
                  theme === 'system'
                    ? 'bg-white/20 text-white'
                    : 'text-white/60 hover:text-white'
                }`}
                title="System preference"
              >
                <Monitor size={16} />
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Content - Centered */}
      <div className="absolute inset-0 z-10 flex flex-col items-center justify-center px-8">
        {/* Product Name */}
        <h1 className="text-7xl md:text-8xl lg:text-9xl font-semibold text-white tracking-tight animate-fade-in-up-delay-1">
          prompt-ops
        </h1>

        {/* Tagline */}
        <p className="mt-6 text-xl md:text-2xl lg:text-3xl text-white/80 font-light tracking-wide animate-fade-in-up-delay-2">
          AI-powered prompt optimization
        </p>

        {/* CTA Button */}
        <Link
          to="/playground"
          className="mt-12 group animate-fade-in-up-delay-3"
        >
          <div className="flex items-center gap-3 px-8 py-4 bg-meta-blue text-white text-lg font-medium rounded-full hover:bg-meta-blue-hover transition-all duration-300 animate-pulse-glow">
            <span>Try it</span>
            <ArrowRight
              size={20}
              className="group-hover:translate-x-1 transition-transform duration-300"
            />
          </div>
        </Link>
      </div>

    </div>
  );
};

export default Home;
