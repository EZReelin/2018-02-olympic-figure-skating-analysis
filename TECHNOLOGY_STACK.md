# Technology Stack - Detailed Justifications

## Overview

This document provides detailed rationale for each technology choice in the Manufacturing AI System.

---

## Backend Stack

### 1. FastAPI (Python 3.11+)

**Chosen**: ✅ FastAPI

**Why**:
- **Performance**: Built on Starlette and Pydantic, one of the fastest Python frameworks
- **Async Support**: Native async/await for handling concurrent requests efficiently
- **Auto Documentation**: Automatic OpenAPI/Swagger docs (critical for API-first design)
- **Type Safety**: Pydantic models prevent runtime errors, improve IDE support
- **Modern**: Active development, growing ecosystem
- **Validation**: Built-in request/response validation
- **Easy Testing**: Excellent test client

**Alternatives Considered**:

| Framework | Pros | Cons | Decision |
|-----------|------|------|----------|
| **Django + DRF** | Mature, batteries included, admin panel | Slower, more opinionated, heavier | ❌ Too heavyweight |
| **Flask** | Lightweight, flexible | Requires many plugins, no async (without extensions) | ❌ Missing features |
| **Node.js (Express)** | Fast, huge ecosystem | Not ideal for AI/ML, weak typing | ❌ Python better for AI |

**Implementation Notes**:
```python
# Example structure
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Manufacturing AI Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Multi-tenant middleware
@app.middleware("http")
async def add_tenant_context(request: Request, call_next):
    # Extract tenant from subdomain or API key
    tenant_id = await get_tenant_from_request(request)
    request.state.tenant_id = tenant_id
    response = await call_next(request)
    return response
```

---

### 2. PostgreSQL 15+

**Chosen**: ✅ PostgreSQL

**Why**:
- **Row-Level Security (RLS)**: Built-in multi-tenancy support
- **JSONB**: Flexible schema for varying client configurations
- **Full-Text Search**: Built-in powerful search (better than MySQL)
- **Performance**: Excellent query optimizer, indexing options
- **Reliability**: ACID compliant, proven at scale
- **Extensions**: PostGIS (if geo data), pgvector (for embeddings if needed)
- **Ecosystem**: Great tools (pgAdmin, pg_dump, etc.)

**Alternatives Considered**:

| Database | Pros | Cons | Decision |
|----------|------|------|----------|
| **MySQL** | Popular, fast reads | Weaker full-text search, no RLS | ❌ Less suitable |
| **MongoDB** | Schema flexibility | Harder multi-tenancy, consistency issues | ❌ ACID not guaranteed |
| **CockroachDB** | Distributed, PostgreSQL compatible | Expensive, overkill for our scale | ❌ Premature |

**Multi-Tenancy Implementation**:
```sql
-- Row-Level Security Example
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON quotes
    USING (tenant_id = current_setting('app.tenant_id')::uuid);

-- In application, set context per request
SET LOCAL app.tenant_id = '123e4567-e89b-12d3-a456-426614174000';
```

---

### 3. Vector Database: Qdrant

**Chosen**: ✅ Qdrant (with Weaviate as alternative)

**Why**:
- **Multi-Tenancy**: Native support via collections and payloads
- **Performance**: Written in Rust, very fast
- **Filtering**: Advanced filtering on metadata while searching
- **Scalability**: Horizontal scaling, clustering support
- **API**: Clean REST and gRPC APIs
- **Cloud Option**: Managed cloud available (Qdrant Cloud)
- **Open Source**: Self-hostable, no vendor lock-in

**Alternatives Considered**:

| Vector DB | Pros | Cons | Decision |
|-----------|------|------|----------|
| **ChromaDB** | Simple, Python-native | Less mature for production, weaker multi-tenancy | ❌ Prototype only |
| **Pinecone** | Fully managed, easy | Expensive, vendor lock-in, no self-host | ❌ Cost concerns |
| **Weaviate** | Great features, GraphQL | Steeper learning curve | ✅ Strong alternative |
| **Milvus** | Very fast, scalable | Complex setup, heavy | ❌ Overkill initially |

**Implementation**:
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Initialize
client = QdrantClient(url="http://localhost:6333")

