# Financial Intelligence Dashboard - Implementation Plan

## Executive Summary

Build a professional, institutional-grade financial intelligence dashboard for compliance officers with a distinctive **Bloomberg Terminal aesthetic** (dark theme, cyan accents, high information density). The dashboard integrates all backend AI systems (RAG agents, SQL agents, alerts) with mock data placeholders, creating a fully functional frontend ready for backend integration.

**Tech Stack:**
- Next.js 16.1 (App Router) + React 19
- shadcn/ui components (Radix primitives)
- Recharts for data visualization
- Zustand for state management
- Tailwind CSS v4 with custom design system
- Typography: JetBrains Mono + IBM Plex Sans (avoiding generic Inter/Roboto)

---

## Critical Files & Architecture

### Foundation Files (Create First)

1. **`src/app/globals.css`** - Design system foundation
   - Dark Bloomberg Terminal color palette (deep dark blue-black backgrounds, cyan accents)
   - CSS variables for all colors, spacing, shadows
   - Typography scale with extreme weight variations
   - Atmospheric backgrounds (grid patterns, gradients)

2. **`src/lib/types/api.ts`** - TypeScript interfaces
   - All API response types: Company, Filing, Alert, CopilotAnswer, FinancialRatio, IngestionJob
   - Ensures type safety across entire application

3. **`src/lib/mock-data/index.ts`** - Mock data factories
   - Generate realistic test data for all entities
   - Easy to swap with real API calls later

4. **`src/components/layout/app-shell.tsx`** - Main layout
   - Persistent sidebar (280px, left)
   - Top header bar (60px)
   - Main content area (flex-1)
   - Dashboard shell for all pages

5. **`src/components/copilot/chat-window.tsx`** - Copilot interface
   - Full chat UI with message bubbles, citations, suggested questions
   - Central AI integration feature

---

## Design System Specifications

### Color Palette (Dark Bloomberg Terminal)

```css
/* globals.css CSS Variables */
:root {
  /* Base - Deep dark backgrounds */
  --color-bg-primary: #0a0e14;
  --color-bg-secondary: #0f1419;
  --color-bg-tertiary: #151a20;
  --color-bg-elevated: #1a1f26;

  /* Text - Off-white with muted grays */
  --color-text-primary: #e6edf3;
  --color-text-secondary: #8b949e;
  --color-text-tertiary: #6e7681;
  --color-text-accent: #00d9ff;

  /* Accent - Cyan/Blue theme */
  --color-accent-primary: #00d9ff;    /* Bright cyan */
  --color-accent-secondary: #0091ff;  /* Electric blue */
  --color-accent-tertiary: #005c99;   /* Dark blue */

  /* Semantic colors */
  --color-success: #00ff88;
  --color-warning: #ffaa00;
  --color-error: #ff4444;
  --color-info: #00aaff;

  /* Alert severity */
  --color-alert-high: #ff4444;
  --color-alert-medium: #ffaa00;
  --color-alert-low: #00aaff;

  /* Borders with subtle glow */
  --color-border-primary: #21262d;
  --color-border-secondary: #2d333b;
  --color-border-accent: #00d9ff;

  /* Chart colors */
  --color-chart-1: #00d9ff;
  --color-chart-2: #00ff88;
  --color-chart-3: #ffaa00;
  --color-chart-4: #ff44aa;
  --color-chart-5: #aa44ff;
}
```

### Typography (Distinctive, Non-Generic)

**Fonts:**
- **JetBrains Mono** - Monospace for data, metrics, code (avoid generic monospace)
- **IBM Plex Sans** - Sans-serif for UI text (avoid Inter, Roboto)

**Load in `src/app/layout.tsx`:**
```typescript
import { JetBrains_Mono, IBM_Plex_Sans } from 'next/font/google'

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  weight: ['400', '500', '700'],
})

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ['latin'],
  variable: '--font-sans',
  weight: ['300', '400', '500', '600', '700'],
})
```

**Type Scale:**
- Extreme weight contrasts (300 vs 700, not 400 vs 600)
- Large size jumps (3x+ for headings)
- Monospace for all numeric data

### Atmospheric Backgrounds

**Dashboard Grid Pattern:**
```css
.dashboard-bg {
  background:
    linear-gradient(90deg, rgba(0, 217, 255, 0.02) 1px, transparent 1px),
    linear-gradient(rgba(0, 217, 255, 0.02) 1px, transparent 1px),
    linear-gradient(180deg, #0a0e14 0%, #0f1419 100%);
  background-size: 50px 50px, 50px 50px, 100% 100%;
}
```

**Card Backgrounds:**
```css
.card-bg {
  background: linear-gradient(135deg, #151a20 0%, #0f1419 100%);
  border: 1px solid rgba(0, 217, 255, 0.1);
  box-shadow: 0 0 0 1px rgba(0, 217, 255, 0.05);
}

.card-bg:hover {
  border-color: var(--color-border-accent);
  box-shadow: 0 0 20px rgba(0, 217, 255, 0.1);
}
```

---

## Page Structure & Routes

### App Router Pages (`src/app/`)

