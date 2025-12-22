# DCS Parts Matching Agent

**AI-Powered Intelligent Parts Quotation System for Industrial Automation**

A production-ready AI agent system that automatically matches customer-submitted technical drawings and descriptions to the correct DCS (Distributed Control System) part numbers from your Smart Click PDF catalog. Built for the industrial automation sector to reduce quotation response time, improve accuracy, and minimize human error.

---

## 🚀 Features

### Multi-Modal Document Processing
- **PDF Analysis**: Extract specifications from datasheets and technical documents
- **Image Recognition**: Analyze technical drawings, schematics, and part photographs using GPT-4 Vision or Claude 3
- **Text Processing**: Understand natural language part descriptions and requirements
- **CAD Support**: Handle DWG and DXF files (with conversion to images)

### Intelligent Matching Engine
- **Specification Matching**: Match critical specs (voltage, current, pressure ratings, I/O counts)
- **Dimensional Analysis**: Compare physical dimensions with configurable tolerance
- **Semantic Search**: Vector-based similarity search across entire catalog
- **Confidence Scoring**: 0-100% confidence scores with transparent justification

### Production-Ready Architecture
- **FastAPI REST API**: High-performance async API with automatic OpenAPI documentation
- **Vector Database**: ChromaDB integration for efficient similarity search
- **Scalable Design**: Handles concurrent requests with configurable workers
- **Comprehensive Logging**: Structured logging with rotation and request tracking
- **Error Handling**: Graceful handling of corrupted files and ambiguous inputs

