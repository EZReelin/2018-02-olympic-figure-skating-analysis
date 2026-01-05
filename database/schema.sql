-- Manufacturing AI System - Database Schema
-- PostgreSQL 15+
-- Multi-Tenant Architecture with Row-Level Security

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- CORE TENANT MANAGEMENT
-- ============================================================================

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    industry VARCHAR(100),
    company_size VARCHAR(50), -- small, medium, large, enterprise
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'trial', 'suspended', 'churned')),
    subscription_tier VARCHAR(50) DEFAULT 'starter', -- starter, professional, enterprise

    -- Contact information
    primary_contact_name VARCHAR(255),
    primary_contact_email VARCHAR(255),
    primary_contact_phone VARCHAR(50),

    -- Billing
    billing_email VARCHAR(255),
    billing_address JSONB,
    payment_method VARCHAR(50), -- credit_card, invoice, ach

    -- Configuration
    settings JSONB DEFAULT '{}', -- Tenant-specific settings
    branding JSONB DEFAULT '{}', -- Logo URLs, colors, etc.

    -- Limits
    max_users INT DEFAULT 10,
    max_storage_gb INT DEFAULT 100,

    -- Lifecycle
    trial_ends_at TIMESTAMP,
    onboarding_completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP -- Soft delete
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_created_at ON tenants(created_at);

-- ============================================================================
-- SERVICE SUBSCRIPTIONS
-- ============================================================================

CREATE TABLE tenant_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Service details
    service_type VARCHAR(50) NOT NULL CHECK (
        service_type IN ('quote_intelligence', 'knowledge_preservation', 'erp_copilot')
    ),
    status VARCHAR(50) DEFAULT 'active' CHECK (
        status IN ('active', 'paused', 'cancelled', 'past_due')
    ),

    -- Pricing
    pricing_plan VARCHAR(50), -- monthly, annual
    setup_fee DECIMAL(10, 2) DEFAULT 0.00,
    monthly_fee DECIMAL(10, 2) NOT NULL,
    annual_fee DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',

    -- Limits for this service
    usage_limits JSONB DEFAULT '{}', -- e.g., {"max_quotes_per_month": 100}

    -- Lifecycle
    started_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    auto_renew BOOLEAN DEFAULT TRUE,

    -- Metadata
    config JSONB DEFAULT '{}', -- Service-specific configuration
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(tenant_id, service_type)
);

CREATE INDEX idx_subscriptions_tenant ON tenant_subscriptions(tenant_id);
CREATE INDEX idx_subscriptions_service ON tenant_subscriptions(service_type);
CREATE INDEX idx_subscriptions_status ON tenant_subscriptions(status);

-- ============================================================================
-- USERS & AUTHENTICATION
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Authentication (managed by Supabase, but we track here too)
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,

    -- Authorization
    role VARCHAR(50) DEFAULT 'user' CHECK (
        role IN ('super_admin', 'tenant_admin', 'manager', 'user', 'viewer')
    ),
    permissions JSONB DEFAULT '[]', -- Array of permission strings

    -- Status
    status VARCHAR(50) DEFAULT 'active' CHECK (
        status IN ('active', 'inactive', 'suspended')
    ),

    -- Activity tracking
    last_login_at TIMESTAMP,
    login_count INT DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,

    UNIQUE(tenant_id, email)
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(tenant_id, role);

-- ============================================================================
-- QUOTE INTELLIGENCE SYSTEM
-- ============================================================================

