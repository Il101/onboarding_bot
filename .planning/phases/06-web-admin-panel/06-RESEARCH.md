# Phase 6: Web Admin Panel - Research

**Researched:** 2026-04-19
**Domain:** FastAPI web admin panel with HTMX + Alpine.js
**Confidence:** MEDIUM

## Summary

This research explores how to implement a web admin panel for the V-Brain system using the HTMX + Alpine.js stack as specified in CLAUDE.md. The admin panel will enable administrators to upload PDF and Telegram sources, review extracted knowledge before publication, manage users, and view analytics. The implementation will build upon the existing FastAPI backend infrastructure and leverage HTMX for dynamic UI updates without JavaScript complexity.

**Primary recommendation:** Use FastAPI with Jinja2 templates, HTMX for dynamic interactions, and Alpine.js for lightweight state management to create a responsive admin interface with minimal frontend tooling.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Source file upload | API / Backend | Browser / Client | File handling and validation belong in the backend for security and processing |
| Knowledge review | API / Backend | — | Knowledge approval/rejection involves business logic and database state changes |
| User management | API / Backend | Browser / Client | User authentication and authorization decisions belong in the backend |
| Analytics dashboard | API / Backend | Browser / Client | Data aggregation and calculation should happen server-side for consistency |
| Dynamic UI updates | Browser / Client | API / Backend | HTMX handles client-side dynamic content with server-driven updates |
| State management | Browser / Client | — | Alpine.js provides lightweight reactive state without a framework |
| Form handling | Browser / Client | API / Backend | Frontend manages form UX, backend handles validation and business logic |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115.x | Web API backend | Already implemented with ingest and knowledge routers, ready for admin routes |
| HTMX | 1.9.x | Dynamic UI updates | Enables server-rendered HTML with client-side interactivity without JavaScript complexity |
| Alpine.js | 3.14.x | Lightweight JavaScript framework | Provides reactive state management and component capabilities for minimal UI interactions |
| Jinja2 | 3.1.x | Template engine | FastAPI's default template engine, already available in the project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Tailwind CSS | 3.4.x | Utility-first CSS | Used with CDN for styling admin panels without build pipeline |
| python-telegram-bot | 20.7 | Telegram integration | Already implemented, admin can reference user_id from this |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| HTMX + Alpine.js | React + FastAPI | React adds significant complexity for an internal admin tool; HTMX provides equivalent functionality with 95% less code |
| HTMX + Alpine.js | Vue + FastAPI | Vue is a good middle-ground but still requires a separate build pipeline; HTMX works with static files |
| Server-rendered | Full SPA approach | SPA would require Node.js, bundling, and deployment complexity - overkill for admin CRUD operations |

**Installation:**
```bash
pip install jinja2
# No additional packages needed - HTMX and Alpine.js served via CDN
```

**Version verification:**
- FastAPI: 0.115.6 (verified)
- Jinja2: 3.1.6 (verified)
- SQLAlchemy: 2.0.25 (verified)
- python-telegram-bot: 20.7 (verified)

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (Admin)                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   HTMX      │  │  Alpine.js   │  │   Templates     │  │
│  │   (HTTP)    │  │ (State)      │  │   (Jinja2)      │  │
│  └─────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               │ HTTP
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Admin Router│  │   DB Session │  │   Models        │  │
│  │ (New)       │  │ (SQLAlchemy) │  │ (Source, Ingest, │  │
│  └─────────────┘  └──────────────┘  │  Feedback)      │  │
│           │           │           └─────────────────┘  │
│           │           │                                │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ File Upload │  │ Knowledge   │  │   Analytics     │  │
│  │ Handler     │  │ Review      │  │   Queries       │  │
│  └─────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data Storage                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ PostgreSQL │  │   Qdrant    │  │   File System   │  │
│  │ (Metadata)  │  │ (Vectors)   │  │   (Uploads)     │  │
│  └─────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
src/
├── api/
│   ├── routes/
│   │   ├── admin.py          # New admin routes
│   │   ├── ingest.py         # Existing
│   │   └── knowledge.py      # Existing
│   ├── templates/            # New - Jinja2 templates
│   │   ├── base.html         # Base template with layout
│   │   ├── sidebar.html      # Navigation sidebar
│   │   ├── sources/          # Source management templates
│   │   ├── knowledge/        # Knowledge review templates
│   │   ├── users/           # User management templates
│   │   └── analytics/       # Dashboard templates
│   └── static/              # New - Static assets
│       ├── css/
│       │   └── admin.css    # Custom admin styles
│       └── js/
│           └── admin.js     # Alpine.js app entry
├── models/
│   ├── source.py            # Existing
│   ├── ingest_job.py        # Existing
│   ├── feedback_event.py   # Existing
│   └── knowledge_item.py   # New - for review queue
└── core/
    └── config.py           # Add admin_password field