### Smart Catalog Management
- **Auto-Indexing**: Automatically index Smart Click PDF catalogs on startup
- **Multiple Formats**: Support for PDF, JSON, and CSV catalog sources
- **Live Updates**: Add/update parts without system restart
- **Statistics Dashboard**: Monitor catalog size and system health

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Architecture](#-architecture)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

## 🏃 Quick Start

### Prerequisites

- Python 3.10 or higher
- OpenAI API key (for GPT-4 Vision) OR Anthropic API key (for Claude 3)
- Tesseract OCR (optional, for enhanced text extraction)

### 5-Minute Setup

```bash
# 1. Clone the repository
cd dcs-parts-matching-agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your API keys

# 5. Prepare your catalog
mkdir -p data/catalog
# Place your Smart Click PDF catalog or JSON files in data/catalog/

# 6. Start the server
python -m src.api.main
```

Your API will be running at `http://localhost:8000`

Interactive API docs: `http://localhost:8000/api/docs`

---

## 📦 Installation

### System Requirements

- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: 2GB for application + catalog size
- **CPU**: Multi-core recommended for concurrent requests
- **OS**: Linux, macOS, or Windows

### Install Tesseract (Optional but Recommended)

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

### Python Dependencies

```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- `fastapi` - Web framework
- `openai` - GPT-4 Vision integration
- `anthropic` - Claude 3 integration
- `chromadb` - Vector database
- `pdfplumber` - PDF processing
- `Pillow` - Image processing
- `loguru` - Structured logging

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

#### Required Settings

```env
# At least one AI provider is required
OPENAI_API_KEY=sk-your-openai-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

#### Model Selection

```env
# For vision analysis (technical drawings)
USE_VISION_MODEL=gpt-4-vision-preview
# Alternatives: claude-3-opus-20240229, claude-3-sonnet-20240229

# For text embeddings (similarity search)
USE_EMBEDDING_MODEL=text-embedding-3-large
```

#### API Server

```env
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
DEBUG=false
```

#### Matching Engine Tuning

```env
# Dimensional tolerance for matching (%)
DIMENSIONAL_TOLERANCE_PERCENT=5.0

# Weight multiplier for critical specifications
CRITICAL_SPECS_WEIGHT=2.0
```

See `.env.example` for all available options.

---

## 🎯 Usage

### 1. Index Your Catalog

Before matching parts, index your Smart Click PDF catalog:

**Option A: Auto-Index on Startup** (Recommended)
```env
AUTO_INDEX_ON_STARTUP=true
```

**Option B: Manual Index via API**
```bash
curl -X POST http://localhost:8000/api/catalog/index
```

**Option C: Place Files in Catalog Directory**
```
data/catalog/
├── smart_click_catalog_2024.pdf
├── additional_parts.json
└── legacy_parts.csv
```

### 2. Submit Requests

#### Via API (Recommended)

**Upload Technical Drawing:**
```bash
curl -X POST "http://localhost:8000/api/match" \
  -F "file=@technical_drawing.pdf" \
  -F "max_alternatives=3" \
  -F "min_confidence=50.0"
```

**Text Description:**
```bash
curl -X POST "http://localhost:8000/api/match" \
  -F "text_description=Need 24V DC digital input module with 16 channels" \
  -F "additional_context=For Siemens PLC compatibility" \
  -F "max_alternatives=3"
```

**Python Example:**
```python
import requests

# Match from file
with open("technical_drawing.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/match",
        files={"file": f},
        data={
            "max_alternatives": 3,
            "min_confidence": 50.0
        }
    )

result = response.json()
print(f"Primary match: {result['primary_match']['part']['part_number']}")
print(f"Confidence: {result['primary_match']['confidence_score']:.1f}%")
print(f"Justification: {result['primary_match']['justification']}")
```

#### Via Python SDK

```python
from src.agents.parts_agent import PartsMatchingAgent
from src.core.models import DocumentSubmission, ProcessingRequest, DocumentType

# Initialize agent
agent = PartsMatchingAgent()
await agent.initialize()

# Create submission
submission = DocumentSubmission(
    file_path="technical_drawing.pdf",
    document_type=DocumentType.PDF,
    text_description="24V digital input module"
)

# Create request
request = ProcessingRequest(
    submission=submission,
    max_alternatives=3,
    min_confidence_threshold=50.0
)

# Process
result = await agent.process_request(request)

# Check result
if result.primary_match:
    print(f"Match found: {result.primary_match.part.part_number}")
    print(f"Confidence: {result.primary_match.confidence_score:.1f}%")

    # Check if human review needed
    if result.requires_human_review:
        print(f"⚠️ Review required: {result.review_reason}")
else:
    print("No suitable match found")
```

### 3. Response Format

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-15T10:30:00Z",
  "extracted_features": {
    "specifications": [
      {
        "spec_type": "voltage_rating",
        "name": "Voltage Rating",
        "value": "24",
        "unit": "V",
        "is_critical": true,
        "confidence": 0.95
      }
    ],
    "dimensions": {
      "width": 100.0,
      "height": 150.0,
      "unit": "mm"
    },
    "text_description": "24V DC digital input module"
  },
  "primary_match": {
    "part": {
      "part_number": "DCS-1234-ABC",
      "description": "24V DC Digital Input Module, 16 channels",
      "category": "Digital Input",
      "specifications": [...]
    },
    "confidence_score": 92.5,
    "confidence_level": "high",
    "matched_specifications": [
      {
        "spec_name": "Voltage Rating",
        "customer_value": "24 V",
        "part_value": "24 V",
        "is_match": true,
        "match_score": 1.0,
        "notes": "Exact match"
      }
    ],
    "missing_specifications": [],
    "justification": "Matched DCS-1234-ABC - 24V DC Digital Input Module. 3 exact specification matches. Strong match based on high specification match, high dimensional match.",
    "warnings": []
  },
  "alternative_matches": [...],
  "processing_time_seconds": 2.45,
  "requires_human_review": false,
  "review_reason": null
}
```

---

## 📚 API Documentation

### Interactive Documentation

Once the server is running:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/match` | POST | Match parts from file or text |
| `/api/catalog/index` | POST | Reindex catalog |
| `/api/catalog/stats` | GET | Get catalog statistics |
| `/api/catalog/parts` | POST | Add new part to catalog |
| `/api/catalog/parts/{part_number}` | GET | Get specific part |
| `/health` | GET | System health check |
| `/api/version` | GET | Get API version |

### Authentication (Optional)

To add authentication, implement a middleware in `src/api/main.py`:

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/api/match")
async def match_parts(
    token: str = Depends(security),
    # ... other parameters
):
    # Validate token
    if not validate_token(token):
        raise HTTPException(status_code=401)
    # ... rest of logic
```

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
│            (Web UI, Mobile App, ERP Integration)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI REST API                          │
│              (Authentication, Rate Limiting)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Parts Matching Agent                         │
│                  (Orchestration Layer)                       │
└────────┬──────────────┬──────────────┬──────────────────────┘
         │              │              │
    ┌────▼────┐    ┌───▼────┐    ┌────▼─────┐
    │ Vision  │    │  PDF   │    │   Text   │
    │Processor│    │Processor│    │Processor │
    └────┬────┘    └───┬────┘    └────┬─────┘
         │              │              │
         └──────────────┴──────────────┘
                       │
                       ▼
         ┌──────────────────────────┐
         │   Feature Extraction     │
         │  (Specs, Dimensions)     │
         └────────────┬─────────────┘
                      │
                      ▼
         ┌──────────────────────────┐
         │   Matching Engine        │
         │  (Scoring & Ranking)     │
         └────────────┬─────────────┘
                      │
              ┌───────┴────────┐
              ▼                ▼
    ┌──────────────┐  ┌──────────────┐
    │ Vector Store │  │ AI Models    │
    │  (ChromaDB)  │  │ (GPT-4/Claude)│
    └──────────────┘  └──────────────┘
```