-- Parts Catalog
CREATE TABLE parts_catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Part identification
    part_number VARCHAR(255) NOT NULL,
    internal_sku VARCHAR(255), -- Client's internal SKU if different
    description TEXT,
    category VARCHAR(100),
    subcategory VARCHAR(100),

    -- Specifications (flexible JSONB)
    specifications JSONB DEFAULT '{}',
    -- Example: {"voltage": "24V", "current": "10A", "io_channels": 16}

    -- Dimensions
    dimensions JSONB,
    -- Example: {"width": 100, "height": 150, "depth": 50, "unit": "mm"}

    -- Pricing
    unit_price DECIMAL(10, 2),
    cost_price DECIMAL(10, 2), -- For margin calculation
    currency VARCHAR(3) DEFAULT 'USD',
    price_valid_from DATE,
    price_valid_until DATE,

    -- Supplier information
    manufacturer VARCHAR(255),
    supplier VARCHAR(255),
    lead_time_days INT,
    minimum_order_quantity INT DEFAULT 1,

    -- Media
    datasheet_url TEXT,
    image_urls TEXT[],
    cad_file_urls TEXT[],

    -- Metadata
    tags TEXT[],
    notes TEXT,
    status VARCHAR(50) DEFAULT 'active' CHECK (
        status IN ('active', 'discontinued', 'obsolete', 'pending')
    ),

    -- Vector search metadata (stored in Qdrant, tracked here)
    vector_indexed BOOLEAN DEFAULT FALSE,
    last_indexed_at TIMESTAMP,

    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,

    UNIQUE(tenant_id, part_number)
);

CREATE INDEX idx_parts_tenant ON parts_catalog(tenant_id);
CREATE INDEX idx_parts_category ON parts_catalog(tenant_id, category);
CREATE INDEX idx_parts_status ON parts_catalog(tenant_id, status);
CREATE INDEX idx_parts_number ON parts_catalog(tenant_id, part_number);
CREATE INDEX idx_parts_specs ON parts_catalog USING GIN(specifications);
CREATE INDEX idx_parts_tags ON parts_catalog USING GIN(tags);

-- Quote Templates
CREATE TABLE quote_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Template content
    template_type VARCHAR(50) DEFAULT 'standard', -- standard, proposal, rfq_response
    header_html TEXT,
    footer_html TEXT,
    terms_and_conditions TEXT,
    sections JSONB DEFAULT '[]', -- Array of section definitions

    -- Styling
    styles JSONB DEFAULT '{}', -- CSS/styling configuration

    -- Settings
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_quote_templates_tenant ON quote_templates(tenant_id);

-- Quotes
CREATE TABLE quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Quote identification
    quote_number VARCHAR(100) NOT NULL,
    title VARCHAR(255),

    -- Customer information
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255),
    customer_phone VARCHAR(50),
    customer_company VARCHAR(255),
    customer_address JSONB,

    -- Line items
    line_items JSONB NOT NULL DEFAULT '[]',
    /* Example line item structure:
    {
        "part_id": "uuid",
        "part_number": "ABC-123",
        "description": "24V DC Input Module",
        "quantity": 5,
        "unit_price": 150.00,
        "discount_percent": 10,
        "subtotal": 675.00,
        "notes": "Expedited delivery"
    }
    */

    -- Pricing
    subtotal DECIMAL(10, 2) NOT NULL,
    discount_amount DECIMAL(10, 2) DEFAULT 0.00,
    tax_amount DECIMAL(10, 2) DEFAULT 0.00,
    shipping_amount DECIMAL(10, 2) DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',

    -- Status and workflow
    status VARCHAR(50) DEFAULT 'draft' CHECK (
        status IN ('draft', 'pending_approval', 'approved', 'sent', 'accepted', 'rejected', 'expired', 'cancelled')
    ),

    -- Workflow tracking
    created_by UUID NOT NULL REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    sent_to_customer_at TIMESTAMP,
    customer_viewed_at TIMESTAMP,
    customer_responded_at TIMESTAMP,

    -- Versioning
    version INT DEFAULT 1,
    parent_quote_id UUID REFERENCES quotes(id), -- For revisions

    -- Template used
    template_id UUID REFERENCES quote_templates(id),

    -- Validity
    valid_from DATE DEFAULT CURRENT_DATE,
    valid_until DATE,

    -- Additional info
    notes TEXT,
    internal_notes TEXT, -- Not shown to customer
    tags TEXT[],

    -- AI generation metadata
    ai_generated BOOLEAN DEFAULT FALSE,
    ai_confidence_score DECIMAL(5, 2), -- 0-100
    ai_generation_metadata JSONB,

    -- Files
    pdf_url TEXT,
    attachments TEXT[],

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,

    UNIQUE(tenant_id, quote_number)
);