```

### Pattern 1: HTMX Dynamic Content Updates
**What:** Use HTMX to replace HTML fragments without full page reloads
**When to use:** For tables, forms, and any dynamic content that needs to update without navigation
**Example:**
```html
<!-- Base template with HTMX -->
<div id="main-content" hx-get="/api/admin/sources" hx-trigger="load">
    <!-- Content will be loaded here -->
</div>

<!-- HTMX form submission -->
<form hx-post="/api/admin/sources/upload" hx-target="#upload-status">
    <input type="file" name="pdf_file" accept=".pdf">
    <button type="submit">Upload</button>
    <div id="upload-status"></div>
</form>
```

### Pattern 2: Alpine.js State Management
**What:** Alpine.js for reactive UI state and component behavior
**When to use:** For toggles, filters, checkboxes, and any client-side state
**Example:**
```html
<div x-data="{ showFilters: false, selectedItems: [] }">
    <button @click="showFilters = !showFilters">
        Toggle Filters
    </button>

    <div x-show="showFilters">
        <!-- Filter form -->
    </div>

    <!-- Bulk actions with selected items -->
    <button
        x-show="selectedItems.length > 0"
        @click="approveSelected()">
        Approve Selected
    </button>
</div>
```

### Pattern 3: Server-Side Pagination with HTMX
**What:** Server-rendered paginated tables with HTMX fragment replacement
**When to use:** For large datasets (sources, knowledge items, users)
**Example:**
```html
<table>
    <thead>
        <tr>
            <th><input type="checkbox" x-model="selectAll"></th>
            <th>Source</th>
            <th>Status</th>
            <th>Progress</th>
        </tr>
    </thead>
    <tbody>
        <!-- Items loaded via HTMX -->
        <tr hx-get="/api/admin/sources?page={{page}}" hx-trigger="load">
            <!-- Dynamic content -->
        </tr>
    </tbody>
</table>
```

### Anti-Patterns to Avoid
- **Full SPA approach**: Using React/Vue for a simple admin panel adds unnecessary build complexity
- **Client-side pagination**: Loading all data in memory for pagination is inefficient
- **Mixed architectural tiers**: Don't put business logic in Alpine.js - keep it in FastAPI
- **Manual DOM manipulation**: Use HTMX and Alpine.js instead of document.getElementById()

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Simple password auth | Custom auth system | FastAPI middleware or dependency | HTMX handles session cookies; FastAPI manages auth state |
| File upload validation | Manual file checking | FastAPI UploadFile with custom validators | FastAPI handles multipart/form-data, size limits, type checking |
| Data filtering | Manual SQL | SQLAlchemy + Pydantic models | ORM prevents SQL injection, provides validation |
| Pagination | Custom offset logic | FastAPI pagination utilities | Built-in limit/offset handling, cursor-based alternatives |
| Bulk operations | Manual iteration per item | Batch API endpoints | Network-efficient, atomic operations, better error handling |

**Key insight:** Admin panels are CRUD-heavy applications. The HTMX + Alpine.js pattern leverages server-side rendering for complex logic while keeping client interactions simple and declarative.

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Knowledge review queue needs new SQLAlchemy model (knowledge_item.py with status field: published/pending/rejected) | Create new model with migration script |
| Live service config | No admin-specific configuration yet in config.py | Add admin_password field to Settings class |
| OS-registered state | None - admin panel doesn't register OS-level services | None |
| Secrets/env vars | Admin password needs to be added to .env | Add ADMIN_PASSWORD to env configuration |
| Build artifacts | No build artifacts - HTMX/Alpine.js served as static files | None |

## Common Pitfalls

### Pitfall 1: Over-Engineering with Frontend Frameworks
**What goes wrong:** Teams often reach for React/Vue for admin panels, adding unnecessary complexity
**Why it happens:** "This looks like a web app, so we need a framework" mental model
**How to avoid:** Remind yourself that admin panels are primarily data-focused with simple interactions - HTMX handles 90% of common patterns
**Warning signs:** Discussion about component library, state management patterns, build pipeline requirements

### Pitfall 2: Mixing Client and Server Business Logic
**What goes wrong:** Putting data filtering, validation, or business logic in Alpine.js instead of FastAPI
**Why it happens:** Trying to optimize server round trips when the real bottleneck is database queries
**How to avoid:** Keep all business logic in FastAPI endpoints. Alpine.js should only manage UI state and trigger actions
**Warning signs:** Complex Alpine.js reactive expressions, manual API response parsing, data manipulation in x-data

### Pitfall 3: Ignoring HTMX Progress Indicators
**What goes wrong:** Long-running operations (file uploads, knowledge extraction) leave users wondering what's happening
**Why it happens:** HTMX replaces content but doesn't provide loading states by default
**How to avoid:** Use HTMX swap:outerHTML with loading indicators and progress updates via SSE or polling
**Warning signs:** Users refreshing pages, impatient clicking, confusion about operation status

### Pitfall 4: Not Leveraging Server-Side Rendering
**What goes wrong:** Trying to do too much client-side when the server can render the full HTML
**Why it happens:** JavaScript mindset where everything must be dynamic
**How to avoid:** Use HTMX for progressive enhancement - start with server-rendered HTML and add interactivity only where needed
**Warning signs:** Excessive use of x-init, DOM manipulation, complex Alpine.js components

### Pitfall 5: Forgetting Security in HTMX Applications
**What goes wrong:** HTMX makes it easy to add features but security is often overlooked
**Why it happens:** Focus on UI features while treating security as an afterthought
**How to avoid:** Implement CSRF protection, validate all inputs, use proper session management
**Warning signs:** Direct DOM manipulation from untrusted sources, no CSRF tokens, missing input validation

## Code Examples

### HTMX File Upload with Progress
```python
# src/api/routes/admin.py
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from src.api.deps import get_db_session

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/sources/pdf")
async def upload_pdf_source(file: UploadFile, db: Session = Depends(get_db_session)):
    # Same logic as ingest.py but wrapped for admin panel
    from src.models.source import Source, SourceType
    from src.tasks.ingest import ingest_pdf

    # Validate and save file
    # Create source record
    # Queue Celery task
    return {"job_id": task.id, "status": "started"}