```
app/
├── layout.tsx                    # Root layout (fonts, theme, providers)
├── page.tsx                      # Home (redirect to /dashboard)
├── globals.css                   # Design system
│
├── dashboard/
│   ├── layout.tsx                # Dashboard shell with AppShell
│   └── page.tsx                  # Overview (metrics, recent alerts, filings)
│
├── companies/
│   ├── page.tsx                  # Company list (searchable table)
│   └── [code]/
│       ├── page.tsx              # Company 360 view (tabs: Overview, Filings, Financials, Alerts)
│       ├── filings/page.tsx      # Company-specific filing timeline
│       ├── financials/page.tsx   # Financial ratios & charts
│       └── alerts/page.tsx       # Company-specific alerts
│
├── filings/
│   ├── page.tsx                  # All filings timeline (global, filterable)
│   └── [id]/page.tsx             # Filing detail (full content, tables, PDF)
│
├── alerts/
│   ├── page.tsx                  # Alert dashboard (grouped by severity)
│   └── [id]/page.tsx             # Alert detail (evidence, timeline)
│
├── copilot/
│   └── page.tsx                  # Full-screen chat interface
│
├── sql/
│   └── page.tsx                  # Natural language SQL interface
│
├── ingest/
│   ├── page.tsx                  # Ingestion dashboard (job status)
│   ├── bursa/page.tsx            # Bursa scraping interface (progress visualization)
│   └── upload/page.tsx           # Manual file upload (drag-drop)
│
└── settings/
    └── page.tsx                  # User preferences, alert config
```

### Navigation Structure (Sidebar)

```
Dashboard
├── Overview
├── Companies
├── Filings
├── Alerts
├── Copilot
└── SQL Query

Ingestion
├── Status
├── Bursa Scraper
└── Upload Files

System
├── Settings
└── Health Status
```

---

## Component Architecture

### Layout Components (`src/components/layout/`)

1. **`app-shell.tsx`** - Main application layout
   - Sidebar (280px, persistent)
   - Header bar (60px, breadcrumbs, search, user profile)
   - Main content area
   - Optional right panel (contextual actions)

2. **`sidebar.tsx`** - Navigation sidebar
   - Logo/branding area
   - Navigation links with icons (lucide-react)
   - Active route indicator (cyan accent border)
   - Collapsible sections
   - System health indicator (bottom)

3. **`header.tsx`** - Top header bar
   - Breadcrumb navigation
   - Global search bar
   - Real-time alert badge counter
   - User profile dropdown
   - Theme toggle

4. **`breadcrumbs.tsx`** - Dynamic breadcrumb trail

### Data Display Components (`src/components/data-display/`)

5. **`metric-card.tsx`** - KPI cards
   - Label, value, trend indicator
   - Icon support
   - Variant styling (default, success, warning, error)

6. **`data-table.tsx`** - Enhanced table
   - Sortable columns
   - Filterable
   - Pagination
   - Row actions dropdown

7. **`timeline-card.tsx`** - Event/filing timeline entries
   - Date, title, company
   - Quick preview
   - Action buttons

8. **`alert-card.tsx`** - Alert display
   - Severity badge (high=red, medium=orange, low=blue)
   - Reason, evidence count
   - Quick actions (view, dismiss)

9. **`company-card.tsx`** - Company overview card
   - Name, ticker, sector
   - Key metrics (filings count, alerts, health score)

10. **`chart-card.tsx`** - Wrapper for charts
    - Consistent styling
    - Title, period selector
    - Export button

11. **`pdf-viewer.tsx`** - Inline PDF preview
    - Page navigation
    - Zoom controls
    - Download button
    - Highlight cited sections

### Copilot Components (`src/components/copilot/`)

12. **`chat-window.tsx`** - Main chat interface
    - Message list (auto-scroll)
    - Input area (bottom)
    - Suggested questions chips
    - Context filters (company, date)

13. **`message-bubble.tsx`** - Chat messages
    - User: right-aligned, cyan accent
    - Assistant: left-aligned, card background
    - Timestamp, copy button

14. **`citation-block.tsx`** - Evidence citations
    - Collapsible citation list
    - Source name, excerpt, link
    - Page number for PDFs
    - Click to open source

15. **`chat-input.tsx`** - Message input
    - Auto-expanding textarea
    - Send button (Enter to submit)
    - Attachment button
    - Character count

16. **`suggested-questions.tsx`** - Quick question chips
    - Context-aware suggestions
    - Click to populate input

### Upload Components (`src/components/upload/`)

17. **`file-upload.tsx`** - Drag-drop upload
    - Visual feedback on drag-over
    - File type validation (PDF, CSV)
    - Multiple file support
    - Preview before upload

18. **`upload-progress.tsx`** - Upload status
    - Progress bars per file
    - Cancel button
    - Error states

19. **`file-preview.tsx`** - Uploaded file cards
    - File icon, name, size
    - Remove button
    - Download link

### Filter Components (`src/components/filters/`)

20. **`filter-panel.tsx`** - Multi-criteria filtering
    - Company selector
    - Date range picker
    - Category/type filters
    - Severity filters (for alerts)
    - Apply/reset buttons

21. **`date-range-picker.tsx`** - Date selection
    - Calendar popover (shadcn calendar)
    - Quick presets (Today, Last 7 days, Last 30 days, Custom)
    - Validation

22. **`company-selector.tsx`** - Searchable company dropdown
    - Autocomplete
    - Recent companies
    - Favorites

### Visualization Components (`src/components/visualizations/`)

23. **`sentiment-chart.tsx`** - Sentiment trend line
    - Recharts LineChart
    - Color gradient (red → yellow → green)
    - Event annotations
    - Custom tooltips

24. **`financial-chart.tsx`** - Financial metrics charts
    - Bar/line charts for ratios
    - Multi-series support
    - Period comparison

25. **`alert-timeline.tsx`** - Alert timeline visualization
    - Recharts timeline
    - Severity-coded markers

### Notification Components (`src/components/notifications/`)

26. **`alert-notification.tsx`** - Real-time alert popup
    - Toast notifications (sonner)
    - Severity styling
    - Quick actions (view, dismiss)
    - Sound/vibration option