CREATE INDEX idx_quotes_tenant ON quotes(tenant_id);
CREATE INDEX idx_quotes_status ON quotes(tenant_id, status);
CREATE INDEX idx_quotes_customer ON quotes(tenant_id, customer_name);
CREATE INDEX idx_quotes_created_at ON quotes(tenant_id, created_at DESC);
CREATE INDEX idx_quotes_total ON quotes(tenant_id, total_amount DESC);
CREATE INDEX idx_quotes_number ON quotes(tenant_id, quote_number);

-- Parts Matching Requests (for logging and improvement)
CREATE TABLE parts_matching_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),

    -- Input
    input_type VARCHAR(50), -- text, pdf, image, technical_drawing
    input_text TEXT,
    input_file_url TEXT,

    -- Extracted features
    extracted_features JSONB,

    -- Results
    matched_parts JSONB, -- Array of matched parts with scores
    primary_match_id UUID REFERENCES parts_catalog(id),
    confidence_score DECIMAL(5, 2),

    -- Feedback
    was_correct BOOLEAN,
    user_selected_part_id UUID REFERENCES parts_catalog(id),
    feedback_notes TEXT,

    -- Performance
    processing_time_ms INT,
    ai_model_used VARCHAR(100),

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_parts_matching_tenant ON parts_matching_requests(tenant_id);
CREATE INDEX idx_parts_matching_created ON parts_matching_requests(created_at DESC);

-- ============================================================================
-- KNOWLEDGE PRESERVATION PACKAGE
-- ============================================================================

-- Knowledge Domains (client-defined categories)
CREATE TABLE knowledge_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(50), -- For UI
    color VARCHAR(20), -- For UI

    -- Hierarchy
    parent_domain_id UUID REFERENCES knowledge_domains(id),

    -- Associated SOP template
    default_template_id UUID, -- References sop_templates(id), added later

    -- Metadata
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_knowledge_domains_tenant ON knowledge_domains(tenant_id);
CREATE INDEX idx_knowledge_domains_parent ON knowledge_domains(parent_domain_id);

-- Interviews
CREATE TABLE interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Interview details
    title VARCHAR(255) NOT NULL,
    description TEXT,

    -- Participants
    interviewee_name VARCHAR(255) NOT NULL,
    interviewee_role VARCHAR(100),
    interviewee_department VARCHAR(100),
    interviewee_years_experience INT,
    interviewer_name VARCHAR(255),

    -- Classification
    knowledge_domain_id UUID REFERENCES knowledge_domains(id),

    -- Media files
    audio_file_url TEXT,
    video_file_url TEXT,
    duration_seconds INT,
    file_size_mb DECIMAL(10, 2),

    -- Transcription
    transcript_text TEXT,
    transcript_file_url TEXT,
    transcription_status VARCHAR(50) DEFAULT 'pending' CHECK (
        transcription_status IN ('pending', 'processing', 'completed', 'failed')
    ),
    transcription_completed_at TIMESTAMP,

    -- AI Analysis
    key_insights TEXT[], -- Array of extracted insights
    topics TEXT[], -- Automatically extracted topics
    action_items TEXT[],
    mentioned_equipment TEXT[],
    mentioned_processes TEXT[],
    safety_concerns TEXT[],

    -- Interview metadata
    interview_date DATE,
    interview_location VARCHAR(255),

    -- Processing status
    status VARCHAR(50) DEFAULT 'recorded' CHECK (
        status IN ('recorded', 'transcribing', 'transcribed', 'analyzed', 'sop_generated')
    ),

    -- Generated SOPs
    generated_sop_ids UUID[], -- Array of SOP IDs generated from this interview

    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE INDEX idx_interviews_tenant ON interviews(tenant_id);
CREATE INDEX idx_interviews_domain ON interviews(tenant_id, knowledge_domain_id);
CREATE INDEX idx_interviews_status ON interviews(tenant_id, status);
CREATE INDEX idx_interviews_interviewee ON interviews(tenant_id, interviewee_name);