# Create tenant-specific collection
client.create_collection(
    collection_name=f"tenant_{tenant_id}_parts_catalog",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

# Search with tenant isolation
results = client.search(
    collection_name=f"tenant_{tenant_id}_parts_catalog",
    query_vector=embedding,
    limit=10,
    query_filter={"category": "digital_io"}
)
```

---

### 4. Object Storage: MinIO (self-hosted) or AWS S3

**Chosen**: ✅ MinIO for development, AWS S3 for production

**Why**:
- **S3 Compatibility**: MinIO provides S3-compatible API
- **Tenant Isolation**: Separate buckets per tenant
- **Cost**: MinIO free for self-host, S3 affordable with Intelligent-Tiering
- **Durability**: 99.999999999% durability (S3)
- **Integration**: Excellent SDK support (boto3)
- **Scalability**: Virtually unlimited

**Bucket Strategy**:
```
tenant-{tenant_id}-documents/
├── parts-catalogs/
│   ├── catalog_v1.pdf
│   └── catalog_v2.pdf
├── quotes/
│   ├── 2024/
│   │   ├── Q-001.pdf
│   │   └── Q-002.pdf
├── interviews/
│   ├── audio/
│   └── transcripts/
├── sops/
│   └── exports/
└── erp-docs/
    ├── manuals/
    └── screenshots/
```

**Implementation**:
```python
import boto3

s3_client = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',  # MinIO for dev
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin'
)

# Generate pre-signed upload URL
url = s3_client.generate_presigned_url(
    'put_object',
    Params={
        'Bucket': f'tenant-{tenant_id}-documents',
        'Key': f'parts-catalogs/{filename}'
    },
    ExpiresIn=3600
)
```

---

### 5. Redis 7+

**Chosen**: ✅ Redis

**Why**:
- **Caching**: Fast in-memory cache for frequently accessed data
- **Sessions**: Store user sessions
- **Rate Limiting**: Token bucket algorithm
- **Job Queues**: Celery backend
- **Pub/Sub**: Real-time notifications
- **Performance**: Sub-millisecond latency

**Use Cases**:
```python
import redis
from datetime import timedelta

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Cache parts catalog metadata
redis_client.setex(
    f"tenant:{tenant_id}:catalog:stats",
    timedelta(hours=1),
    json.dumps(catalog_stats)
)

# Rate limiting (100 requests per minute per tenant)
key = f"rate_limit:{tenant_id}:{minute}"
current = redis_client.incr(key)
if current == 1:
    redis_client.expire(key, 60)
if current > 100:
    raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

---

### 6. Celery (Background Jobs)

**Chosen**: ✅ Celery + RabbitMQ

**Why**:
- **Mature**: Battle-tested for 10+ years
- **Flexible**: Multiple broker options (RabbitMQ, Redis, SQS)
- **Monitoring**: Flower dashboard
- **Scheduling**: Cron-like periodic tasks
- **Retries**: Automatic retry with exponential backoff
- **Priority Queues**: Different queues for different job types

**Use Cases**:
- Long-running AI tasks (SOP generation)
- Batch processing (catalog indexing)
- Scheduled jobs (usage metrics aggregation)
- Email sending
- Report generation