```

```html
<!-- src/api/templates/sources/upload.html -->
<form
    hx-post="/api/admin/sources/pdf"
    hx-target="#upload-status"
    hx-swap="outerHTML"
    hx-indicator="#upload-progress">
    <input type="file" name="pdf_file" accept=".pdf" required>
    <button type="submit">Upload PDF</button>
    <progress id="upload-progress" value="0" max="100" style="display: none"></progress>
    <div id="upload-status"></div>
</form>

<script>
// Show progress indicator on htmx:beforeRequest
document.addEventListener('htmx:beforeRequest', (e) => {
    if (e.detail.target.id === 'upload-status') {
        document.getElementById('upload-progress').style.display = 'block';
    }
});
</script>
```

### Knowledge Review Table with Filters
```python
# src/api/routes/admin.py
from pydantic import BaseModel
from typing import Optional, List

class KnowledgeFilter(BaseModel):
    topic: Optional[str] = None
    source_id: Optional[str] = None
    status: Optional[str] = None  # published/pending/rejected

@router.get("/knowledge")
async def get_knowledge_items(filter: KnowledgeFilter = None, skip: int = 0, limit: int = 20):
    query = db.query(KnowledgeItem)
    if filter:
        if filter.topic:
            query = query.filter(KnowledgeItem.topic.contains(filter.topic))
        if filter.source_id:
            query = query.filter(KnowledgeItem.source_refs.any(source_id=filter.source_id))
        if filter.status:
            query = query.filter(KnowledgeItem.status == filter.status)
    return {"items": query.offset(skip).limit(limit).all()}
```

```html
<!-- src/api/templates/knowledge/review.html -->
<div x-data="{
    filter: { topic: '', source: '', status: '' },
    items: [],
    loading: false
}">
    <!-- Filter form -->
    <div class="filters">
        <input
            type="text"
            x-model="filter.topic"
            placeholder="Filter by topic..."
            @input="debounceFilter()">
        <select x-model="filter.status" @change="filterItems()">
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="published">Published</option>
            <option value="rejected">Rejected</option>
        </select>
    </div>

    <!-- Table with HTMX -->
    <table>
        <thead>
            <tr>
                <th><input type="checkbox" @change="toggleAll()"></th>
                <th>Fact</th>
                <th>Topic</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            <template x-for="item in items" :key="item.id">
                <tr>
                    <td><input type="checkbox" :value="item.id" x-model="selectedItems"></td>
                    <td x-text="item.fact"></td>
                    <td x-text="item.topic"></td>
                    <td x-text="item.confidence"></td>
                    <td x-text="item.status"></td>
                    <td>
                        <button @click="edit(item)">Edit</button>
                        <button @click="approve(item.id)" x-show="item.status === 'pending'">Approve</button>
                    </td>
                </tr>
            </template>
        </tbody>
    </table>

    <!-- Bulk approve -->
    <button
        x-show="selectedItems.length > 0"
        @click="bulkApprove()">
        Approve Selected
    </button>
