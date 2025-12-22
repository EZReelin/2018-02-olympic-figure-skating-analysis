# Quick Start Guide - DCS Parts Matching Agent

Get up and running in 10 minutes!

## Prerequisites

- Python 3.10+ installed
- OpenAI API key OR Anthropic API key
- Internet connection

## Step-by-Step Setup

### 1. Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env and add your API key
# You need EITHER OpenAI OR Anthropic (or both)
nano .env  # or use your favorite editor
```

**Minimum configuration in `.env`:**
```env
OPENAI_API_KEY=sk-your-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Prepare Sample Catalog (Optional)

Create a sample catalog to test with:

```bash
python examples/catalog_management.py
```

This creates a sample catalog in `data/catalog/sample_catalog.json` with 5 example parts.

### 4. Start the Server

```bash
python -m src.api.main
```

You should see:
```
INFO: Started server process
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 5. Test the API

Open another terminal and try these commands:

**Check Health:**
```bash
curl http://localhost:8000/health
```

**Match a Part (Text Description):**
```bash
curl -X POST "http://localhost:8000/api/match" \
  -F "text_description=Need a 24V digital input module with 16 channels"
```

**View API Documentation:**

Open your browser to: http://localhost:8000/api/docs

## Quick Examples

### Python Example

```python
import requests

# Match from text
response = requests.post(
    "http://localhost:8000/api/match",
    data={
        "text_description": "24V DC input module 16 channels",
        "max_alternatives": 3
    }
)

result = response.json()
if result["primary_match"]:
    print(f"Found: {result['primary_match']['part']['part_number']}")
    print(f"Confidence: {result['primary_match']['confidence_score']:.1f}%")
```

### Upload File Example

```bash
curl -X POST "http://localhost:8000/api/match" \
  -F "file=@technical_drawing.pdf" \
  -F "max_alternatives=3"
```

## Run Examples

Try the provided example scripts:

```bash
# Simple text matching
python examples/simple_text_match.py

# API client usage
python examples/api_client_example.py

# Catalog management
python examples/catalog_management.py

# Batch processing
python examples/batch_processing.py
```

## Docker Quick Start

If you prefer Docker:

```bash
# Build image
docker-compose build

# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

## Troubleshooting

**Problem: "Agent not initialized"**
- Check that your API keys are set correctly in `.env`
- Verify the API key has access to vision models

**Problem: "No parts found"**
- Run `python examples/catalog_management.py` to create sample catalog
- Or place your catalog files in `data/catalog/`
- Restart the server to trigger auto-indexing

**Problem: Server won't start**
- Check if port 8000 is already in use
- Try a different port: `API_PORT=8001` in `.env`

**Problem: Low confidence scores**
- Ensure your catalog has detailed specifications
- Try lowering `min_confidence` threshold
- Add more parts to the catalog

## Next Steps

1. **Add Your Catalog**
   - Place your Smart Click PDF in `data/catalog/`
   - Restart server (auto-index will run)

2. **Customize Configuration**
   - Edit `.env` for your needs
   - Adjust matching tolerances
   - Configure OCR settings

3. **Integrate with Your System**
   - Use the REST API from your applications
   - Check out `examples/api_client_example.py`

4. **Production Deployment**
   - See README.md for deployment options
   - Set up HTTPS/SSL
   - Configure authentication

## Support

- 📖 Full Documentation: See `README.md`
- 🔧 Examples: Check `examples/` directory
- 🐛 Issues: Report on GitHub
- 📧 Email: support@yourcompany.com

---

**You're ready to go!** 🚀

Try matching your first part:
```bash
curl -X POST "http://localhost:8000/api/match" \
  -F "text_description=Your part description here"
```
