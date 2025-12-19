# Prompt Ops - Frontend

A modern React frontend interface for [prompt-ops](https://github.com/meta-llama/prompt-ops), providing an intuitive web interface for prompt optimization workflows.

## Features

- **Prompt Enhancement**: Optimize prompts for better performance with Llama models
- **Prompt Migration**: Migrate prompts between different model architectures
- **Real-time Optimization**: Monitor optimization progress with live updates
- **Dataset Management**: Upload and manage datasets for optimization
- **Configuration Management**: Flexible configuration for different optimization strategies
- **Clean UI**: Modern, accessible interface with Meta's design language

## Technology Stack

- **Frontend**: React 18 + TypeScript
- **UI Components**: Radix UI + shadcn/ui
- **Styling**: Tailwind CSS with Meta/Facebook design system
- **Build Tool**: Vite
- **Backend**: FastAPI with prompt-ops integration

## Quick Start

### Prerequisites

- **Node.js 18+** and npm
- **Python 3.8+** (for backend)
- **OpenRouter API Key** (get one at [OpenRouter](https://openrouter.ai/))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/meta-llama/prompt-ops.git
   cd prompt-ops/frontend
   ```

2. **Install frontend dependencies**
   ```bash
   npm install
   ```

3. **Set up backend environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the `frontend/backend` directory:
   ```bash
   # In frontend/backend/.env
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here  # Optional: for fallback enhance feature
   ```

### Running the Application

You'll need **two terminal windows** - one for the backend and one for the frontend.

**Terminal 1 - Backend:**
```bash
cd frontend/backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload --port 8001
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

### First Run

1. **Upload a dataset**: Click "Manage Dataset" and upload a JSON file with your training data
2. **Configure optimization**: Select your preferred model, metrics, and optimization strategy
3. **Enter your prompt**: Paste your existing prompt in the text area
4. **Click "Optimize"**: Watch the real-time progress and get your optimized prompt!

## Dataset Format

Upload JSON files in this format:
```json
[
  {
    "question": "Your input query here",
    "answer": "Expected response here"
  },
  {
    "question": "Another input query",
    "answer": "Another expected response"
  }
]
```

## Troubleshooting

### Common Issues

**Backend won't start:**
- Ensure you've activated the virtual environment: `source venv/bin/activate`
- Check that all requirements are installed: `pip install -r requirements.txt`
- Verify your API keys are set in the `.env` file

**Frontend can't connect to backend:**
- Make sure the backend is running on port 8001
- Check browser console for CORS errors
- Verify the backend URL in the frontend code

**Optimization fails:**
- Check that you've uploaded a valid dataset
- Verify your OpenRouter API key is correct
- Ensure your dataset has the expected format

**Port already in use:**
- Kill existing processes: `pkill -f "uvicorn\|vite"`
- Or use different ports in the configuration

## Development

### Frontend Development

```bash
# Start with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Backend Development

```bash
# Start with auto-reload
uvicorn main:app --reload --port 8001

# Run with debug logging
uvicorn main:app --reload --port 8001 --log-level debug
```

## Project Structure

```
frontend/
├── backend/                 # FastAPI backend
│   ├── main.py             # API server
│   ├── requirements.txt    # Python dependencies
│   └── uploaded_datasets/  # Dataset storage
├── src/
│   ├── components/         # React components
│   │   ├── ui/            # Reusable UI components
│   │   ├── ConfigurationPanel.tsx
│   │   ├── PromptInput.tsx
│   │   └── ...
│   ├── context/           # React context
│   ├── hooks/             # Custom hooks
│   └── pages/             # Page components
└── package.json
```

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new features
3. Update documentation for any changes
4. Ensure the application builds and runs successfully

## License

This project is licensed under the same terms as prompt-ops.