</div>
```

### Admin Dashboard Analytics
```python
# src/api/routes/admin.py
@router.get("/analytics")
async def get_dashboard_analytics(db: Session = Depends(get_db_session)):
    from sqlalchemy import func, desc
    from datetime import datetime, timedelta

    # Popular questions from feedback
    popular_questions = db.query(
        FeedbackEvent.thread_id,
        func.count(FeedbackEvent.id).label('count')
    ).group_by(FeedbackEvent.thread_id).order_by(desc('count')).limit(10).all()

    # Average rating
    avg_rating = db.query(func.avg(FeedbackEvent.vote.cast(Integer))).scalar()

    # Knowledge stats
    knowledge_stats = db.query(
        func.count(KnowledgeItem.id).label('total'),
        func.sum(func.case([(KnowledgeItem.status == 'published', 1)], else_=0)).label('published'),
        func.sum(func.case([(KnowledgeItem.status == 'pending', 1)], else_=0)).label('pending'),
        func.sum(func.case([(KnowledgeItem.status == 'rejected', 1)], else_=0)).label('rejected')
    ).first()

    # User activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_users = db.query(func.count(func.distinct(FeedbackEvent.user_id))).filter(
        FeedbackEvent.created_at >= week_ago
    ).scalar()

    return {
        "popular_questions": popular_questions,
        "average_rating": avg_rating,
        "knowledge_stats": knowledge_stats,
        "active_users": active_users
    }
```

```html
<!-- src/api/templates/analytics/dashboard.html -->
<div class="dashboard">
    <div class="metrics">
        <div class="metric-card">
            <h3>Total Knowledge</h3>
            <div x-text="analytics.knowledge_stats?.total || 0"></div>
        </div>
        <div class="metric-card">
            <h3>Published</h3>
            <div class="positive" x-text="analytics.knowledge_stats?.published || 0"></div>
        </div>
        <div class="metric-card">
            <h3>Pending</h3>
            <div class="warning" x-text="analytics.knowledge_stats?.pending || 0"></div>
        </div>
        <div class="metric-card">
            <h3>Avg Rating</h3>
            <div x-text="analytics.average_rating?.toFixed(1) || 'N/A'"></div>
        </div>
        <div class="metric-card">
            <h3>Active Users</h3>
            <div x-text="analytics.active_users || 0"></div>
        </div>
    </div>

    <div class="popular-questions">
        <h3>Popular Questions</h3>
        <ul>
            <template x-for="q in analytics.popular_questions">
                <li>
                    <span x-text="q.count"></span>
                    <span x-text="q.thread_id"></span>
                </li>
            </template>
        </ul>
    </div>
</div>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Server-rendered HTML + jQuery | HTMX + Alpine.js | 2021-2023 | Eliminates 80% of JavaScript code while maintaining dynamic UI |
| Full-page form submissions | HTMX partial updates | 2022-present | Better UX, faster perceived performance, reduced bandwidth |
| Custom CSS frameworks | Tailwind CSS utility classes | 2023-2024 | Rapid development with consistent design, no custom CSS needed |
| Server-side session management | Cookie-based auth | 2023-present | Stateless sessions with JWT or simple auth cookies |

**Deprecated/outdated:**
- jQuery with AJAX patterns - HTMX provides declarative approach
- Server-side rendering with sprinkled jQuery - HTMX handles all dynamic needs
- Manual HTML manipulation with document.getElementById() - Alpinejs reactivity pattern
- Traditional form submissions with full page reloads - HTMX handles partial updates

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | HTMX can handle file upload progress indicators | Pitfalls 3 | Users will be confused about upload status |
| A2 | Alpine.js can manage bulk selection state for knowledge items | Architecture Patterns | Bulk operations will be difficult to implement |
| A3 | Existing FastAPI application structure can be extended with admin routes | Standard Stack | Route conflicts or integration issues may arise |
| A4 | PostgreSQL can handle the analytics queries efficiently | Code Examples | Dashboard may be slow with large datasets |

## Open Questions (RESOLVED)

1. **How to handle real-time ingest status updates without WebSocket?** (RESOLVED)
   - Decision: Use polling for MVP. Real-time updates (WebSocket/SSE) explicitly deferred in CONTEXT.md deferred items. Polling every 5s is sufficient for a single-admin internal tool.

