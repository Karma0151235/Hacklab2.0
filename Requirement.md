
MARKET INTELLIGENCE &
FINANCIAL ANALYTICS MVP
Detailed Implementation Plan


Prepared for: AmBank Group
Version 1.0 | January 2026
 
1. Executive Summary
This implementation plan outlines the development of a Market Intelligence and Financial Analytics MVP designed to transform raw market data into actionable intelligence for AmBank Group. The system will ingest Bursa Malaysia filings, targeted news sources, and financial documents, applying advanced NLP and analytics to surface critical insights through an intuitive dashboard with AI-powered copilot capabilities.

1.1 Key Objectives
•	Automate ingestion of Bursa announcements and major Malaysian news sources
•	Transform unstructured data into structured intelligence via NLP categorization, sentiment analysis, and entity extraction
•	Standardize financial statements from PDFs into clean, comparable financial ratios
•	Deliver real-time intelligence through configurable dashboards and alerts
•	Provide a GenAI Copilot with RAG-based grounded answers, citations, and transparent reasoning

1.2 Success Criteria
Metric	Target
Data Ingestion Coverage	≥95% of Bursa announcements within 15 minutes
Sentiment Accuracy	≥85% agreement with human evaluation
Financial OCR Accuracy	≥95% field extraction accuracy
Copilot Response Quality	≥90% grounded with valid citations
System Uptime	≥99.5% availability
 
2. System Architecture Overview
The MVP follows a modular, microservices-based architecture designed for scalability, maintainability, and compliance with enterprise security requirements.

2.1 High-Level Architecture
Layer	Components
Data Ingestion	Bursa Connector, News Scrapers, File Upload Service, Message Queue (Kafka/RabbitMQ)
Processing	NLP Pipeline, OCR Engine, Financial Parser, Entity Extractor, Sentiment Analyzer
Storage	PostgreSQL (structured), Elasticsearch (search), Vector DB (embeddings), S3 (documents)
Intelligence	Alert Engine, Analytics Service, Company 360 Aggregator
Presentation	React Dashboard, REST/GraphQL API, WebSocket (real-time updates)
AI/Copilot	RAG Pipeline, LLM Service, Citation Engine, Reasoning Chain Logger

2.2 Technology Stack
Category	Primary Choice	Rationale
Backend Framework	Python (FastAPI)	Rich NLP ecosystem, async support
Frontend	React + TypeScript	Type safety, component ecosystem
Database	PostgreSQL 15+	ACID compliance, JSON support
Search Engine	Elasticsearch 8.x	Full-text search, analytics
Vector Store	Pinecone / pgvector	RAG similarity search
OCR Engine	Azure Document Intelligence	High accuracy for financial docs
LLM Provider	Claude API (Anthropic)	Strong reasoning, safety
Message Queue	Apache Kafka	High throughput, durability
Container Platform	Kubernetes (AKS/EKS)	Scalability, orchestration
 
3. Implementation Phases
Phase 1: Foundation & Data Infrastructure (Weeks 1-4)
Establish core infrastructure, data pipelines, and initial connector framework.

3.1.1 Infrastructure Setup
Week	Deliverable	Owner
1	Kubernetes cluster provisioning with namespaces for dev/staging/prod	DevOps Lead
1	CI/CD pipeline setup (GitHub Actions / Azure DevOps)	DevOps Lead
1-2	PostgreSQL cluster with read replicas, backup policies	Data Engineer
2	Elasticsearch cluster with index templates	Data Engineer
2	S3-compatible object storage configuration	DevOps Lead
2-3	Kafka cluster with topic architecture	Backend Lead
3	Vector database setup (Pinecone or pgvector)	ML Engineer
3-4	API gateway and authentication service (OAuth 2.0 / OIDC)	Backend Lead

3.1.2 Data Connectors Development
Bursa Malaysia Connector:
•	Implement RSS/API integration for announcement feeds
•	Build scraper for filing PDFs with rate limiting and retry logic
•	Create announcement type classifier (Corporate Actions, Financial Results, Material Events, etc.)
•	Establish deduplication logic using announcement IDs and content hashing

News Source Connectors (The Edge, The Star, NST, Malay Mail):
•	Develop RSS feed parsers with content extraction
•	Implement article scraping with robots.txt compliance
•	Build content normalizer for consistent data structure
•	Create source-specific parsers for metadata extraction