**Implementation**:
```python
from celery import Celery

celery_app = Celery(
    'manufacturing_ai',
    broker='amqp://guest:guest@localhost:5672//',
    backend='redis://localhost:6379/0'
)

@celery_app.task(bind=True, max_retries=3)
def generate_sop_from_interview(self, tenant_id, interview_id):
    try:
        # Long-running AI task
        sop = await ai_service.generate_sop(interview_id)
        return sop.id
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

---

## AI/ML Stack

### 7. Anthropic Claude API

**Chosen**: ✅ Claude 3 Sonnet/Opus

**Why**:
- **Context Window**: 200K tokens (critical for long documents)
- **Document Understanding**: Excellent at extracting structured data
- **Reasoning**: Strong logical reasoning for matching parts
- **Tool Use**: Function calling for structured output
- **Safety**: Built-in safety features
- **Pricing**: Competitive (especially with caching)
- **Quality**: Best for our use cases based on testing

**Use Cases by Model**:

| Model | Use Case | Why |
|-------|----------|-----|
| **Claude 3.5 Sonnet** | Parts matching, quote generation, ERP queries | Best balance of speed/cost/quality |
| **Claude 3 Opus** | Complex SOP generation, multi-page analysis | Highest quality for critical tasks |
| **Claude 3 Haiku** | Simple queries, classification | Fastest, cheapest for simple tasks |

**Cost Optimization**:
- Prompt caching for repeated contexts (catalog data)
- Batch similar requests
- Use cheaper models when appropriate
- Streaming responses for better UX

**Implementation**:
```python
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Parts matching with prompt caching
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=2000,
    system=[
        {
            "type": "text",
            "text": "You are a parts matching expert...",
            "cache_control": {"type": "ephemeral"}
        },
        {
            "type": "text",
            "text": f"Parts Catalog:\n{catalog_json}",  # Cached!
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[
        {"role": "user", "content": f"Match this part: {part_description}"}
    ]
)
```

**Fallback Strategy**:
```python
# OpenAI as fallback
async def call_ai_with_fallback(prompt, model="claude"):
    try:
        if model == "claude":
            return await call_claude(prompt)
        elif model == "openai":
            return await call_openai(prompt)
    except AnthropicError:
        logger.warning("Claude API failed, falling back to OpenAI")
        return await call_openai(prompt)
```

---

## Frontend Stack

### 8. Next.js 14 (React)

**Chosen**: ✅ Next.js 14 with App Router

**Why**:
- **SSR**: Server-side rendering for better SEO, faster initial load
- **React**: Large talent pool, component ecosystem
- **TypeScript**: Type safety across frontend
- **API Routes**: Backend-for-frontend pattern
- **File-based Routing**: Intuitive structure
- **Image Optimization**: Built-in image optimization
- **Deployment**: Easy Vercel deployment (or Docker)

**Project Structure**:
```
frontend/
├── app/
│   ├── (admin)/              # Admin portal
│   │   ├── dashboard/
│   │   ├── tenants/
│   │   └── billing/
│   ├── (client)/             # Client portal
│   │   ├── quotes/
│   │   ├── sops/
│   │   └── erp-copilot/
│   └── api/                  # Backend-for-frontend
├── components/
│   ├── ui/                   # shadcn/ui components
│   ├── quotes/
│   ├── sops/
│   └── shared/
├── lib/
│   ├── api-client.ts
│   ├── auth.ts
│   └── utils.ts
└── public/
```

**Alternatives Considered**:
- Vue.js: Great, but smaller ecosystem for enterprise components
- Svelte: Excellent performance, but smaller talent pool
- Angular: Too heavyweight, steeper learning curve

---

### 9. UI Library: shadcn/ui + Tailwind CSS

**Chosen**: ✅ shadcn/ui with Tailwind CSS

**Why**:
- **Copy-Paste**: Components owned by you, not npm dependency
- **Customizable**: Full control over styling
- **Accessible**: Built on Radix UI (WCAG compliant)
- **Modern**: Beautiful, professional designs
- **Tailwind**: Utility-first CSS, fast development
- **No Runtime**: CSS at build time, smaller bundle

**Example Component**:
```tsx
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

export function QuoteCard({ quote }) {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold">{quote.quote_number}</h3>
      <p className="text-muted-foreground">{quote.customer_name}</p>
      <div className="mt-4 flex justify-between">
        <span className="text-2xl font-bold">
          ${quote.total_amount.toFixed(2)}
        </span>
        <Button>View Details</Button>
      </div>
    </Card>
  )
}
```

**Alternatives Considered**:
- Material-UI: Heavy, opinionated design
- Ant Design: Great for admin panels, but less customizable
- Chakra UI: Good, but runtime styling performance concerns

---

### 10. State Management: Zustand

**Chosen**: ✅ Zustand

**Why**:
- **Simple**: Minimal boilerplate vs Redux
- **TypeScript**: Excellent type inference
- **Lightweight**: ~1KB
- **DevTools**: Redux DevTools compatible
- **No Provider Wrapping**: Less boilerplate
- **Middleware**: Persist, logging, etc.

**Example**:
```typescript
import create from 'zustand'

interface TenantStore {
  currentTenant: Tenant | null
  setTenant: (tenant: Tenant) => void
  quotes: Quote[]
  fetchQuotes: () => Promise<void>
}

export const useTenantStore = create<TenantStore>((set, get) => ({
  currentTenant: null,
  setTenant: (tenant) => set({ currentTenant: tenant }),

  quotes: [],
  fetchQuotes: async () => {
    const tenant = get().currentTenant
    if (!tenant) return

    const quotes = await apiClient.getQuotes(tenant.id)
    set({ quotes })
  }
}))

// Usage in component
function QuotesList() {
  const { quotes, fetchQuotes } = useTenantStore()

  useEffect(() => {
    fetchQuotes()
  }, [])

  return <div>{quotes.map(q => <QuoteCard quote={q} />)}</div>
}
```

---

## DevOps & Infrastructure

### 11. Docker + Docker Compose

**Chosen**: ✅ Docker for everything

**Why**:
- **Consistency**: Same environment dev to prod
- **Isolation**: Services don't conflict
- **Easy Onboarding**: New developers up and running quickly
- **Scalability**: Easy to move to Kubernetes later
- **Ecosystem**: Huge library of images

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/manufacturing_ai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
      - qdrant

  postgres:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=yourpassword

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

  celery_worker:
    build: ./backend
    command: celery -A app.tasks worker --loglevel=info
    depends_on:
      - redis
      - rabbitmq

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  minio_data:
```

