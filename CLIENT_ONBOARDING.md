# Client Onboarding Guide

## Overview

This guide outlines the standardized process for onboarding new manufacturing clients to the Manufacturing AI System across all three service tiers.

**Onboarding Timeline**: 3-5 weeks
**Success Rate Target**: >90% completion
**Time to Value**: <2 weeks for first service

---

## Onboarding Process Overview

```
Week 1: Discovery & Setup
  ↓
Week 2-3: Data Import & Configuration
  ↓
Week 4: Training & Testing
  ↓
Week 5: Go-Live & Support
```

---

## Phase 1: Pre-Onboarding (Before Day 1)

### Sales Handoff Checklist

**Completed by Sales Team**:
- [ ] Signed contract with selected services
- [ ] Pricing confirmed and billing setup
- [ ] Primary contact designated
- [ ] Kickoff meeting scheduled
- [ ] Implementation questionnaire sent

**Questionnaire (sent to client)**:
```
1. Company Information
   - Legal name
   - Industry/vertical
   - Number of employees
   - Manufacturing processes (brief overview)

2. Service Selection
   □ Quote Intelligence System
   □ Knowledge Preservation Package
   □ ERP Copilot

3. For Quote Intelligence:
   - Current quoting process (tools, average time)
   - Parts catalog format (PDF, Excel, ERP export, custom database)
   - Typical quote volume per month
   - Number of users who will generate quotes

4. For Knowledge Preservation:
   - Number of retiring employees in next 12 months
   - Key knowledge domains to capture
   - Existing SOP format/system
   - Compliance standards (ISO 9001, AS9100, etc.)

5. For ERP Copilot:
   - ERP system name and version
   - Modules in use
   - Existing documentation location
   - Number of ERP users

6. Technical Details
   - IT contact name and email
   - Preferred go-live date
   - Integration requirements
   - Security/compliance requirements
```

### Implementation Team Assignment

**Assign**:
- Implementation Lead (primary contact)
- Technical Specialist
- Training Coordinator

**Notify Client** of team with contact info

---

## Phase 2: Discovery & Setup (Week 1)

### Day 1: Kickoff Meeting (60 minutes)

**Agenda**:
1. Introductions (10 min)
   - Implementation team
   - Client stakeholders
2. Project Overview (15 min)
   - Timeline
   - Milestones
   - Success criteria
3. Current State Assessment (20 min)
   - Review questionnaire responses
   - Identify pain points
   - Clarify requirements
4. Next Steps (15 min)
   - Data requirements
   - Access needed
   - Action items

**Deliverables**:
- Kickoff meeting notes
- Action items list
- Customized project plan

### Day 2-3: Tenant Provisioning

**Technical Setup**:
- [ ] Create tenant in system
  ```bash
  # Admin creates tenant
  POST /api/v1/tenants
  {
    "company_name": "Acme Manufacturing",
    "slug": "acme-manufacturing",
    "industry": "Automotive",
    "primary_contact_email": "john@acme.com"
  }
  ```

- [ ] Provision services
  ```bash
  # Add subscriptions
  POST /api/v1/tenants/{id}/subscriptions
  {
    "service_type": "quote_intelligence",
    "pricing_plan": "monthly",
    "monthly_fee": 750.00
  }
  ```

- [ ] Set up storage buckets
- [ ] Create vector collections
- [ ] Configure authentication

- [ ] Create admin user
  ```bash
  POST /api/v1/tenants/{id}/users
  {
    "email": "john@acme.com",
    "full_name": "John Smith",
    "role": "tenant_admin"
  }
  ```

**Email to Client**:
```
Subject: Welcome to Manufacturing AI - Your Account is Ready

Hi [Name],

Your Manufacturing AI account is now set up! Here are your details:

Login URL: https://[tenant-slug].manufacturing-ai.com
Admin Email: [email]
Temporary Password: [sent separately]

Next Steps:
1. Log in and change your password
2. Review the onboarding checklist in your dashboard
3. Upload initial data (instructions attached)

Your Implementation Lead: [Name] ([email])
Support: support@manufacturing-ai.com

Best regards,
The Manufacturing AI Team
```