File Upload Service:
•	RESTful API for PDF/CSV uploads with virus scanning
•	File validation and type detection
•	Chunking support for large files (>100MB)
•	Integration with processing queue
 
Phase 2: NLP & Analytics Pipeline (Weeks 5-8)
Build the core intelligence layer with NLP capabilities.

3.2.1 Qualitative Categorization Engine
Category Type	Sub-categories
Corporate Actions	Dividends, Stock Splits, Rights Issues, Bonus Issues, Mergers & Acquisitions, Share Buybacks
Financial Performance	Quarterly Results, Annual Reports, Profit Warnings, Revenue Guidance, Earnings Surprises
Regulatory/Compliance	Board Changes, Audit Opinions, Related Party Transactions, Unusual Market Activity
Material Events	Contract Wins, Litigation, Default, Restructuring, Major Investments
Market News	Industry Analysis, Economic Indicators, Competitor News, Regulatory Changes

Implementation approach: Hybrid model combining rule-based classification for structured announcements with fine-tuned transformer models (e.g., FinBERT) for news articles.

3.2.2 Sentiment Analysis with Rationale
Architecture:
•	Multi-class sentiment classification: Strong Positive, Positive, Neutral, Negative, Strong Negative
•	Aspect-based sentiment for multi-topic documents
•	Explainability layer using attention weights and LIME/SHAP
•	Confidence scoring with uncertainty quantification

Output Schema:
•	overall_sentiment: enum (5 classes)
•	confidence: float (0-1)
•	rationale: string (2-3 sentence explanation)
•	key_phrases: array of sentiment-driving phrases
•	aspect_sentiments: object mapping topics to sentiment scores

3.2.3 Entity & Relationship Extraction
Named Entity Recognition (NER):
•	Companies: Listed entities, subsidiaries, competitors
•	People: Directors, executives, key personnel
•	Financial: Amounts, percentages, dates, periods
•	Regulatory: Acts, sections, compliance terms
•	Custom entities: Stock codes, industry terms

Relationship Extraction:
•	Company-Company: Parent-subsidiary, competitor, partner, supplier-customer
•	Person-Company: Director-of, CEO-of, shareholder-of
•	Event-Company: Affects, originates-from, targets
•	Build knowledge graph in Neo4j for relationship queries
 
Phase 3: Financial Statement Processing (Weeks 9-12)
Develop OCR/NLP pipeline for financial document standardization.

3.3.1 Document Processing Pipeline
1.	PDF Ingestion: Accept multi-page financial PDFs with table detection
2.	OCR Processing: Azure Document Intelligence with table extraction
3.	Structure Detection: Identify Income Statement, Balance Sheet, Cash Flow sections
4.	Field Mapping: Map extracted values to standardized taxonomy
5.	Validation: Cross-check totals, balance equations, YoY consistency
6.	Storage: Persist raw, processed, and validated data with lineage

3.3.2 Financial Ratios Engine (Minimum 10 Key Metrics)
Category	Ratio	Formula
Profitability	Return on Equity (ROE)	Net Income / Shareholders' Equity
Profitability	Net Profit Margin	Net Income / Revenue
Profitability	Return on Assets (ROA)	Net Income / Total Assets
Liquidity	Current Ratio	Current Assets / Current Liabilities
Liquidity	Quick Ratio	(Current Assets - Inventory) / Current Liabilities
Leverage	Debt-to-Equity	Total Debt / Shareholders' Equity
Leverage	Interest Coverage	EBIT / Interest Expense
Efficiency	Asset Turnover	Revenue / Average Total Assets
Efficiency	Inventory Turnover	COGS / Average Inventory
Valuation	Price-to-Earnings (P/E)	Market Price / EPS
Valuation	Price-to-Book (P/B)	Market Price / Book Value per Share
Cash Flow	Operating Cash Flow Ratio	Operating Cash Flow / Current Liabilities

3.3.3 Validation & Quality Assurance
•	Automated balance checks: Assets = Liabilities + Equity
•	Cash flow reconciliation with balance sheet changes
•	Historical comparison for anomaly detection
•	Human-in-the-loop review queue for low-confidence extractions
•	Audit trail for all corrections and overrides
 
Phase 4: Intelligence Dashboard & Alerts (Weeks 13-16)
Build the presentation layer and alerting system.

3.4.1 Dashboard Components
Market Overview:
•	Real-time feed of incoming announcements and news
•	Sentiment heatmap across sectors and companies
•	Trending topics and emerging themes
•	Anomaly indicators for unusual activity