2. **Should admin password be bcrypt hashed or SHA-256?** (RESOLVED)
   - Decision: SHA-256 hash. Plan 01 implements `_hash_password` using `hashlib.sha256`. This is simpler than bcrypt (no extra dependency) while still not storing plaintext. Adequate for single-admin internal tool behind httponly cookie auth. bcrypt would be preferred for multi-user systems, but this MVP has exactly one admin password.

3. **How to handle knowledge editing before approval?** (RESOLVED)
   - Decision: Modify in-place. CONTEXT.md D-04 states "Admin can edit fact before publication" -- the pending KnowledgeItem is updated directly, no version history needed. This is the simplest approach for MVP.

4. **Should dashboard use charts or just numbers?** (RESOLVED)
   - Decision: Numbers only (metric cards), no charts. CONTEXT.md D-07 specifies "basic metrics on one page" and the deferred items list explicitly defers charts (Chart.js). Plan 05 implements server-rendered metric cards with count/percentage displays.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| FastAPI | Admin panel | Yes | 0.115.6 | -- |
| PostgreSQL | Analytics data | ? | 16+ | SQLite (not for production) |
| Celery | File processing | ? | latest | Sequential processing |
| Redis | Celery broker | ? | latest | Local development without tasks |

**Missing dependencies with no fallback:**
- PostgreSQL - need to verify running and accessible
- Redis - needed for Celery task queue

**Missing dependencies with fallback:**
- Local Celery/Redis - can run without background tasks for initial testing

## Validation Architecture

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | tests/conftest.py (if exists) |
| Quick run command | `pytest tests/ -k "test_" -x` |
| Full suite command | `pytest tests/` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADM-01 | PDF upload endpoint works | integration | `pytest tests/test_admin.py::test_pdf_upload` | No - Wave 0 |
| ADM-02 | Telegram upload endpoint works | integration | `pytest tests/test_admin.py::test_telegram_upload` | No - Wave 0 |
| ADM-03 | Knowledge review table loads | integration | `pytest tests/test_admin.py::test_knowledge_list` | No - Wave 0 |
| ADM-04 | Knowledge approval process | integration | `pytest tests/test_admin.py::test_approve_knowledge` | No - Wave 0 |
| ADM-05 | Knowledge rejection process | integration | `pytest tests/test_admin.py::test_reject_knowledge` | No - Wave 0 |
| ADM-06 | User management CRUD | integration | `pytest tests/test_admin.py::test_user_management` | No - Wave 0 |
| ADM-07 | Analytics endpoints return data | integration | `pytest tests/test_admin.py::test_analytics` | No - Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_admin.py -x`
- **Per wave merge:** `pytest tests/test_admin.py -k "test_" --tb=short`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_admin.py` - basic admin functionality tests
- [ ] `tests/conftest.py` - test fixtures for admin testing
- [ ] Framework install: already present in project

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | FastAPI auth middleware + secure cookies |
| V3 Session Management | yes | Session timeout and secure cookie flags |
| V4 Access Control | yes | Role-based access for admin-only routes |
| V5 Input Validation | yes | FastAPI + Pydantic validation on all endpoints |
| V6 Cryptography | no | Password hashing (SHA-256) but no other cryptography |

### Known Threat Patterns for FastAPI

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| CSRF attacks | Denial | Use HTMX with proper CSRF tokens for form submissions |
| SQL injection | Tampering | Use SQLAlchemy ORM with parameterized queries |
| File upload attacks | Tampering | Validate file types, scan for malicious content |
| Unauthorized admin access | Elevation | Role-based access control with proper session management |

## Sources

### Primary (HIGH confidence)
- Context7: `/fastapi/fastapi` -- FastAPI router architecture, template rendering, dependency injection
- Context7: `/jinja/jinja` -- Template inheritance, macros, filters for admin UI
- Existing codebase: `src/api/main.py`, `src/api/routes/ingest.py` -- Current FastAPI structure to extend

### Secondary (MEDIUM confidence)
- HTMX documentation (from training data) -- HTMX attributes, swap strategies, progress indicators
- Alpine.js documentation (from training data) -- Reactive patterns, x-data syntax, event handling
- Tailwind CSS documentation (from training data) -- Utility classes, responsive design patterns

### Tertiary (LOW confidence)
- Web search results (unavailable) -- Latest HTMX + FastAPI patterns and best practices

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - Based on existing FastAPI usage and HTMX/Alpine.js patterns
- Architecture: MEDIUM - Server-rendered admin panels are well-established but need to integrate with existing backend
- Pitfalls: HIGH - Common patterns for admin UI have been documented extensively

**Research date:** 2026-04-19
**Valid until:** 2026-05-19