27. **`scraping-progress.tsx`** - Scraping visualization
    - Progress bar (0-100%)
    - Phase indicator
    - Document count
    - Log stream (last 10 events)
    - Video recording indicator

---

## TypeScript Type System

### API Response Types (`src/lib/types/api.ts`)

```typescript
export interface Company {
  company_code: string
  company_name: string
  ticker: string
  sector: string
  market_cap?: number
  filings_count: number
  latest_filing_date?: string
  alert_count: number
  financial_health_score?: number
}

export interface Filing {
  filing_id: string
  company_code: string
  company_name: string
  announcement_date: string
  document_type: string
  title: string
  summary?: string
  pdf_urls: string[]
  sentiment?: 'positive' | 'neutral' | 'negative'
  tables_count: number
  keywords: string[]
}

export interface Alert {
  alert_id: string
  company_code: string
  company_name: string
  severity: 'high' | 'medium' | 'low'
  alert_type: string
  triggered_at: string
  reason: string
  evidence: Citation[]
  status: 'active' | 'reviewed' | 'dismissed'
}

export interface Citation {
  source: string
  link: string
  page?: number
  excerpt: string
}

export interface CopilotAnswer {
  answer_text: string
  citations: Citation[]
  tables?: any[]
  alerts?: Alert[]
  confidence: number
  source_agents: string[] // ["rag", "sql", "financial"]
}

export interface FinancialRatio {
  ratio_name: string
  ratio_value: number
  period: string
  change_percent?: number
  trend: 'up' | 'down' | 'stable'
}

export interface IngestionJob {
  job_id: string
  type: 'bursa' | 'news' | 'manual'
  status: 'queued' | 'running' | 'completed' | 'failed'
  progress: number
  total_documents: number
  processed_documents: number
  started_at: string
  completed_at?: string
  video_url?: string
}
```

---

## Mock Data Strategy

### Mock Data Factories (`src/lib/mock-data/`)

Create realistic test data for all entities:

```
lib/mock-data/
├── companies.ts          # 50+ mock companies (MAYBANK, GLICO, etc.)
├── filings.ts            # 200+ mock filings
├── alerts.ts             # 50+ mock alerts
├── copilot.ts            # Mock copilot responses by query type
├── financials.ts         # Mock financial ratios
├── ingestion.ts          # Mock scraping jobs
└── index.ts              # Export all mocks
```

**Example Mock Factory (`companies.ts`):**

```typescript
export const mockCompanies: Company[] = [
  {
    company_code: '1155',
    company_name: 'Malayan Banking Berhad',
    ticker: 'MAYBANK',
    sector: 'Financial Services',
    market_cap: 95000000000,
    filings_count: 124,
    latest_filing_date: '2025-01-10',
    alert_count: 3,
    financial_health_score: 78,
  },
  // ... 50+ more companies
]
```

### API Client Layer (`src/lib/api/`)

All API calls go through this layer (easy to swap mock → real):

```typescript
// lib/api/companies.ts
import { Company } from '@/lib/types/api'
import { mockCompanies } from '@/lib/mock-data/companies'

export async function getCompanies(): Promise<Company[]> {
  // Simulate network delay
  await new Promise((r) => setTimeout(r, 500))

  // TODO: Replace with actual API call
  // const response = await fetch('/api/companies')
  // return response.json()

  return mockCompanies
}

export async function getCompany(code: string): Promise<Company> {
  await new Promise((r) => setTimeout(r, 300))

  // TODO: const response = await fetch(`/api/companies/${code}`)
  const company = mockCompanies.find(c => c.company_code === code)
  if (!company) throw new Error('Company not found')

  return company
}
```

**Create similar files for:**
- `lib/api/filings.ts`
- `lib/api/alerts.ts`
- `lib/api/copilot.ts`
- `lib/api/sql.ts`
- `lib/api/ingestion.ts`
- `lib/api/upload.ts`

---

## State Management (Zustand)

### Global Stores (`src/stores/`)

1. **`use-app-store.ts`** - Global app state
```typescript
interface AppStore {
  sidebarCollapsed: boolean
  theme: 'dark' | 'light'
  toggleSidebar: () => void
  setTheme: (theme: 'dark' | 'light') => void
}
```

2. **`use-copilot-store.ts`** - Chat history
```typescript
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  copilotAnswer?: CopilotAnswer
  timestamp: string
}

interface CopilotStore {
  messages: Message[]
  isLoading: boolean
  addMessage: (message: Message) => void
  clearMessages: () => void
}
```

3. **`use-filter-store.ts`** - Filter state across pages
```typescript
interface FilterStore {
  companyCode?: string
  dateRange?: { start: Date; end: Date }
  documentType?: string
  severity?: string
  setCompanyCode: (code?: string) => void
  setDateRange: (range?: { start: Date; end: Date }) => void
  resetFilters: () => void
}
```

4. **`use-alert-store.ts`** - Real-time alerts
```typescript
interface AlertStore {
  alerts: Alert[]
  unreadCount: number
  addAlert: (alert: Alert) => void
  markAsRead: (alertId: string) => void
  dismissAlert: (alertId: string) => void
}
```

5. **`use-ingestion-store.ts`** - Ingestion job tracking
```typescript
interface IngestionStore {
  jobs: IngestionJob[]
  activeJobId?: string
  addJob: (job: IngestionJob) => void
  updateJobProgress: (jobId: string, progress: number) => void
}
```

---

## Dependencies Installation

### 1. Initial Setup

```bash
# shadcn/ui setup (interactive)
cd C:\Users\limfo\Desktop\AI\HackLab2.0_Ambank\frontend
pnpm dlx shadcn@latest init
# Choose: Default style, Slate base color, CSS variables: Yes
```