-- SOP Templates
CREATE TABLE sop_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Template classification
    template_category VARCHAR(100), -- manufacturing, quality, safety, maintenance, etc.
    compliance_standard VARCHAR(100), -- ISO 9001, AS9100, IATF 16949, etc.

    -- Template structure
    sections JSONB NOT NULL DEFAULT '[]',
    /* Example section structure:
    {
        "title": "Purpose",
        "order": 1,
        "required": true,
        "prompt": "Explain the purpose of this procedure",
        "example": "This SOP describes..."
    }
    */

    -- Required fields
    required_metadata JSONB DEFAULT '{}',

    -- Styling
    header_template TEXT,
    footer_template TEXT,
    styles JSONB DEFAULT '{}',

    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_sop_templates_tenant ON sop_templates(tenant_id);
CREATE INDEX idx_sop_templates_category ON sop_templates(tenant_id, template_category);

-- Add foreign key for knowledge_domains.default_template_id
ALTER TABLE knowledge_domains
    ADD CONSTRAINT fk_knowledge_domains_template
    FOREIGN KEY (default_template_id)
    REFERENCES sop_templates(id);

-- SOPs (Standard Operating Procedures)
CREATE TABLE sops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- SOP identification
    sop_number VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,

    -- Classification
    knowledge_domain_id UUID REFERENCES knowledge_domains(id),
    template_id UUID REFERENCES sop_templates(id),

    -- Content
    content_markdown TEXT NOT NULL,
    content_html TEXT, -- Generated from markdown

    -- Metadata
    purpose TEXT,
    scope TEXT,
    responsible_role VARCHAR(255),
    required_equipment TEXT[],
    required_materials TEXT[],
    safety_requirements TEXT[],
    quality_checkpoints TEXT[],
    estimated_duration_minutes INT,

    -- Source
    source_interview_id UUID REFERENCES interviews(id),
    ai_generated BOOLEAN DEFAULT FALSE,
    ai_generation_prompt TEXT,

    -- Status and workflow
    status VARCHAR(50) DEFAULT 'draft' CHECK (
        status IN ('draft', 'under_review', 'approved', 'published', 'archived', 'obsolete')
    ),

    -- Review process
    reviewer_assignments JSONB DEFAULT '[]',
    /* Example reviewer assignment:
    {
        "user_id": "uuid",
        "assigned_at": "timestamp",
        "completed_at": "timestamp",
        "status": "pending|approved|rejected",
        "comments": "text"
    }
    */

    approval_history JSONB DEFAULT '[]',

    -- Versioning
    version INT DEFAULT 1,
    parent_sop_id UUID REFERENCES sops(id),
    effective_date DATE,
    review_due_date DATE,
    review_frequency_days INT DEFAULT 365, -- Annual review by default

    -- Publishing
    published_at TIMESTAMP,
    published_by UUID REFERENCES users(id),
    last_reviewed_at TIMESTAMP,
    last_reviewed_by UUID REFERENCES users(id),

    -- Usage tracking
    view_count INT DEFAULT 0,
    download_count INT DEFAULT 0,

    -- Files
    pdf_url TEXT,
    docx_url TEXT,

    -- Tags for searchability
    tags TEXT[],

    created_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,

    UNIQUE(tenant_id, sop_number)
);

CREATE INDEX idx_sops_tenant ON sops(tenant_id);
CREATE INDEX idx_sops_domain ON sops(tenant_id, knowledge_domain_id);
CREATE INDEX idx_sops_status ON sops(tenant_id, status);
CREATE INDEX idx_sops_number ON sops(tenant_id, sop_number);
CREATE INDEX idx_sops_title ON sops USING gin(to_tsvector('english', title));
CREATE INDEX idx_sops_tags ON sops USING GIN(tags);

-- ============================================================================
-- ERP COPILOT
-- ============================================================================