### Day 4-5: Initial Data Collection

**For Quote Intelligence**:
- [ ] Parts catalog data
  - Format: CSV template provided OR existing catalog file
  - Required fields: part_number, description, unit_price
  - Optional: specifications, dimensions, images
- [ ] Historical quotes (optional)
  - Past 6-12 months recommended
  - CSV template provided
- [ ] Quote template preferences
  - Logo (PNG/SVG, minimum 300x100px)
  - Colors (hex codes)
  - Terms and conditions text

**For Knowledge Preservation**:
- [ ] Knowledge domain list
  - Domain names (e.g., "CNC Machining", "Quality Control")
  - Categories/subcategories
- [ ] Employee list for interviews
  - Name, role, department, expertise area
- [ ] Existing SOP samples (for template matching)
- [ ] Compliance requirements

**For ERP Copilot**:
- [ ] ERP documentation
  - User manuals (PDF)
  - Training videos (mp4, YouTube links)
  - Screenshots of key processes
  - Internal how-to guides
- [ ] ERP system details
  - System name, version
  - Modules in use
  - Custom terminology/acronyms

**Data Transfer Options**:
1. **Secure Upload Portal** (preferred)
   - Client uploads via web interface
   - Encrypted transmission
2. **Email** (small files <25MB)
3. **SFTP/Cloud Storage Link** (large files)

---

## Phase 3: Data Import & Configuration (Week 2-3)

### Week 2: Data Processing

#### Quote Intelligence Setup

**Step 1: Import Parts Catalog**
```bash
# Via API or Admin UI
POST /api/v1/quote-intelligence/catalogs/upload
Content-Type: multipart/form-data
file: parts_catalog.csv
```

**Processing**:
- Validate data format
- Check for duplicates
- Flag missing required fields
- Generate preview for client review

**Client Review**:
- Show first 10 parts
- Highlight any issues
- Get approval to proceed

**Step 2: Index Catalog**
- Generate embeddings
- Build vector index
- Test search functionality

**Step 3: Configure Quote Templates**
- Upload logo and branding
- Customize template sections
- Set default terms and conditions
- Generate sample quote for approval

**Step 4: Import Historical Quotes** (if provided)
- Validate format
- Import to database
- Verify search functionality

#### Knowledge Preservation Setup

**Step 1: Set Up Knowledge Domains**
```bash
POST /api/v1/knowledge/domains
{
  "name": "CNC Machining",
  "description": "CNC machine operation and maintenance"
}
```

**Step 2: Configure SOP Templates**
- Select or customize templates
- Match to compliance standards
- Set approval workflows

**Step 3: Create Interview Schedule** (if applicable)
- Identify interviewees
- Schedule interviews
- Prepare interview guides

#### ERP Copilot Setup

**Step 1: Configure ERP System**
```bash
POST /api/v1/erp-copilot/systems
{
  "name": "SAP ERP",
  "version": "S/4HANA",
  "modules": ["Finance", "Inventory", "Production"]
}
```

**Step 2: Upload Documentation**
- Bulk upload manuals
- Process and extract text
- Generate embeddings
- Index for search

**Step 3: Set Up Custom Terminology**
- Map standard terms to client terms
- Configure for better query understanding

### Week 3: Configuration & Testing

**For All Services**:
- [ ] Add additional users
- [ ] Set up role-based permissions
- [ ] Configure notifications
- [ ] Set usage limits (if applicable)
- [ ] Test key workflows

**Internal Testing Checklist**:

**Quote Intelligence**:
- [ ] Search for parts by keyword
- [ ] Match part from description
- [ ] Generate test quote
- [ ] Export quote to PDF
- [ ] Search historical quotes

**Knowledge Preservation**:
- [ ] Upload test interview
- [ ] Verify transcription
- [ ] Generate SOP from interview
- [ ] Review and approve SOP
- [ ] Export SOP to PDF

**ERP Copilot**:
- [ ] Ask 10 common questions
- [ ] Verify answer accuracy
- [ ] Check source citations
- [ ] Test "helpful" feedback