### 2. Core Dependencies

```bash
# Charts
pnpm add recharts

# State Management
pnpm add zustand

# Forms
pnpm add react-hook-form @hookform/resolvers zod

# Date Handling
pnpm add date-fns

# Icons
pnpm add lucide-react

# PDF Handling
pnpm add react-pdf pdfjs-dist

# File Upload
pnpm add react-dropzone

# Syntax Highlighting (SQL)
pnpm add react-syntax-highlighter
pnpm add -D @types/react-syntax-highlighter

# Toast Notifications
pnpm add sonner

# Utilities
pnpm add clsx tailwind-merge
```

### 3. shadcn/ui Components

```bash
# Install all required components
pnpm dlx shadcn@latest add button card input label select dialog dropdown-menu popover badge separator tabs table toast avatar skeleton scroll-area command calendar checkbox switch textarea tooltip alert progress
```

---

## Implementation Sequence (10-Day Plan)

### Phase 1: Foundation (Days 1-2)

**Day 1: Setup & Design System**
- [x] Install all dependencies (shadcn, Recharts, Zustand, etc.)
- [x] Configure Tailwind with custom color palette in `tailwind.config.ts`
- [x] Set up fonts (JetBrains Mono, IBM Plex Sans) in `layout.tsx`
- [x] Create CSS variables in `globals.css` (colors, typography, shadows)
- [x] Add atmospheric backgrounds (grid pattern, gradients)
- [ ] Set up theme provider (dark mode default)

**Day 2: Type System & Mock Data**
- [x] Create all TypeScript interfaces in `lib/types/api.ts`
- [x] Build mock data factories in `lib/mock-data/`
  - [x] `companies.ts` (50+ companies)
  - [x] `filings.ts` (200+ filings)
  - [x] `alerts.ts` (50+ alerts)
  - [x] `copilot.ts` (mock responses)
  - [x] `financials.ts` (ratios)
  - [x] `ingestion.ts` (jobs)
- [x] Create API client layer in `lib/api/` (all return mock data)
  - [x] `companies.ts` - Company data API
  - [x] `filings.ts` - Filings data API
  - [x] `alerts.ts` - Alerts management API
  - [x] `copilot.ts` - Copilot chat API
  - [x] `financials.ts` - Financial ratios API
  - [x] `ingestion.ts` - Ingestion jobs API
  - [x] `sql.ts` - Natural language SQL API

### Phase 2: Core Layout (Day 3)

**Day 3: App Shell & Navigation**
- [x] Build `components/layout/app-shell.tsx`
  - [x] Sidebar container (280px)
  - [x] Header bar (60px)
  - [x] Main content area
- [x] Build `components/layout/sidebar.tsx`
  - [x] Logo/branding
  - [x] Navigation links with icons
  - [x] Active route indicator (cyan accent)
  - [x] System health indicator
- [x] Build `components/layout/header.tsx`
  - [x] Breadcrumbs
  - [x] Global search bar
  - [x] Alert badge counter
  - [x] User profile dropdown
- [x] Create Zustand stores (`use-app-store.ts`, `use-filter-store.ts`, `use-copilot-store.ts`, `use-alert-store.ts`, `use-ingestion-store.ts`)
- [x] Update `app/dashboard/layout.tsx` to use AppShell

### Phase 3: Dashboard Pages (Days 4-5)

**Day 4: Dashboard Overview & Company Pages**
- [x] Create `app/dashboard/page.tsx`
  - [x] Build `components/data-display/metric-card.tsx` (4-6 KPI cards)
  - [x] Build `components/data-display/timeline-card.tsx` (recent filings)
  - [x] Build `components/data-display/alert-card.tsx` (recent alerts)
  - [x] Add quick actions (trigger ingestion, open copilot)
- [x] Create `app/companies/page.tsx`
  - [x] Build `components/data-display/data-table.tsx` (sortable, filterable)
  - [x] Build `components/data-display/company-card.tsx`
  - [x] Add search bar
- [x] Create `app/companies/[code]/page.tsx` (Company 360)
  - [x] Company header with quick actions
  - [x] Company overview with metrics display
  - [x] Recent filings and alerts sections

**Day 5: Filings & Alerts Pages**
- [x] Create `app/filings/page.tsx`
  - [x] Timeline view (chronological)
  - [x] Integrated filter panel (sentiment, document type, company, search)
  - [x] Sentiment badges
- [ ] Create `app/filings/[id]/page.tsx`
  - [ ] Filing detail layout
  - [ ] Build `components/data-display/pdf-viewer.tsx`
  - [ ] Table display
  - [ ] Related filings
- [x] Create `app/alerts/page.tsx`
  - [x] Alert summary bar (counts by severity)
  - [x] Alert cards with integrated filters
  - [x] Severity-based sorting and filtering
- [ ] Create `app/alerts/[id]/page.tsx`
  - [ ] Alert detail with evidence
  - [ ] Timeline of events
  - [ ] Related filings

### Phase 4: AI Integration (Days 6-7)

**Day 6: Copilot Chat**
- [x] Create `app/copilot/page.tsx`
- [x] Build `components/copilot/chat-window.tsx`
  - [x] Message list container (auto-scroll)
  - [x] Input area at bottom
  - [x] Empty state with suggested questions
- [x] Build `components/copilot/message-bubble.tsx`
  - [x] User messages (right, cyan)
  - [x] Assistant messages (left, card background)
  - [x] Timestamp, copy button
  - [x] Confidence indicators and source agent badges