-- ERP Systems Configuration
CREATE TABLE erp_systems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- System identification
    name VARCHAR(255) NOT NULL, -- e.g., "SAP", "Oracle ERP", "Epicor"
    version VARCHAR(100),

    -- Configuration
    system_type VARCHAR(100), -- sap, oracle, epicor, netsuite, custom
    connection_config JSONB, -- For future live integration

    -- Modules enabled
    modules TEXT[], -- Finance, Inventory, Production, HR, etc.

    -- Customizations
    custom_terminology JSONB DEFAULT '{}', -- Map standard terms to client-specific terms
    /* Example: {"purchase_order": "PO", "work_order": "Job Ticket"} */

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_erp_systems_tenant ON erp_systems(tenant_id);

-- ERP Documentation
CREATE TABLE erp_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    erp_system_id UUID REFERENCES erp_systems(id),

    -- Document classification
    title VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) CHECK (
        document_type IN ('manual', 'video', 'screenshot', 'training_doc', 'faq', 'release_notes')
    ),
    module_name VARCHAR(100), -- Which ERP module this relates to

    -- File information
    file_url TEXT,
    file_size_mb DECIMAL(10, 2),
    file_format VARCHAR(50), -- pdf, docx, mp4, jpg, etc.

    -- Extracted content
    content_text TEXT, -- Extracted text for search
    page_count INT,

    -- Metadata
    description TEXT,
    tags TEXT[],
    related_topics TEXT[],
    difficulty_level VARCHAR(50), -- beginner, intermediate, advanced

    -- Vector indexing
    vector_indexed BOOLEAN DEFAULT FALSE,
    last_indexed_at TIMESTAMP,

    -- Usage analytics
    view_count INT DEFAULT 0,
    helpful_count INT DEFAULT 0,
    unhelpful_count INT DEFAULT 0,
    avg_rating DECIMAL(3, 2), -- 0.00 to 5.00

    -- Publishing
    is_published BOOLEAN DEFAULT TRUE,
    published_at TIMESTAMP DEFAULT NOW(),

    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE INDEX idx_erp_docs_tenant ON erp_documents(tenant_id);
CREATE INDEX idx_erp_docs_system ON erp_documents(erp_system_id);
CREATE INDEX idx_erp_docs_module ON erp_documents(tenant_id, module_name);
CREATE INDEX idx_erp_docs_type ON erp_documents(document_type);
CREATE INDEX idx_erp_docs_title ON erp_documents USING gin(to_tsvector('english', title));
CREATE INDEX idx_erp_docs_content ON erp_documents USING gin(to_tsvector('english', content_text));

-- ERP Queries (user questions)
CREATE TABLE erp_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),

    -- Query details
    query_text TEXT NOT NULL,
    query_context TEXT, -- Additional context provided by user

    -- Classification
    intent_classified VARCHAR(100), -- how_to, what_is, troubleshooting, navigation, etc.
    module_identified VARCHAR(100),
    confidence_level VARCHAR(50), -- high, medium, low

    -- Search results
    matched_document_ids UUID[], -- Array of erp_documents.id
    search_method VARCHAR(50), -- semantic, keyword, hybrid

    -- Response
    answer_text TEXT,
    answer_sources JSONB, -- Array of document references with snippets
    answer_confidence DECIMAL(5, 2), -- 0-100

    -- Feedback
    was_helpful BOOLEAN,
    feedback_text TEXT,
    user_selected_document_id UUID REFERENCES erp_documents(id),

    -- Alternative queries suggested
    suggested_queries TEXT[],

    -- Performance
    response_time_ms INT,
    ai_model_used VARCHAR(100),

    -- Follow-up tracking
    parent_query_id UUID REFERENCES erp_queries(id), -- For conversation threading

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_erp_queries_tenant ON erp_queries(tenant_id);
CREATE INDEX idx_erp_queries_user ON erp_queries(user_id);
CREATE INDEX idx_erp_queries_created ON erp_queries(created_at DESC);
CREATE INDEX idx_erp_queries_helpful ON erp_queries(was_helpful) WHERE was_helpful IS NOT NULL;