**Issue Resolution**:
- Document any issues
- Fix or workaround
- Re-test

---

## Phase 4: Training (Week 4)

### Training Schedule

**Session 1: Admin Training** (90 minutes)
- For: Admin users, IT contact
- Covers:
  - User management
  - System configuration
  - Data management
  - Reporting and analytics
  - Troubleshooting

**Session 2: Quote Intelligence Training** (60 minutes)
- For: Sales, quoting team
- Covers:
  - Searching parts catalog
  - Matching parts from drawings/descriptions
  - Generating quotes
  - Customizing quotes
  - Managing quote pipeline
  - Best practices

**Session 3: Knowledge Preservation Training** (60 minutes)
- For: HR, operations managers
- Covers:
  - Uploading interviews
  - Reviewing transcripts
  - Generating SOPs
  - Review and approval workflow
  - Publishing and distribution

**Session 4: ERP Copilot Training** (45 minutes)
- For: All ERP users
- Covers:
  - Asking questions
  - Understanding answers
  - Providing feedback
  - Using common queries

**Training Format**:
- Live Zoom sessions (recorded)
- Hands-on demos
- Q&A
- Practice exercises

**Training Materials Provided**:
- Video recordings
- PDF user guides
- Quick reference cards
- FAQ document

### Sandbox Testing (Week 4, Days 4-5)

**Client Tasks**:
- [ ] Each user logs in
- [ ] Complete practice exercises
- [ ] Ask questions
- [ ] Provide feedback

**Practice Exercises**:

**Quote Intelligence**:
1. Find a specific part by part number
2. Match a part from a description you provide
3. Generate a quote for a sample customer
4. Search for a historical quote

**Knowledge Preservation**:
1. Upload a sample interview
2. Review the transcript
3. Generate an SOP
4. Submit for review

**ERP Copilot**:
1. Ask "How do I create a purchase order?"
2. Ask "Where do I find inventory reports?"
3. Provide feedback on answers

**Success Criteria**:
- All users successfully log in
- All practice exercises completed
- <5 support tickets per service
- >80% user satisfaction

---

## Phase 5: Go-Live (Week 5)

### Day 1: Production Activation

**Pre-Go-Live Checklist**:
- [ ] All data imported and verified
- [ ] All users trained
- [ ] Sandbox testing completed
- [ ] No critical issues outstanding
- [ ] Client approval to go live

**Activation**:
- [ ] Switch to production mode
- [ ] Notify all users
- [ ] Monitor for issues

**Go-Live Email**:
```
Subject: Manufacturing AI is Now Live!

Hi Team,

We're excited to announce that Manufacturing AI is now live for production use!

What's Available:
✓ [List enabled services]

How to Access:
URL: https://[tenant-slug].manufacturing-ai.com
Use your existing credentials

Support:
- Email: support@manufacturing-ai.com
- Live chat: Available in app
- Your Implementation Lead: [Name] ([email])

Remember:
- Review the user guides if you need a refresher
- Don't hesitate to ask questions
- Provide feedback to help us improve

Let's make this a success together!

Best regards,
The Manufacturing AI Team
```

### Week 5: Intensive Monitoring

**Daily Activities**:
- [ ] Check usage metrics
- [ ] Review error logs
- [ ] Monitor performance
- [ ] Respond to support tickets (< 2 hour response time)
- [ ] Daily check-in call with client

**Metrics to Track**:
- Active users
- Feature usage
- Error rate
- Response times
- User feedback

**Week 1 Check-in Call** (Friday)
- Review usage
- Address concerns
- Collect feedback
- Identify quick wins

---

## Phase 6: Ongoing Success (Week 6+)

### Success Metrics Tracking

**Weekly (Weeks 6-8)**:
- Usage reports
- User adoption rates
- Support tickets
- Feature requests

**Monthly**:
- Business review call
- Usage analytics
- ROI tracking
- Roadmap discussion

**Quarterly**:
- Strategic review
- Service optimization
- Contract renewal discussion
- Feature prioritization

### Client Success Milestones