- [x] Build `components/copilot/citation-block.tsx`
  - [x] Collapsible citation list
  - [x] Source name, excerpt, link
  - [x] Page number for PDFs
- [x] Build `components/copilot/chat-input.tsx`
  - [x] Auto-expanding textarea
  - [x] Send button (Enter to submit)
  - [x] Character count and validation
- [x] Build `components/copilot/suggested-questions.tsx`
  - [x] Question chips (context-aware)
- [x] Integration with `stores/use-copilot-store.ts` (already exists)
- [x] Integration with `lib/api/copilot.ts` (already exists)

**Day 7: File Upload & Alerts**
- [x] Create `app/ingest/upload/page.tsx`
- [x] Build `components/upload/file-upload.tsx`
  - [x] Drag-drop zone
  - [x] File type validation
  - [x] Multiple file support
  - [x] Error handling
- [x] Build `components/upload/upload-progress.tsx`
  - [x] Progress bars per file
  - [x] Cancel button
  - [x] Status indicators (pending, uploading, completed, error)
- [x] Build `components/notifications/alert-notification.tsx`
  - [x] Toast notifications (sonner)
  - [x] Severity styling
  - [x] Quick actions (view, dismiss)
- [x] Build `components/notifications/alert-simulator.tsx`
  - [x] Real-time alert simulation
  - [x] Periodic alert generation
- [x] Build `components/notifications/alert-notification-provider.tsx`
  - [x] Provider wrapper for notifications
  - [x] Integration with alert store
- [x] Integration with `stores/use-alert-store.ts` (already exists)
- [x] Add real-time alert simulation (useEffect with interval)
- [x] Integrate Toaster into root layout
- [x] Update header component to show real-time unread count

### Phase 5: Data Visualization (Days 8-9)

**Day 8: Financial Charts**
- [x] Create `app/companies/[code]/financials/page.tsx`
- [x] Build `components/data-display/chart-card.tsx`
  - [x] Title, period selector
  - [x] Export button
- [x] Build `components/visualizations/financial-chart.tsx`
  - [x] Recharts LineChart for ratio trends
  - [x] Color coding (success, warning, error)
  - [x] Custom tooltips
- [x] Add ratio cards with trend indicators
- [x] Add financial statement tables

**Day 9: Sentiment & SQL Interface**
- [x] Build `components/visualizations/sentiment-chart.tsx`
  - [x] Recharts LineChart
  - [x] Color gradient (red → yellow → green)
  - [x] Event annotations
- [x] Create `app/sql/page.tsx`
- [x] Natural language input (textarea)
- [x] SQL display (read-only, syntax highlighting with react-syntax-highlighter)
- [x] Result table (use `data-table.tsx`)
- [x] Export CSV button
- [x] Query history list

### Phase 6: Ingestion & Polish (Day 10)

**Day 10: Scraping Progress & Final Polish**
- [x] Create `app/ingest/page.tsx` (job status dashboard)
- [x] Create `app/ingest/bursa/page.tsx`
- [x] Build `components/notifications/scraping-progress.tsx`
  - [x] Progress bar (0-100%)
  - [x] Phase indicator
  - [x] Document count
  - [x] Log stream (last 10 events)
  - [x] Video recording indicator
- [x] Create `app/settings/page.tsx` (user preferences)
- [x] Add loading skeletons to all pages (shadcn skeleton)
- [ ] Add empty states (when no data)
- [ ] Add error states (when API fails)
- [ ] Test responsive design (tablet, mobile)
- [ ] Add hover states with glow effects
- [ ] Add staggered animations for list items
- [ ] Performance check (code splitting, image optimization)
- [ ] Accessibility check (keyboard navigation, ARIA labels)

---

## Key Features Implementation Details

### 1. Company 360 Dashboard

**Page:** `app/companies/[code]/page.tsx`

**Layout:**
- Company header (name, ticker, sector, quick actions)
- 3-column metric grid (Market Cap, Filings Count, Alert Count)
- Financial health score gauge (circular progress, Recharts RadialBarChart)
- Tabs: Overview, Filings, Financials, Alerts
- Overview tab: Recent activity timeline (last 20 events)

**Components Used:**
- `metric-card.tsx` × 3
- `chart-card.tsx` (financial health gauge)
- shadcn `tabs`
- `timeline-card.tsx`

### 2. Copilot Chat Interface

**Page:** `app/copilot/page.tsx`

**Layout:**
- Full-height chat container
- Suggested questions at top (when empty)
- Message list (scrollable, auto-scroll to bottom)
- Input area at bottom (sticky)
- Context filters in header (company, date range)

**Mock Response Logic:**
```typescript
// lib/api/copilot.ts
export async function sendCopilotMessage(query: string): Promise<CopilotAnswer> {
  await new Promise((r) => setTimeout(r, 1500)) // Simulate thinking

  if (query.toLowerCase().includes('dividend')) {
    return mockCopilotAnswers.dividend
  } else if (query.toLowerCase().includes('risk')) {
    return mockCopilotAnswers.risk
  } else if (query.toLowerCase().includes('financial')) {
    return mockCopilotAnswers.financial
  } else {
    return mockCopilotAnswers.default
  }
}
```

**Citation Display:**
- Collapsible section below answer
- Each citation as a card with source, excerpt, link
- Click to open source in modal (filing detail page)

### 3. Alert Management

**Page:** `app/alerts/page.tsx`

**Layout:**
- Summary bar (High: 3, Medium: 12, Low: 5, Reviewed: 42)
- Filter panel (severity, type, status, company)
- Alert cards grouped by severity
- Bulk actions (mark as reviewed, dismiss)