-- Common Queries Library (auto-populated from frequently asked questions)
CREATE TABLE erp_common_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    question TEXT NOT NULL,
    answer TEXT NOT NULL,

    -- Classification
    category VARCHAR(100),
    module_name VARCHAR(100),

    -- Metadata
    ask_count INT DEFAULT 0, -- How many times this was asked
    helpful_count INT DEFAULT 0,

    -- Related documents
    related_document_ids UUID[],

    -- Management
    is_published BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 0, -- Higher priority shown first

    created_from_query_id UUID REFERENCES erp_queries(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_erp_common_tenant ON erp_common_queries(tenant_id);
CREATE INDEX idx_erp_common_category ON erp_common_queries(tenant_id, category);

-- ============================================================================
-- USAGE TRACKING & BILLING
-- ============================================================================

-- Usage Metrics (for billing and analytics)
CREATE TABLE usage_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    subscription_id UUID REFERENCES tenant_subscriptions(id),

    -- Metric details
    service_type VARCHAR(50) NOT NULL, -- quote_intelligence, knowledge_preservation, erp_copilot
    metric_type VARCHAR(100) NOT NULL,
    /* Metric types:
       - quote_generated
       - parts_matched
       - sop_generated
       - interview_transcribed
       - erp_query_answered
       - api_call
       - storage_used_mb
       - ai_tokens_used
    */

    metric_value DECIMAL(15, 2) DEFAULT 1,
    unit VARCHAR(50), -- count, mb, tokens, etc.

    -- Cost tracking
    cost_amount DECIMAL(10, 4), -- Actual cost incurred (e.g., AI API cost)

    -- Context
    metadata JSONB DEFAULT '{}',
    resource_id UUID, -- ID of related resource (quote, SOP, etc.)

    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_usage_tenant_service ON usage_metrics(tenant_id, service_type, recorded_at DESC);
CREATE INDEX idx_usage_subscription ON usage_metrics(subscription_id);
CREATE INDEX idx_usage_recorded ON usage_metrics(recorded_at DESC);

-- Invoices
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Invoice identification
    invoice_number VARCHAR(100) UNIQUE NOT NULL,

    -- Billing period
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,

    -- Amounts
    subtotal DECIMAL(10, 2) NOT NULL,
    tax_rate DECIMAL(5, 4), -- e.g., 0.0825 for 8.25%
    tax_amount DECIMAL(10, 2) DEFAULT 0.00,
    discount_amount DECIMAL(10, 2) DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL,
    amount_paid DECIMAL(10, 2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',

    -- Line items breakdown
    line_items JSONB NOT NULL DEFAULT '[]',
    /* Example:
    {
        "description": "Quote Intelligence - Professional Plan",
        "quantity": 1,
        "unit_price": 750.00,
        "amount": 750.00,
        "service_type": "quote_intelligence"
    }
    */

    -- Status
    status VARCHAR(50) DEFAULT 'pending' CHECK (
        status IN ('draft', 'pending', 'sent', 'paid', 'partial_paid', 'overdue', 'cancelled', 'void')
    ),

    -- Important dates
    issue_date DATE DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    sent_at TIMESTAMP,
    paid_at TIMESTAMP,

    -- Payment
    payment_method VARCHAR(50),
    payment_transaction_id VARCHAR(255),

    -- Notes
    notes TEXT,

    -- Files
    pdf_url TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_invoices_tenant ON invoices(tenant_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_due ON invoices(due_date);
CREATE INDEX idx_invoices_period ON invoices(billing_period_start, billing_period_end);

-- ============================================================================
-- AUDIT LOG
-- ============================================================================

CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),

    -- Action details
    action VARCHAR(100) NOT NULL, -- created, updated, deleted, viewed, exported, etc.
    resource_type VARCHAR(100) NOT NULL, -- quote, sop, part, etc.
    resource_id UUID,

    -- Changes
    old_values JSONB,
    new_values JSONB,

    -- Request context
    ip_address INET,
    user_agent TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant ON audit_log(tenant_id, created_at DESC);
CREATE INDEX idx_audit_user ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_action ON audit_log(action);

-- ============================================================================
-- SYSTEM CONFIGURATION
-- ============================================================================

CREATE TABLE system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE, -- Encrypt if true
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- NOTIFICATIONS
-- ============================================================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Notification details
    type VARCHAR(50) NOT NULL, -- quote_approved, sop_needs_review, invoice_due, etc.
    title VARCHAR(255) NOT NULL,
    message TEXT,

    -- Action
    action_url TEXT,
    action_label VARCHAR(100),

    -- Status
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,

    -- Priority
    priority VARCHAR(50) DEFAULT 'normal', -- low, normal, high, urgent

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, is_read, created_at DESC);
CREATE INDEX idx_notifications_tenant ON notifications(tenant_id);

-- ============================================================================
-- ROW-LEVEL SECURITY POLICIES
-- ============================================================================

-- Enable RLS on all tenant-aware tables
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE parts_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE interviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE sops ENABLE ROW LEVEL SECURITY;
ALTER TABLE erp_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE erp_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Example policy (will be customized based on application needs)
CREATE POLICY tenant_isolation_policy ON quotes
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Similar policies for other tables...

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quotes_updated_at BEFORE UPDATE ON quotes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_parts_catalog_updated_at BEFORE UPDATE ON parts_catalog
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sops_updated_at BEFORE UPDATE ON sops
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_interviews_updated_at BEFORE UPDATE ON interviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Active tenants with their subscriptions
CREATE VIEW active_tenants_with_subscriptions AS
SELECT
    t.id as tenant_id,
    t.company_name,
    t.slug,
    t.status as tenant_status,
    json_agg(
        json_build_object(
            'service_type', ts.service_type,
            'status', ts.status,
            'monthly_fee', ts.monthly_fee
        )
    ) as subscriptions,
    COUNT(u.id) as user_count
FROM tenants t
LEFT JOIN tenant_subscriptions ts ON t.id = ts.tenant_id
LEFT JOIN users u ON t.id = u.tenant_id AND u.status = 'active'
WHERE t.status = 'active'
GROUP BY t.id, t.company_name, t.slug, t.status;

-- Quote statistics by tenant
CREATE VIEW quote_statistics AS
SELECT
    tenant_id,
    COUNT(*) as total_quotes,
    COUNT(CASE WHEN status = 'accepted' THEN 1 END) as accepted_quotes,
    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_quotes,
    SUM(total_amount) as total_quoted_amount,
    SUM(CASE WHEN status = 'accepted' THEN total_amount ELSE 0 END) as total_won_amount,
    CASE
        WHEN COUNT(*) > 0 THEN
            ROUND(100.0 * COUNT(CASE WHEN status = 'accepted' THEN 1 END) / COUNT(*), 2)
        ELSE 0
    END as win_rate_percent
FROM quotes
WHERE deleted_at IS NULL
GROUP BY tenant_id;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert system config defaults
INSERT INTO system_config (config_key, config_value, description) VALUES
('ai_provider', '{"primary": "anthropic", "fallback": "openai"}', 'AI service provider configuration'),
('max_file_upload_mb', '100', 'Maximum file upload size in MB'),
('default_currency', '"USD"', 'Default currency for billing'),
('email_notifications_enabled', 'true', 'Enable email notifications'),
('session_timeout_minutes', '60', 'User session timeout in minutes');

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Additional composite indexes for common query patterns
CREATE INDEX idx_quotes_tenant_created_status ON quotes(tenant_id, created_at DESC, status);
CREATE INDEX idx_sops_tenant_domain_status ON sops(tenant_id, knowledge_domain_id, status);
CREATE INDEX idx_usage_tenant_service_date ON usage_metrics(tenant_id, service_type, recorded_at DESC);

-- Full-text search indexes
CREATE INDEX idx_parts_description_fts ON parts_catalog USING gin(to_tsvector('english', description));
CREATE INDEX idx_sops_content_fts ON sops USING gin(to_tsvector('english', content_markdown));

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

-- Grant permissions (adjust based on your user setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO manufacturing_ai_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO manufacturing_ai_app;