### Key Components

1. **Document Processors** (`src/processors/`)
   - Vision Processor: AI vision analysis of drawings
   - PDF Processor: Text and image extraction from PDFs
   - Text Processor: NLP analysis of descriptions

2. **Matching Engine** (`src/agents/matching_engine.py`)
   - Multi-factor scoring algorithm
   - Specification comparison with tolerance
   - Confidence calculation

3. **Vector Store** (`src/database/vector_store.py`)
   - ChromaDB integration
   - Embedding generation
   - Similarity search

4. **Catalog Manager** (`src/agents/catalog_manager.py`)
   - PDF catalog parsing
   - JSON/CSV import
   - Index management

### Data Flow

1. **Ingestion**: Customer submits document/text via API
2. **Processing**: Appropriate processor extracts features
3. **Matching**: Matching engine scores catalog parts
4. **Ranking**: Parts ranked by confidence score
5. **Response**: Top matches returned with justification

---

## 🧪 Testing

### Run All Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests with coverage
pytest tests/ -v --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run Specific Tests

```bash
# Test matching engine
pytest tests/test_matching_engine.py -v

# Test API endpoints
pytest tests/test_api.py -v
```

### Manual Testing

```bash
# Check API health
curl http://localhost:8000/health

# Get catalog stats
curl http://localhost:8000/api/catalog/stats

# Test with sample data
curl -X POST "http://localhost:8000/api/match" \
  -F "text_description=24V DC input module 16 channels"
```

---

## 🚀 Deployment

### Docker Deployment (Recommended)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data/catalog data/uploads data/vector_db logs

EXPOSE 8000

CMD ["python", "-m", "src.api.main"]
```

Build and run:
```bash
docker build -t dcs-parts-agent .
docker run -p 8000:8000 --env-file .env dcs-parts-agent
```

### Cloud Deployment

**AWS (Elastic Beanstalk)**
```bash
eb init -p python-3.11 dcs-parts-agent
eb create production-env
eb deploy
```

**Google Cloud (Cloud Run)**
```bash
gcloud run deploy dcs-parts-agent \
  --source . \
  --platform managed \
  --region us-central1
```

**Azure (Container Instances)**
```bash
az container create \
  --resource-group myResourceGroup \
  --name dcs-parts-agent \
  --image dcs-parts-agent \
  --dns-name-label dcs-parts-agent
```

### Production Checklist

- [ ] Set `DEBUG=false` in environment
- [ ] Configure HTTPS/SSL
- [ ] Set up authentication/API keys
- [ ] Enable rate limiting
- [ ] Configure log aggregation (e.g., ELK stack)
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure automated backups of vector database
- [ ] Set up health check monitoring
- [ ] Review and adjust worker count for load

---

## 🔧 Troubleshooting

### Common Issues

**Issue: "Agent not initialized" error**
```
Solution: Ensure API keys are set correctly in .env file
Check: OPENAI_API_KEY or ANTHROPIC_API_KEY is set
```

**Issue: Low confidence scores**
```
Solution:
1. Ensure catalog is properly indexed
2. Add more detailed specifications to catalog
3. Adjust DIMENSIONAL_TOLERANCE_PERCENT
4. Lower min_confidence threshold for testing
```

**Issue: Vision processing fails**
```
Solution:
1. Verify API key has GPT-4 Vision or Claude 3 access
2. Check image file is not corrupted
3. Ensure image is under size limit
4. Try alternative vision model
```

**Issue: PDF text extraction incomplete**
```
Solution:
1. Install Tesseract OCR
2. Set TESSERACT_PATH if not in system PATH
3. For image-based PDFs, enable vision processing
```

### Enable Debug Logging

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

Check logs:
```bash
tail -f logs/app.log
```

### Performance Optimization

**Slow matching:**
- Increase `API_WORKERS`
- Use faster embedding model
- Reduce `top_k` in vector search
- Enable caching

**High memory usage:**
- Reduce concurrent requests
- Use smaller embedding model
- Limit catalog size per index

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest tests/ -v`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Standards

- Follow PEP 8 style guide
- Add docstrings to all functions/classes
- Include type hints
- Write unit tests for new features
- Update documentation

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 📞 Support

For technical support or questions:
- Open an issue on GitHub
- Email: support@yourcompany.com
- Documentation: See `docs/` directory

---

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [OpenAI GPT-4](https://openai.com/) and [Anthropic Claude](https://anthropic.com/)
- Vector search by [ChromaDB](https://www.trychroma.com/)

---

**Version**: 1.0.0
**Last Updated**: 2024-01-15