---

### 12. Authentication: Supabase Auth

**Chosen**: ✅ Supabase Auth

**Why**:
- **Multi-Tenant**: Built-in organization support
- **PostgreSQL-Based**: Fits our stack
- **MFA**: Email, SMS, authenticator apps
- **SSO**: SAML for enterprise clients
- **Social Auth**: Google, Microsoft, etc.
- **Open Source**: Can self-host if needed
- **Row-Level Security**: Integrates with our PostgreSQL RLS

**Alternative**: Auth0
- Pros: More mature, better enterprise features
- Cons: More expensive, not PostgreSQL-based

**Implementation**:
```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
)

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@company.com',
  password: 'password'
})

// Get user with tenant
const { data: { user } } = await supabase.auth.getUser()
const tenant_id = user.user_metadata.tenant_id

// Middleware to inject tenant
export async function middleware(req: NextRequest) {
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return NextResponse.redirect('/login')
  }

  // Add tenant to request
  const requestHeaders = new Headers(req.headers)
  requestHeaders.set('X-Tenant-ID', user.user_metadata.tenant_id)

  return NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  })
}
```

---

### 13. Monitoring: Prometheus + Grafana

**Chosen**: ✅ Prometheus for metrics, Grafana for dashboards

**Why**:
- **Standard**: Industry standard for monitoring
- **Pull-Based**: Scrapes metrics from services
- **Powerful**: PromQL query language
- **Alerting**: AlertManager for notifications
- **Grafana**: Beautiful dashboards
- **Free**: Open source

**Metrics to Track**:
```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter(
    'api_requests_total',
    'Total API requests',
    ['tenant_id', 'endpoint', 'status']
)

request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['tenant_id', 'endpoint']
)

# Business metrics
quotes_generated = Counter(
    'quotes_generated_total',
    'Total quotes generated',
    ['tenant_id']
)

ai_api_calls = Counter(
    'ai_api_calls_total',
    'AI API calls',
    ['tenant_id', 'model', 'service']
)

# System metrics
active_tenants = Gauge(
    'active_tenants',
    'Number of active tenants'
)
```

---

### 14. Logging: Structured Logging with Loguru

**Chosen**: ✅ Loguru for application logs, ELK Stack for aggregation

**Why**:
- **Structured**: JSON logs for easy parsing
- **Context**: Automatic context (tenant, user, request_id)
- **Rotation**: Automatic log rotation
- **Sinks**: Multiple outputs (file, stdout, cloud)
- **Performance**: Async logging

**Implementation**:
```python
from loguru import logger
import sys

# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[tenant_id]}</cyan> | <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[tenant_id]} | {message}",
    serialize=True  # JSON format
)

# Use in application
@app.middleware("http")
async def add_logging_context(request: Request, call_next):
    tenant_id = request.state.tenant_id
    request_id = str(uuid.uuid4())

    with logger.contextualize(tenant_id=tenant_id, request_id=request_id):
        logger.info(f"{request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
```

---

## Summary Comparison

### Cost Breakdown (Monthly, 50 Clients)

| Component | Option | Monthly Cost |
|-----------|--------|--------------|
| Compute | 3x EC2 t3.medium | $75 |
| Database | RDS PostgreSQL db.t3.medium | $60 |
| Vector DB | Qdrant self-hosted | $30 (in compute) |
| Object Storage | S3 (500GB) | $12 |
| Redis | ElastiCache t3.micro | $15 |
| Load Balancer | ALB | $20 |
| Domain & SSL | CloudFlare | Free |
| Monitoring | Grafana Cloud free tier | Free |
| **Total Infrastructure** | | **~$180/month** |
| | | |
| AI API Calls | Anthropic Claude | $300-500/month |
| Auth Service | Supabase | $25/month |
| **Total Operational** | | **~$505-705/month** |

**Revenue (50 clients)**: ~$37,500-50,000/month
**Gross Margin**: ~98-99%

---

## Migration Path

### Start Simple, Scale Smart

**Phase 1 (1-10 clients)**: Single VPS
- Docker Compose on DigitalOcean droplet
- ~$50/month

**Phase 2 (10-50 clients)**: Managed services
- AWS/GCP with managed DB, Redis
- ~$180/month

**Phase 3 (50-200 clients)**: Kubernetes
- EKS/GKE cluster
- Auto-scaling
- ~$500-1000/month

**Phase 4 (200+ clients)**: Multi-region
- Global deployment
- CDN
- ~$2000+/month

---

**Document Version**: 1.0
**Last Updated**: 2026-01-05
