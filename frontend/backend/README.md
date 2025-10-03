# Llama Prompt Ops Frontend Backend

This is a FastAPI backend for the llama-prompt-ops frontend interface. It provides API endpoints for optimizing prompts using OpenAI's GPT models and the llama-prompt-ops library.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
   - Copy `.env.example` to `.env` (if available)
   - Add your OpenAI API key and OpenRouter API key to the `.env` file

## Running the Server

Start the FastAPI server with:
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at http://localhost:8000

## API Endpoints

### POST /api/enhance-prompt

Enhances a prompt using OpenAI's GPT model.

**Request Body:**
```json
{
  "prompt": "Your prompt text here"
}
```

**Response:**
```json
{
  "optimizedPrompt": "Enhanced prompt text"
}
```

### POST /api/migrate-prompt

Optimizes a prompt using the llama-prompt-ops library.

**Request Body:**
```json
{
  "prompt": "Your prompt text here",
  "config": {
    "taskModel": "Llama 3.3 70B",
    "proposerModel": "Llama 3.1 8B",
    "optimizer": "MiPro",
    "dataset": "Q&A",
    "metrics": "Exact Match",
    "useLlamaTips": true
  }
}
```

**Response:**
```json
{
  "optimizedPrompt": "Optimized prompt text"
}
```

## Integration with llama-prompt-ops

This backend serves as a development interface for the llama-prompt-ops library, providing web API access to prompt optimization features. When this frontend is eventually integrated into the main llama-prompt-ops repository, this backend functionality will be incorporated into the library's core API structure.