**Alert Card Design:**
- Severity badge (red/orange/blue)
- Company name, alert type
- Reason (1-2 sentences)
- Evidence count
- Actions: View Details, Dismiss, Ask Copilot

**Real-time Updates:**
- Simulate new alerts with `setInterval` (every 30s, random chance)
- Show toast notification
- Update badge counter in header
- Add to top of alert list

### 4. Bursa Scraping Progress

**Page:** `app/ingest/bursa/page.tsx`

**Layout:**
- Configuration form (year, company filter, max announcements)
- Start button (triggers mock job)
- Progress visualization (when running)
- Video recording preview (mock thumbnail)
- Completed job summary (documents scraped, tables extracted)

**Progress Component:**
- Progress bar (0-100%)
- Current phase text ("Crawling listings", "Extracting tables", "Finalizing video")
- Document count (X / Y processed)
- Real-time log stream (last 10 events, scrollable)
- Cancel button (future)

**Mock Progress Simulation:**
```typescript
// hooks/use-scraping-progress.ts
const interval = setInterval(() => {
  setProgress((p) => Math.min(p + 5, 100))
  if (progress < 30) setPhase('Crawling announcement listings')
  else if (progress < 60) setPhase('Extracting table data')
  else if (progress < 90) setPhase('Downloading PDFs')
  else setPhase('Finalizing video recording')
}, 1000)
```

### 5. Financial Metrics Display

**Page:** `app/companies/[code]/financials/page.tsx`

**Layout:**
- Period selector (Q1 2024, Q2 2024, ..., dropdown)
- 3 ratio cards: Liquidity, Profitability, Leverage
  - Current value
  - Change from previous period (%, trend arrow)
- Ratio trend charts (Recharts line charts, 8 quarters)
- Financial statement tables (tabs: Income Statement, Balance Sheet, Cash Flow)

**Ratio Card:**
```typescript
<MetricCard
  label="Return on Equity"
  value="15.2%"
  trend={{ direction: 'down', percentage: -8 }}
  variant="warning"
/>
```

**Chart Colors:**
- ROE: `var(--color-chart-1)` (cyan)
- ROA: `var(--color-chart-2)` (green)
- Net Margin: `var(--color-chart-3)` (orange)

---

## Distinctive Design Elements (Avoid AI Slop)

### Typography Execution

**Headings:**
```css
h1 {
  font-family: var(--font-sans);
  font-size: 2.25rem; /* 36px */
  font-weight: 700;
  letter-spacing: -0.02em;
}
```

**Data/Metrics:**
```css
.metric-value {
  font-family: var(--font-mono);
  font-size: 1.875rem; /* 30px */
  font-weight: 700;
  color: var(--color-accent-primary);
}
```

**Body Text:**
```css
body {
  font-family: var(--font-sans);
  font-size: 1rem; /* 16px */
  font-weight: 400;
  line-height: 1.6;
}
```

### Hover Effects

**Card Hover:**
```css
.card {
  transition: all 0.2s ease;
  border: 1px solid var(--color-border-primary);
}

.card:hover {
  border-color: var(--color-border-accent);
  box-shadow: 0 0 20px rgba(0, 217, 255, 0.15);
  transform: translateY(-2px);
}
```

**Button Hover:**
```css
.btn-primary {
  background: var(--color-accent-primary);
  color: #0a0e14;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background: var(--color-accent-secondary);
  box-shadow: 0 0 30px rgba(0, 217, 255, 0.4);
}
```

### Animations

**Staggered List Items:**
```css
.timeline-card {
  animation: slide-up 0.3s ease;
  animation-fill-mode: both;
}

.timeline-card:nth-child(1) { animation-delay: 0.05s; }
.timeline-card:nth-child(2) { animation-delay: 0.1s; }
.timeline-card:nth-child(3) { animation-delay: 0.15s; }

@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

**Shimmer Loading:**
```css
@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

.skeleton {
  background: linear-gradient(
    90deg,
    #151a20 0px,
    #1a1f26 40px,
    #151a20 80px
  );
  background-size: 1000px 100%;
  animation: shimmer 2s infinite;
}
```

---

## Testing & Validation

### Manual Testing Checklist

**Visual Design:**
- [ ] Dark theme applied throughout (no white backgrounds)
- [ ] Cyan accents used for interactive elements
- [ ] JetBrains Mono used for all numeric data
- [ ] IBM Plex Sans used for UI text
- [ ] Grid pattern visible on dashboard background
- [ ] Card hover effects working (glow, border color change)
- [ ] No generic AI aesthetics (purple gradients, Inter font, predictable layouts)

**Navigation:**
- [ ] Sidebar navigation functional (all links work)
- [ ] Active route highlighted with cyan accent
- [ ] Breadcrumbs update correctly
- [ ] Header search bar present (can be non-functional for now)
- [ ] Alert badge shows count

**Pages:**
- [ ] Dashboard overview displays metrics, recent alerts, recent filings
- [ ] Company list searchable and filterable
- [ ] Company 360 view shows all tabs (Overview, Filings, Financials, Alerts)
- [ ] Filings timeline displays mock filings
- [ ] Alert dashboard groups alerts by severity
- [ ] Copilot chat accepts input and displays mock responses with citations
- [ ] SQL interface shows generated SQL and mock results
- [ ] Bursa scraping page shows progress visualization
- [ ] File upload page has drag-drop zone

**Data Display:**
- [ ] All tables sortable (click column headers)
- [ ] Charts render correctly (Recharts)
- [ ] PDF viewer displays (or shows placeholder)
- [ ] Citations expandable and clickable

**Interactions:**
- [ ] Buttons have hover states
- [ ] Forms validate input
- [ ] Filters apply correctly
- [ ] Date range picker works
- [ ] Company selector autocompletes

**Responsive Design:**
- [ ] Sidebar collapses on mobile
- [ ] Tables scroll horizontally on mobile
- [ ] Charts resize responsively

---

## Environment Setup

### Create `.env.local`

```bash
# API Configuration (for future backend integration)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Feature Flags
NEXT_PUBLIC_ENABLE_REAL_TIME_ALERTS=false
NEXT_PUBLIC_ENABLE_PDF_GENERATION=false

