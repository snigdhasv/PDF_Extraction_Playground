# Initial Setup Instructions - PDF Extraction Playground

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Modal account (sign up at https://modal.com for $30 free credit)
- Git

## Step 1: Project Setup

```bash
# Create project directory
mkdir pdf-extraction-playground
cd pdf-extraction-playground

# Create backend directory
mkdir backend
cd backend

# Initialize git repository
git init
```

## Step 2: Python Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

## Step 3: Install Dependencies

```bash
# Install requirements
pip install -r requirements.txt
```

## Step 4: Modal Setup

```bash
# Install Modal CLI (if not already installed)
pip install modal

# Authenticate with Modal
modal setup

# This will:
# 1. Open browser for authentication
# 2. Create API token
# 3. Save credentials locally
```

## Step 5: Create Environment File (Optional)

```bash
# Create .env file for local development
touch .env
```

Add the following to `.env`:

```
ENV=development
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=50
```

## Step 6: Test Local Development Server

```bash
# Run FastAPI locally
python main.py
```

Visit `http://localhost:8000` to see the API welcome message.

Visit `http://localhost:8000/docs` to see interactive API documentation.

## Step 7: Test Modal Deployment

```bash
# Deploy to Modal
modal deploy main.py

# This will:
# 1. Build container image
# 2. Deploy to Modal's infrastructure
# 3. Provide a public URL
```

After successful deployment, Modal will provide a URL like:

```
https://your-username--pdf-extraction-playground-fastapi-app.modal.run
```

## Step 8: Verify Deployment

Test the deployed API:

```bash
# Health check
curl https://your-modal-url.modal.run/health

# List models
curl https://your-modal-url.modal.run/models
```

Or visit the URL in your browser to see the welcome message.

## Step 9: Test File Upload

Create a test script or use curl:

```bash
# Test upload endpoint (create a sample PDF first)
curl -X POST "https://your-modal-url.modal.run/upload" \
  -F "file=@sample.pdf" \
  -F "model=docling"
```

## Project Structure

```
pdf-extraction-playground/
├── backend/
│   ├── main.py              # FastAPI + Modal app
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Environment variables (local)
│   ├── .gitignore          # Git ignore file
│   └── README.md           # Project documentation
└── frontend/               # Next.js app (to be created)
```

## Troubleshooting

### Modal Authentication Issues

```bash
# Re-authenticate if needed
modal token set --token-id YOUR_TOKEN_ID --token-secret YOUR_TOKEN_SECRET
```

### Port Already in Use (Local Development)

```bash
# Change port in main.py or kill the process:
# On macOS/Linux:
lsof -ti:8000 | xargs kill -9
# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Import Errors

```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

## Next Steps

Once the basic setup is working:

1. ✅ Test all endpoints locally
2. ✅ Verify Modal deployment
3. ⬜ Integrate first extraction model (Docling recommended)
4. ⬜ Add PDF processing logic
5. ⬜ Implement bounding box generation
6. ⬜ Setup frontend with Next.js

## Useful Commands

```bash
# Local development
python main.py

# Deploy to Modal
modal deploy main.py

# Run Modal app locally (for testing)
modal serve main.py

# View Modal logs
modal app logs pdf-extraction-playground

# Stop Modal deployment
modal app stop pdf-extraction-playground
```

## Testing the API

Once deployed, you can test endpoints:

### 1. Health Check

```bash
curl https://your-modal-url.modal.run/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "pdf-extraction-api",
  "timestamp": "2025-09-30T...",
  "models_available": ["docling", "surya", "mineru"]
}
```

### 2. List Models

```bash
curl https://your-modal-url.modal.run/models
```

### 3. Upload PDF

```bash
curl -X POST https://your-modal-url.modal.run/upload \
  -F "file=@test.pdf" \
  -F "model=docling"
```

## Resources

- **Modal Documentation**: https://modal.com/docs
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **Modal Python SDK**: https://github.com/modal-labs/modal-client

## Support

If you encounter issues:

1. Check Modal logs: `modal app logs pdf-extraction-playground`
2. Review FastAPI docs at `/docs` endpoint
3. Check Modal status page: https://status.modal.com