**30 Days**:
- [ ] 80%+ user adoption
- [ ] First quote generated (Quote Intelligence)
- [ ] First SOP published (Knowledge Preservation)
- [ ] 100+ queries answered (ERP Copilot)
- [ ] <5% error rate

**60 Days**:
- [ ] 50+ quotes generated
- [ ] Measurable time savings
- [ ] Positive user feedback (NPS >50)
- [ ] Feature requests prioritized

**90 Days**:
- [ ] ROI demonstrated
- [ ] Workflow fully integrated
- [ ] Upsell opportunities identified
- [ ] Renewal discussion started

---

## Self-Service Onboarding (Future)

For lower tiers or tech-savvy clients, offer self-service option:

**Automated Flow**:
1. **Sign-up**: Complete online form
2. **Tenant Creation**: Automatic provisioning
3. **Setup Wizard**: Step-by-step configuration
4. **Data Upload**: Guided upload process
5. **Video Tutorials**: Self-paced learning
6. **Go-Live**: Automated activation after checklist completion

**Timeline**: 48-72 hours

**Support**:
- Live chat
- Email support
- Video library
- Knowledge base

---

## Onboarding Metrics & KPIs

| Metric | Target |
|--------|--------|
| Time to First Value | <14 days |
| Onboarding Completion Rate | >90% |
| User Adoption (30 days) | >80% |
| Training Attendance | >90% |
| Support Tickets (Week 1) | <10 |
| Customer Satisfaction | >4.5/5 |
| Feature Activation Rate | >75% |

---

## Common Onboarding Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| **Incomplete data provided** | Provide clear templates, examples, and reminders |
| **Low user adoption** | Executive sponsorship, change management, incentives |
| **Technical integration issues** | Pre-onboarding technical discovery, dedicated support |
| **Resistance to AI** | Education on AI capabilities, show ROI, human-in-loop |
| **Complex approval workflows** | Start simple, iterate, customize later |
| **Slow response from client** | Set clear deadlines, escalation path, executive alignment |

---

## Onboarding Tools & Resources

### For Implementation Team

**Tools**:
- Project management: ClickUp/Asana
- Communication: Slack Connect
- Screen sharing: Zoom
- Documentation: Notion/Confluence
- File sharing: Google Drive/Dropbox

**Templates**:
- Kickoff meeting agenda
- Project plan template
- Data collection templates
- Training slides
- Go-live checklist

### For Client

**Resources**:
- Welcome packet (PDF)
- Video library
- User guides (per service)
- Quick reference cards
- FAQ document
- Support contact card

---

## Onboarding Team Responsibilities

### Implementation Lead
- Primary client contact
- Project management
- Status updates
- Escalation point

### Technical Specialist
- Data import
- System configuration
- Integration support
- Technical troubleshooting

### Training Coordinator
- Schedule training sessions
- Deliver training
- Create training materials
- Measure training effectiveness

### Customer Success Manager (Post-Onboarding)
- Ongoing relationship
- Usage monitoring
- Expansion opportunities
- Renewal management

---

## Appendix: Data Templates

### Parts Catalog CSV Template

```csv
part_number,description,category,unit_price,manufacturer,specifications
ABC-001,"24V DC Input Module, 16 channels",Digital I/O,150.00,Siemens,"{""voltage"": ""24V"", ""channels"": 16}"
ABC-002,"Pressure Sensor 0-100 PSI",Sensors,85.00,Honeywell,"{""range"": ""0-100 PSI"", ""output"": ""4-20mA""}"
```

### Historical Quotes CSV Template

```csv
quote_number,customer_name,quote_date,total_amount,status,line_items_json
Q-2024-001,Acme Corp,2024-01-15,1500.00,accepted,"[{""part_number"": ""ABC-001"", ""quantity"": 10, ""unit_price"": 150.00}]"
```

### Knowledge Domains Template

```csv
domain_name,description,compliance_standard
CNC Machining,Operation and programming of CNC machines,ISO 9001
Quality Control,Inspection and testing procedures,AS9100
Maintenance,Preventive and corrective maintenance,ISO 55000
```

---

**Document Version**: 1.0
**Last Updated**: 2026-01-05
**Owner**: Customer Success Team