# Mock Data (set to true for now)
NEXT_PUBLIC_USE_MOCK_DATA=true
```

---

## Critical Files Summary

**Priority 1 (Foundation):**
1. `src/app/globals.css` - Design system (CSS variables, colors, typography, backgrounds)
2. `src/lib/types/api.ts` - TypeScript interfaces for all data
3. `src/lib/mock-data/index.ts` - Mock data factories

**Priority 2 (Layout):**
4. `src/components/layout/app-shell.tsx` - Main application shell
5. `src/components/layout/sidebar.tsx` - Navigation sidebar
6. `src/components/layout/header.tsx` - Top header bar

**Priority 3 (Core Components):**
7. `src/components/data-display/metric-card.tsx` - KPI cards
8. `src/components/data-display/data-table.tsx` - Sortable tables
9. `src/components/data-display/alert-card.tsx` - Alert display

**Priority 4 (AI Integration):**
10. `src/components/copilot/chat-window.tsx` - Copilot chat interface
11. `src/components/copilot/citation-block.tsx` - Evidence citations
12. `src/components/upload/file-upload.tsx` - File upload

**Priority 5 (Visualization):**
13. `src/components/visualizations/sentiment-chart.tsx` - Sentiment trends
14. `src/components/visualizations/financial-chart.tsx` - Financial charts
15. `src/components/notifications/scraping-progress.tsx` - Scraping progress

---

## Success Criteria

### Visual Excellence
✅ Bloomberg Terminal aesthetic (dark theme, cyan accents, high information density)
✅ No generic fonts (Inter, Roboto avoided)
✅ Distinctive typography (JetBrains Mono + IBM Plex Sans)
✅ Atmospheric backgrounds (grid patterns, gradients)
✅ Smooth animations (hover effects, transitions, staggered reveals)

### Functional Completeness
✅ All 16 pages implemented with mock data
✅ AI integration placeholders (copilot chat, file upload, PDF preview, alerts)
✅ Data visualization (sentiment charts, financial charts, alert timeline)
✅ Filtering and search across all data views
✅ Real-time update simulation (alerts, scraping progress)

### Code Quality
✅ Type-safe (TypeScript interfaces for all data)
✅ Modular (reusable components)
✅ Maintainable (clear file structure, separation of concerns)
✅ Scalable (easy to swap mock data with real API)

### User Experience
✅ Intuitive navigation (persistent sidebar, breadcrumbs)
✅ Fast interactions (optimistic updates, loading skeletons)
✅ Clear feedback (toast notifications, progress indicators)
✅ Accessible (keyboard navigation, ARIA labels)

---

## Next Steps After Implementation

### Backend Integration
1. Replace mock API calls with real fetch to backend endpoints
2. Add authentication (JWT tokens, protected routes)
3. Implement WebSocket connections for real-time updates
4. Integrate video playback for scraping recordings
5. Enable PDF generation API

### Production Deployment
1. Build optimized production bundle (`pnpm build`)
2. Configure environment variables for production
3. Deploy to Vercel/AWS/Docker
4. Set up monitoring (Sentry, LogRocket)
5. Configure CDN for static assets

---

## File Locations Reference

**Frontend Root:** `C:\Users\limfo\Desktop\AI\HackLab2.0_Ambank\frontend\`

**Key Directories:**
- Pages: `src/app/`
- Components: `src/components/`
- Types: `src/lib/types/`
- Mock Data: `src/lib/mock-data/`
- API Layer: `src/lib/api/`
- Stores: `src/stores/`
- Styles: `src/app/globals.css`

**Configuration:**
- Tailwind: `tailwind.config.ts`
- TypeScript: `tsconfig.json`
- Next.js: `next.config.ts`
- shadcn: `components.json`

---

This plan provides a comprehensive roadmap to build a professional, institutional-grade financial intelligence dashboard with distinctive Bloomberg Terminal aesthetics, full AI integration placeholders, and mock data for all features. The implementation is structured for rapid development while maintaining code quality and design excellence.

---

## Phase 7: UI/UX Overhaul - Professional Analytics Polish

### Problem Analysis

The current UI has critical issues that make it look unprofessional:

1. **Oversized Typography** - Font sizes are too large everywhere (4xl headers, 4xl metric values)
2. **Missing Padding** - Text sticks to borders, elements feel cramped
3. **No Visual Hierarchy** - Labels, values, and titles all use similar colors/weights
4. **Color Monotony** - Everything is white-ish, no differentiation between labels and values
5. **Bloated Cards** - Excessive padding (p-8) makes everything feel spacious instead of dense
6. **Poor Information Density** - Bloomberg terminal aesthetic requires dense, scannable data

### Design Principles for Overhaul

**1. Typography Hierarchy (Most Important)**
```
Page Title:     text-2xl (24px) font-semibold - Primary color
Section Title:  text-lg (18px) font-semibold - Primary color
Card Title:     text-base (16px) font-medium - Primary color
Label:          text-xs (12px) font-medium uppercase tracking-wider - Tertiary color (MUTED)
Metric Value:   text-2xl (24px) font-bold mono - Primary or Accent color
Body Text:      text-sm (14px) font-normal - Secondary color
Meta/Timestamp: text-xs (12px) font-mono - Tertiary color
```

**2. Spacing System (Compact but Breathable)**
```
Card Padding:   p-4 (16px) or p-5 (20px) - NOT p-8
Gap in Grids:   gap-4 (16px) or gap-5 (20px) - NOT gap-6
Section Gap:    space-y-6 (24px) between major sections
Internal Gap:   space-y-2 or space-y-3 within cards
Page Padding:   p-6 (24px) - NOT p-8
```

**3. Color Usage for Visual Hierarchy**
```
Labels:         text-text-tertiary (#6e7681) - Very muted
Values:         text-text-primary (#e6edf3) - High contrast
Trends Up:      text-success (#3fb950) - Green
Trends Down:    text-error (#f85149) - Red
Accent Data:    text-accent-primary (#00d9ff) - Cyan for special emphasis
Secondary Text: text-text-secondary (#8b949e) - Medium gray
```

**4. Component-Specific Fixes**

### Task Checklist - UI Overhaul

#### Global Styles (`globals.css`)
- [x] Reduce base font sizes in typography section
- [x] Update heading sizes (h1: 1.5rem, h2: 1.125rem, h3: 1rem)
- [x] Add compact spacing utilities (spacing-md: 1rem, spacing-lg: 1.5rem)
- [x] Create `.label` class for consistent label styling
- [x] Create `.metric-lg`, `.metric-md`, `.metric-sm` for values
- [x] Update card-bg padding from p-8 to p-4 (var(--spacing-md))

#### MetricCard Component
- [x] Reduce value font size from text-4xl to text-2xl
- [x] Reduce padding from p-8 to p-4
- [x] Make label text-xs uppercase tracking-wider text-tertiary
- [x] Reduce icon container from h-12 w-12 to h-10 w-10
- [x] Reduce trend text sizes (text-xs)
- [x] Tighten internal spacing (mb-3 → mb-1, mt-4 → mt-2)

#### AlertCard Component
- [x] Reduce padding from p-8 to p-4 (pl-5 to compensate for left bar)
- [x] Reduce title from text-lg to text-base
- [x] Reduce icon container size (h-4 w-4)
- [x] Tighten header spacing (mb-5 → mb-3)
- [x] Reduce reason text from text-base to text-sm
- [x] Compact evidence divider section (mb-3, gap-2)
- [x] Reduce button padding (gap-2)

#### CompanyCard Component
- [x] Reduce overall padding from p-6 to p-4
- [x] Reduce company name from text-lg to text-base
- [x] Reduce market cap value from text-xl to text-base
- [x] Reduce metric grid item padding from p-3 to p-2
- [x] Tighten spacing between sections (mb-3, gap-2)
- [x] Reduce metric values from text-lg to text-base

#### TimelineCard Component
- [x] Reduce padding (p-4, pl-5)
- [x] Reduce title font size (text-base)
- [x] Compact metadata section (mb-3, gap-3)
- [x] Tighten spacing (mb-1.5, mb-0.5)

#### Dashboard Page
- [x] Reduce page padding from p-8 to p-6
- [x] Reduce h1 from text-4xl to text-2xl
- [x] Reduce h2 from text-2xl to text-lg
- [x] Reduce grid gap from gap-6 to gap-4
- [x] Tighten space-y-8 to space-y-6 (space-y-3)

#### Companies Page
- [x] Reduce page padding from p-8 to p-6
- [x] Reduce h1 from text-4xl to text-2xl
- [x] Reduce search input padding (py-3, pl-10)
- [x] Reduce grid gap from gap-6 to gap-4

#### Sidebar Component
- [x] Width already optimal at w-64
- [x] Navigation item padding already compact (py-2.5)
- [x] Section margins already appropriate (mb-8, mb-3)

#### Header Component
- [x] Height and padding already consistent (h-14)
- [x] Search bar size already appropriate

### Expected Results After Overhaul

**Before:**
- Bloated, spacious feel
- Everything same color (white)
- Poor scannability
- Unprofessional "AI slop" look

**After:**
- Dense, information-rich Bloomberg terminal feel
- Clear visual hierarchy (muted labels, prominent values)
- Professional analytics dashboard aesthetic
- Scannable data with proper contrast

### Color Reference Quick Guide

| Element Type | Color Class | Hex |
|--------------|-------------|-----|
| Page Title | text-text-primary | #e6edf3 |
| Section Title | text-text-primary | #e6edf3 |
| Label (MOST IMPORTANT) | text-text-tertiary | #6e7681 |
| Metric Value | text-text-primary | #e6edf3 |
| Accent Value | text-accent-primary | #00d9ff |
| Body Text | text-text-secondary | #8b949e |
| Timestamp | text-text-tertiary | #6e7681 |
| Success/Up | text-success | #3fb950 |
| Error/Down | text-error | #f85149 |
| Warning | text-warning | #d29922 |

### Size Reference Quick Guide

| Element | Current | Target |
|---------|---------|--------|
| Page Title (h1) | text-4xl (36px) | text-2xl (24px) |
| Section Title (h2) | text-2xl (24px) | text-lg (18px) |
| Card Title | text-lg (18px) | text-base (16px) |
| Metric Value | text-4xl (36px) | text-2xl (24px) |
| Small Metric | text-lg/text-xl | text-base (16px) |
| Label | text-sm (14px) | text-xs (12px) |
| Body | text-base (16px) | text-sm (14px) |
| Card Padding | p-8 (32px) | p-4 (16px) |
| Grid Gap | gap-6 (24px) | gap-4 (16px) |

---