Company 360 View:
•	Profile: Basic info, sector, market cap, key personnel
•	News timeline: Chronological view of all related content
•	Sentiment trend: Historical sentiment over time
•	Financial snapshot: Key ratios with historical comparison
•	Relationship map: Visual graph of related entities
•	Risk indicators: Aggregated adverse signals

Adverse/Positive Event Views:
•	Filterable list of significant positive/negative events
•	Severity scoring based on sentiment intensity and materiality
•	Drill-down to source documents with highlighted excerpts

3.4.2 Configurable Alert Engine
Rule Type	Configuration Options
Keyword Triggers	Custom keyword lists, regex patterns, boolean combinations (AND/OR/NOT)
Sentiment Thresholds	Alert on sentiment below/above threshold, sentiment change velocity
Filing Type Filters	Subscribe to specific announcement types, exclude routine filings
Company Watchlists	Custom company groups, sector-based lists, portfolio tracking
Financial Triggers	Ratio thresholds, YoY changes exceeding percentage, red flag patterns
Delivery Channels	Email, SMS, in-app notifications, webhook integrations
 
Phase 5: GenAI Copilot with RAG (Weeks 17-20)
Implement the AI-powered research assistant with grounded answers.

3.5.1 RAG Architecture
Document Processing for RAG:
•	Chunk documents into semantic units (paragraphs, sections)
•	Generate embeddings using financial domain-tuned model
•	Store in vector database with metadata (source, date, company)
•	Implement hybrid search: dense retrieval + keyword matching

Query Processing Pipeline:
7.	Query Understanding: Parse user intent, extract entities
8.	Query Expansion: Generate related search terms
9.	Retrieval: Fetch top-k relevant chunks from vector store
10.	Re-ranking: Score chunks by relevance to specific query
11.	Context Assembly: Construct prompt with retrieved evidence
12.	Generation: LLM generates response with inline citations
13.	Validation: Verify citations match source content

3.5.2 Transparent Step Plan
Every Copilot response includes:
•	Step-by-step reasoning chain visible to user
•	Sources consulted with relevance scores
•	Evidence snippets supporting each claim
•	Confidence indicators for assertions
•	Expandable audit trail for compliance

3.5.3 Citation & Evidence System
Citation Format:
•	Inline citations: [Source: Document Name, Page/Section]
•	Click-through to highlighted source passage
•	Multi-source aggregation for synthesized answers
•	Citation validity scoring (direct quote vs. inference)

3.5.4 Correction Loop
•	User feedback mechanism: thumbs up/down, flag inaccuracy
•	Correction workflow: review queue, human validation
•	Learning integration: fine-tune retrieval based on feedback
•	Version tracking: maintain history of corrections
 
Phase 6: Security, Compliance & Deployment (Weeks 21-24)
Implement security controls, compliance features, and production deployment.

3.6.1 Role-Based Access Control (RBAC)
Role	Permissions
Analyst	View dashboard, search content, use Copilot, create personal alerts
Senior Analyst	All Analyst + export data, create shared alerts, view audit logs
Manager	All Senior Analyst + manage team alerts, access analytics reports
Administrator	All Manager + user management, system configuration, full audit access
Compliance	Read-only access to all data, full audit log access, export capabilities

3.6.2 Audit Logging
Logged Events:
•	User authentication: logins, logouts, failed attempts
•	Data access: searches, document views, exports
•	Copilot interactions: queries, responses, feedback
•	Alert activity: creation, modification, triggers
•	Administrative actions: user changes, configuration updates

Log Retention: Per AmBank guidelines (minimum 7 years for compliance-related)

3.6.3 Privacy & Data Retention
•	Data classification: Public, Internal, Confidential, Restricted
•	Encryption: At-rest (AES-256), in-transit (TLS 1.3)
•	PII handling: Minimal collection, pseudonymization where possible
•	Retention policies: Configurable per data type, automated purging
•	Right to erasure: Workflow for data deletion requests

3.6.4 Containerized Deployment
•	Docker images for all services with security scanning
•	Kubernetes deployment with resource limits and auto-scaling
•	Helm charts for environment-specific configuration
•	Service mesh (Istio) for inter-service communication
•	Secrets management via HashiCorp Vault
•	Blue-green deployment for zero-downtime updates
 
