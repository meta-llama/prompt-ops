# Llama Prompt Ops - Frontend

A modern React frontend interface for [llama-prompt-ops](https://github.com/meta-llama/llama-prompt-ops), providing an intuitive web interface for prompt optimization workflows.

## Features

- **Prompt Enhancement**: Optimize prompts for better performance with Llama models
- **Prompt Migration**: Migrate prompts between different model architectures
- **Real-time Optimization**: Monitor optimization progress with live updates
- **Configuration Management**: Flexible configuration for different optimization strategies
- **Clean UI**: Modern, accessible interface with Meta's design language

## Technology Stack

- **Frontend**: React 18 + TypeScript
- **UI Components**: Radix UI + shadcn/ui
- **Styling**: Tailwind CSS with Meta/Facebook design system
- **Build Tool**: Vite
- **Backend Integration**: FastAPI (for development)

## Development Setup

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+ (for backend development)

### Frontend Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The frontend will be available at `http://localhost:8080`

### Backend Development (Optional)

If you need to run the development backend:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn main:app --reload --port 8000
```

## Integration with llama-prompt-ops

This frontend is designed to integrate with the main llama-prompt-ops library. It provides:

- Web interface for prompt optimization workflows
- Visual configuration for optimization parameters
- Real-time progress tracking and results display
- Easy export/import of optimization configurations

## Project Structure

```
src/
├── components/           # React components
│   ├── ui/              # Reusable UI components (shadcn/ui)
│   ├── Sidebar.tsx      # Navigation component
│   ├── MainContent.tsx  # Main application content
│   ├── PromptInput.tsx  # Prompt input and optimization
│   └── ...
├── context/             # React context providers
├── hooks/               # Custom React hooks
├── pages/               # Page components
└── lib/                 # Utility functions
```

## Contributing

This project follows the llama-prompt-ops contribution guidelines. Please see the main repository for details on:

- Code style and formatting
- Testing requirements
- Pull request process
- Issue reporting

## License

This project is licensed under the same terms as llama-prompt-ops. See the main repository for license details.

## Future Plans

This frontend will eventually be integrated into the main llama-prompt-ops repository under `llama-prompt-ops/frontend/` to provide a unified development experience.