4. Project Timeline Summary
Phase	Focus Area	Duration
1	Foundation & Data Infrastructure	Weeks 1-4 (4 weeks)
2	NLP & Analytics Pipeline	Weeks 5-8 (4 weeks)
3	Financial Statement Processing	Weeks 9-12 (4 weeks)
4	Intelligence Dashboard & Alerts	Weeks 13-16 (4 weeks)
5	GenAI Copilot with RAG	Weeks 17-20 (4 weeks)
6	Security, Compliance & Deployment	Weeks 21-24 (4 weeks)

Total Duration: 24 weeks (approximately 6 months)

4.1 Key Milestones
Week	Milestone	Deliverable
4	Data pipeline operational	Demo: Live data ingestion
8	NLP engine deployed	Demo: Categorization & sentiment
12	Financial processing complete	Demo: PDF to ratios pipeline
16	Dashboard MVP ready	UAT: User acceptance testing
20	Copilot operational	Demo: RAG with citations
24	Production deployment	Go-live readiness review
 
5. Team Structure & Resource Requirements
Role	FTEs	Key Responsibilities
Project Manager	1	Overall delivery, stakeholder management, risk mitigation
Technical Architect	1	System design, technology decisions, integration patterns
Backend Engineers	3	API development, data pipelines, service integration
Frontend Engineers	2	Dashboard UI, user experience, real-time features
ML/NLP Engineers	2	NLP models, sentiment analysis, entity extraction
Data Engineer	1	Data infrastructure, ETL pipelines, storage optimization
DevOps Engineer	1	CI/CD, Kubernetes, monitoring, security
QA Engineer	1	Test automation, quality assurance, UAT support
Domain Expert (Part-time)	0.5	Financial domain guidance, validation rules, taxonomy

Total: 12.5 FTEs across the project lifecycle
 
6. Risk Management
Risk	Likelihood	Impact	Mitigation
OCR accuracy below target	Medium	High	Multi-engine fallback, human review queue, template optimization
Data source access changes	Medium	High	Modular connectors, fallback sources, relationship with providers
LLM hallucination in Copilot	High	High	Strict RAG grounding, citation validation, confidence thresholds
Scope creep	High	Medium	Clear MVP definition, change control process, backlog prioritization
Integration complexity	Medium	Medium	API-first design, contract testing, staged rollout
Performance at scale	Medium	High	Load testing early, auto-scaling, caching strategy
Security vulnerabilities	Low	Critical	Security-by-design, penetration testing, code scanning
 
7. Appendices
Appendix A: Data Schema (High-Level)
Core Entities:
•	Company: id, name, stock_code, sector, market_cap, listing_date, ...
•	Document: id, source, type, company_id, content, published_at, processed_at, ...
•	Sentiment: id, document_id, overall, confidence, rationale, aspects, ...
•	Entity: id, type, name, normalized_name, aliases, ...
•	Financial: id, company_id, period, statement_type, line_items, ratios, ...
•	Alert: id, user_id, rule_config, status, triggered_at, ...

Appendix B: API Endpoints (Sample)
•	GET /api/v1/companies - List companies with filtering
•	GET /api/v1/companies/{id}/360 - Full company profile
•	GET /api/v1/documents - Search documents
•	POST /api/v1/documents/upload - Upload PDF/CSV
•	GET /api/v1/alerts - User alerts
•	POST /api/v1/copilot/query - Submit question
•	GET /api/v1/copilot/sessions/{id} - Retrieve conversation

Appendix C: Integration Points
•	Bursa Malaysia: RSS feeds, filing downloads
•	News Sources: RSS, web scraping (with compliance)
•	Azure Document Intelligence: OCR API
•	Anthropic Claude API: LLM for Copilot
•	Email/SMS: Notification delivery
•	SSO/LDAP: Authentication integration

Appendix D: Acceptance Criteria Summary
Feature	Acceptance Criteria
Data Ingestion	Bursa announcements within 15 min, 95% coverage, deduplication active
Categorization	≥90% accuracy on standard announcement types
Sentiment Analysis	≥85% accuracy vs. human labels, rationale provided
Entity Extraction	≥90% precision, ≥85% recall on key entities
Financial OCR	≥95% field accuracy, all 12 ratios computed
Dashboard	All views functional, <2s load time, responsive design
Alerts	All rule types configurable, delivery within 5 min
Copilot	90% grounded responses, citations clickable, step plan visible
Security	RBAC enforced, audit logs complete, encryption verified


— End of Document —
