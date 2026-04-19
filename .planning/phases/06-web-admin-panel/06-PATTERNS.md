# Phase 6: Web Admin Panel - Pattern Map

**Mapped:** 2026-04-19
**Files analyzed:** 9 new/modified files
**Analogs found:** 8 / 9

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|-----------------|---------------|
| `src/api/routes/admin.py` | controller | request-response | `src/api/routes/ingest.py` | exact |
| `src/api/templates/base.html` | component | request-response | No analog (new template pattern) | N/A |
| `src/api/templates/sidebar.html` | component | request-response | No analog (new template pattern) | N/A |
| `src/api/templates/sources/` | component | request-response | No analog (new template pattern) | N/A |
| `src/api/templates/knowledge/` | component | request-response | No analog (new template pattern) | N/A |
| `src/api/templates/users/` | component | request-response | No analog (new template pattern) | N/A |
| `src/api/templates/analytics/` | component | request-response | No analog (new template pattern) | N/A |
| `src/models/knowledge_item.py` | model | CRUD | `src/models/source.py` | exact |
| `src/core/config.py` (update) | config | request-response | `src/core/config.py` (existing) | exact |

## Pattern Assignments

### `src/api/routes/admin.py` (controller, request-response)

**Analog:** `src/api/routes/ingest.py`

**Imports pattern** (lines 1-10):
```python
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from src.api.deps import get_db_session
from src.models.source import Source
from src.models.ingest_job import IngestJob
from src.core.config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])
```

**Error handling pattern** (lines 22-30 from ingest.py):
```python
def _validate_size(content: bytes):
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")
```

**Session dependency pattern** (lines 13-18 from deps.py):
```python
def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**FastAPI route pattern** (lines 42-71 from ingest.py):
```python
@router.post("/sources/pdf")
async def upload_pdf_source(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session)
):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid PDF file type")
    
    # Validation logic
    content = await file.read()
    _validate_size(content)
    
    # Database operations
    source_id = str(uuid4())
    safe_name = f"{uuid4()}.pdf"
    file_path = Path(settings.upload_dir) / safe_name
    file_path.write_bytes(content)
    
    # Task queuing
    task = ingest_pdf.delay(source_id, str(file_path))
    return {"job_id": task.id, "status": "started"}
```

**Router registration pattern** (lines 22-23 from main.py):
```python
app.include_router(admin_router)
```

---

### `src/api/templates/base.html` (component, request-response)

**Analog:** No existing analog - new template pattern

**HTMX base pattern** (from research examples):
```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>V-Brain Admin Panel</title>
    <script src="https://unpkg.com/htmx.org@1.9.12"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.0/dist/cdn.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdn.jsdelivr.net/npm/@tabler/icons@latest/iconfont/tabler-icons.min.css" rel="stylesheet">
</head>
<body class="bg-gray-50">
    <div class="flex h-screen">
        <!-- Sidebar will be loaded here -->
        <div id="sidebar-container" 
             hx-get="/api/admin/sidebar" 
             hx-trigger="load"
             class="w-64 bg-white shadow-lg">
            <div class="loading">Loading...</div>
        </div>
        
        <!-- Main content area -->
        <div id="main-content" class="flex-1 overflow-y-auto">
            <div id="content-container">
                <!-- Content will be loaded here -->
            </div>
        </div>
    </div>
</body>
</html>
```

---

### `src/api/templates/sidebar.html` (component, request-response)

**Analog:** No existing analog - new template pattern

**Alpine.js sidebar pattern** (from research examples):
```html
<div x-data="{ activeSection: 'sources' }" class="h-full flex flex-col">
    <div class="p-4 border-b">
        <h1 class="text-xl font-bold text-gray-800">V-Brain Admin</h1>
    </div>
    
    <nav class="flex-1 p-4">
        <ul class="space-y-2">
            <li>
                <a href="#sources" 
                   @click="activeSection = 'sources'"
                   :class="activeSection === 'sources' ? 'bg-blue-50 text-blue-600' : ''"
                   class="flex items-center p-3 rounded-lg hover:bg-gray-100 transition-colors">
                    <i class="ti ti-file-upload w-5 mr-3"></i>
                    <span>Источники</span>
                </a>
            </li>
            <li>
                <a href="#knowledge" 
                   @click="activeSection = 'knowledge'"
                   :class="activeSection === 'knowledge' ? 'bg-blue-50 text-blue-600' : ''"
                   class="flex items-center p-3 rounded-lg hover:bg-gray-100 transition-colors">
                    <i class="ti ti-book w-5 mr-3"></i>
                    <span>Знания</span>
                </a>
            </li>
            <li>
                <a href="#users" 
                   @click="activeSection = 'users'"
                   :class="activeSection === 'users' ? 'bg-blue-50 text-blue-600' : ''"
                   class="flex items-center p-3 rounded-lg hover:bg-gray-100 transition-colors">
                    <i class="ti ti-users w-5 mr-3"></i>
                    <span>Пользователи</span>
                </a>
            </li>
            <li>
                <a href="#analytics" 
                   @click="activeSection = 'analytics'"
                   :class="activeSection === 'analytics' ? 'bg-blue-50 text-blue-600' : ''"
                   class="flex items-center p-3 rounded-lg hover:bg-gray-100 transition-colors">
                    <i class="ti ti-chart-line w-5 mr-3"></i>
                    <span>Аналитика</span>
                </a>
            </li>
        </ul>
    </nav>
    
    <div class="p-4 border-t">
        <button class="w-full flex items-center p-3 rounded-lg hover:bg-gray-100 transition-colors">
            <i class="ti ti-logout w-5 mr-3"></i>
            <span>Выход</span>
        </button>
    </div>
</div>

<script>
// Update main content when sidebar link is clicked
document.addEventListener('htmx:afterRequest', (event) => {
    if (event.detail.target.id === 'sidebar-container') {
        const section = event.detail.xhr.response;
        if (section) {
            const container = document.getElementById('content-container');
            container.innerHTML = section;
        }
    }
});
</script>
```

---

### `src/api/templates/sources/` (component, request-response)

**Analog:** No existing analog - new template pattern

**HTMX file upload pattern** (from research examples):
```html
<!-- sources/upload.html -->
<div x-data="{ uploading: false }">
    <h2 class="text-2xl font-bold mb-6">Загрузка источников</h2>
    
    <div class="grid grid-cols-2 gap-6">
        <!-- PDF Upload -->
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold mb-4">PDF документ</h3>
            <form hx-post="/api/admin/sources/pdf" 
                  hx-target="#pdf-status"
                  hx-swap="outerHTML"
                  hx-indicator="#pdf-progress">
                <input type="file" 
                       name="pdf_file" 
                       accept=".pdf" 
                       class="block w-full text-sm text-gray-500
                              file:mr-4 file:py-2 file:px-4
                              file:rounded-full file:border-0
                              file:text-sm file:font-semibold
                              file:bg-blue-50 file:text-blue-700
                              hover:file:bg-blue-100">
                <button type="submit" 
                        class="mt-4 w-full bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700">
                    Загрузить PDF
                </button>
                <progress id="pdf-progress" value="0" max="100" class="hidden mt-4"></progress>
                <div id="pdf-status"></div>
            </form>
        </div>
        
        <!-- Telegram Upload -->
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold mb-4">Telegram логи</h3>
            <form hx-post="/api/admin/sources/telegram" 
                  hx-target="#telegram-status"
                  hx-swap="outerHTML"
                  hx-indicator="#telegram-progress">
                <input type="file" 
                       name="json_file" 
                       accept=".json" 
                       class="block w-full text-sm text-gray-500
                              file:mr-4 file:py-2 file:px-4
                              file:rounded-full file:border-0
                              file:text-sm file:font-semibold
                              file:bg-blue-50 file:text-blue-700
                              hover:file:bg-blue-100">
                <input type="file" 
                       name="voice_files" 
                       accept=".ogg" 
                       multiple 
                       class="block w-full text-sm text-gray-500 mt-2
                              file:mr-4 file:py-2 file:px-4
                              file:rounded-full file:border-0
                              file:text-sm file:font-semibold
                              file:bg-blue-50 file:text-blue-700
                              hover:file:bg-blue-100">
                <button type="submit" 
                        class="mt-4 w-full bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700">
                    Загрузить Telegram
                </button>
                <progress id="telegram-progress" value="0" max="100" class="hidden mt-4"></progress>
                <div id="telegram-status"></div>
            </form>
        </div>
    </div>
</div>
```

**HTMX table with status pattern**:
```html
<!-- sources/list.html -->
<div x-data="{ sources: [], loading: true }" class="bg-white rounded-lg shadow">
    <div class="p-6">
        <h3 class="text-lg font-semibold mb-4">Источники</h3>
        
        <table class="w-full">
            <thead>
                <tr class="border-b">
                    <th class="text-left py-3 px-4">Имя</th>
                    <th class="text-left py-3 px-4">Тип</th>
                    <th class="text-left py-3 px-4">Статус</th>
                    <th class="text-left py-3 px-4">Сообщений</th>
                    <th class="text-left py-3 px-4">Действия</th>
                </tr>
            </thead>
            <tbody>
                <template x-for="source in sources" :key="source.id">
                    <tr class="border-b hover:bg-gray-50">
                        <td class="py-3 px-4" x-text="source.filename"></td>
                        <td class="py-3 px-4">
                            <span x-text="source.type" class="px-2 py-1 rounded text-xs"></span>
                        </td>
                        <td class="py-3 px-4">
                            <span x-text="source.status" 
                                  :class="getStatusColor(source.status)"
                                  class="px-2 py-1 rounded text-xs"></span>
                        </td>
                        <td class="py-3 px-4" x-text="source.messages_count || 0"></td>
                        <td class="py-3 px-4">
                            <button x-show="source.status === 'processing'"
                                    class="text-blue-600 hover:text-blue-800"
                                    @click="getStatus(source.id)">
                                <i class="ti ti-refresh"></i>
                            </button>
                        </td>
                    </tr>
                </template>
            </tbody>
        </table>
    </div>
</div>

<script>
function getStatusColor(status) {
    const colors = {
        'pending': 'bg-gray-100 text-gray-800',
        'processing': 'bg-yellow-100 text-yellow-800',
        'completed': 'bg-green-100 text-green-800',
        'failed': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
}

// Load sources on page load
document.addEventListener('htmx:afterSwap', (event) => {
    if (event.target.id === 'content-container') {
        // Load initial data
    }
});
</script>
```

---

### `src/api/templates/knowledge/` (component, request-response)

**Analog:** No existing analog - new template pattern

**HTMX knowledge review table pattern** (from research examples):
```html
<!-- knowledge/review.html -->
<div x-data="{ 
    items: [],
    selectedItems: [],
    filter: { topic: '', status: '' },
    loading: false
}">
    <div class="bg-white rounded-lg shadow">
        <div class="p-6">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-semibold">Проверка знаний</h3>
                <div class="space-x-2">
                    <select x-model="filter.topic" @change="filterItems()">
                        <option value="">Все темы</option>
                        <template x-for="topic in topics" :key="topic">
                            <option :value="topic" x-text="topic"></option>
                        </template>
                    </select>
                    <select x-model="filter.status" @change="filterItems()">
                        <option value="">Все статусы</option>
                        <option value="published">Опубликовано</option>
                        <option value="pending">На проверке</option>
                        <option value="rejected">Отклонено</option>
                    </select>
                    <button x-show="selectedItems.length > 0"
                            @click="bulkApprove()"
                            class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
                        Одобрить выбранное
                    </button>
                </div>
            </div>
            
            <table class="w-full">
                <thead>
                    <tr class="border-b">
                        <th class="text-left py-3 px-4">
                            <input type="checkbox" 
                                   :checked="selectedItems.length === items.length"
                                   @change="toggleAll()">
                        </th>
                        <th class="text-left py-3 px-4">Факт</th>
                        <th class="text-left py-3 px-4">Тема</th>
                        <th class="text-left py-3 px-4">Достоверность</th>
                        <th class="text-left py-3 px-4">Статус</th>
                        <th class="text-left py-3 px-4">Действия</th>
                    </tr>
                </thead>
                <tbody>
                    <template x-for="item in items" :key="item.id">
                        <tr class="border-b hover:bg-gray-50">
                            <td class="py-3 px-4">
                                <input type="checkbox" 
                                       :value="item.id" 
                                       x-model="selectedItems">
                            </td>
                            <td class="py-3 px-4">
                                <div x-text="item.fact" class="max-w-xs truncate"></div>
                            </td>
                            <td class="py-3 px-4" x-text="item.topic"></td>
                            <td class="py-3 px-4">
                                <div class="flex items-center">
                                    <div class="w-20 bg-gray-200 rounded-full h-2 mr-2">
                                        <div class="bg-blue-600 h-2 rounded-full" 
                                             :style="`width: ${item.confidence * 100}%`"></div>
                                    </div>
                                    <span x-text="Math.round(item.confidence * 100)"></span>
                                </div>
                            </td>
                            <td class="py-3 px-4">
                                <span x-text="getStatusText(item.status)"
                                      :class="getStatusClass(item.status)"
                                      class="px-2 py-1 rounded text-xs"></span>
                            </td>
                            <td class="py-3 px-4">
                                <button x-show="item.status === 'pending'"
                                        @click="approve(item.id)"
                                        class="text-green-600 hover:text-green-800 mr-2">
                                    <i class="ti ti-check"></i>
                                </button>
                                <button x-show="item.status === 'pending'"
                                        @click="reject(item.id)"
                                        class="text-red-600 hover:text-red-800 mr-2">
                                    <i class="ti ti-x"></i>
                                </button>
                                <button @click="edit(item)"
                                       class="text-blue-600 hover:text-blue-800">
                                    <i class="ti ti-edit"></i>
                                </button>
                            </td>
                        </tr>
                    </template>
                </tbody>
            </table>
        </div>
    </div>
</div>
```

---

### `src/api/templates/users/` (component, request-response)

**Analog:** No existing analog - new template pattern

**Simple user management pattern**:
```html
<!-- users/manage.html -->
<div x-data="{ 
    users: [],
    newUser: { user_id: '', role: 'employee' }
}">
    <div class="bg-white rounded-lg shadow">
        <div class="p-6">
            <h3 class="text-lg font-semibold mb-6">Управление пользователями</h3>
            
            <!-- Add User Form -->
            <div class="mb-6 p-4 bg-gray-50 rounded-lg">
                <h4 class="font-medium mb-3">Добавить пользователя</h4>
                <form @submit.prevent="addUser()">
                    <div class="grid grid-cols-2 gap-4">
                        <input type="number" 
                               x-model="newUser.user_id"
                               placeholder="Telegram User ID"
                               class="px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <select x-model="newUser.role"
                                class="px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="employee">Сотрудник</option>
                            <option value="mentor">Наставник</option>
                            <option value="admin">Администратор</option>
                        </select>
                    </div>
                    <button type="submit"
                            class="mt-4 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                        Добавить
                    </button>
                </form>
            </div>
            
            <!-- Users Table -->
            <table class="w-full">
                <thead>
                    <tr class="border-b">
                        <th class="text-left py-3 px-4">User ID</th>
                        <th class="text-left py-3 px-4">Роль</th>
                        <th class="text-left py-3 px-4">Дата добавления</th>
                        <th class="text-left py-3 px-4">Действия</th>
                    </tr>
                </thead>
                <tbody>
                    <template x-for="user in users" :key="user.user_id">
                        <tr class="border-b hover:bg-gray-50">
                            <td class="py-3 px-4" x-text="user.user_id"></td>
                            <td class="py-3 px-4">
                                <span x-text="getRoleText(user.role)"
                                      :class="getRoleClass(user.role)"
                                      class="px-2 py-1 rounded text-xs"></span>
                            </td>
                            <td class="py-3 px-4" x-text="formatDate(user.created_at)"></td>
                            <td class="py-3 px-4">
                                <button @click="removeUser(user.user_id)"
                                        class="text-red-600 hover:text-red-800">
                                    <i class="ti ti-trash"></i>
                                </button>
                            </td>
                        </tr>
                    </template>
                </tbody>
            </table>
        </div>
    </div>
</div>
```

---

### `src/api/templates/analytics/` (component, request-response)

**Analog:** No existing analog - new template pattern

**Dashboard metrics pattern** (from research examples):
```html
<!-- analytics/dashboard.html -->
<div x-data="{ analytics: null, loading: true }">
    <div class="grid grid-cols-5 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-sm font-medium text-gray-600 mb-2">Всего знаний</h3>
            <div class="text-3xl font-bold text-gray-900" x-text="analytics.knowledge_stats?.total || 0"></div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-sm font-medium text-gray-600 mb-2">Опубликовано</h3>
            <div class="text-3xl font-bold text-green-600" x-text="analytics.knowledge_stats?.published || 0"></div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-sm font-medium text-gray-600 mb-2">На проверке</h3>
            <div class="text-3xl font-bold text-yellow-600" x-text="analytics.knowledge_stats?.pending || 0"></div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-sm font-medium text-gray-600 mb-2">Отклонено</h3>
            <div class="text-3xl font-bold text-red-600" x-text="analytics.knowledge_stats?.rejected || 0"></div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-sm font-medium text-gray-600 mb-2">Активные пользователи</h3>
            <div class="text-3xl font-bold text-blue-600" x-text="analytics.active_users || 0"></div>
        </div>
    </div>
    
    <div class="grid grid-cols-2 gap-6">
        <!-- Popular Questions -->
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold mb-4">Популярные вопросы</h3>
            <ul class="space-y-2">
                <template x-for="q in analytics.popular_questions" :key="q.thread_id">
                    <li class="flex justify-between items-center py-2 border-b">
                        <span class="text-sm text-gray-600 truncate max-w-xs" x-text="q.thread_id"></span>
                        <span class="text-sm font-medium text-gray-900" x-text="q.count"></span>
                    </li>
                </template>
            </ul>
        </div>
        
        <!-- Average Rating -->
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold mb-4">Средняя оценка ответов</h3>
            <div class="text-4xl font-bold text-gray-900 mb-4" x-text="analytics.average_rating?.toFixed(1) || 'N/A'"></div>
            <div class="flex items-center">
                <div class="flex text-yellow-400">
                    <template x-for="i in 5" :key="i">
                        <i class="ti ti-star"></i>
                    </template>
                </div>
                <span class="ml-2 text-sm text-gray-600">из 5</span>
            </div>
        </div>
    </div>
</div>
```

---

### `src/models/knowledge_item.py` (model, CRUD)

**Analog:** `src/models/source.py`

**Model pattern** (matching source.py structure):
```python
from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, String, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base

class KnowledgeStatus(str, enum.Enum):
    PUBLISHED = "published"
    PENDING = "pending"
    REJECTED = "rejected"

class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fact: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    source_refs: Mapped[str] = mapped_column(Text)  # JSON string for simplicity
    status: Mapped[KnowledgeStatus] = mapped_column(Enum(KnowledgeStatus), default=KnowledgeStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
```

**Publish policy pattern** (from publish_policy.py):
```python
from src.ai.extraction.schemas import KnowledgeUnit
from src.core.config import settings
from src.models.knowledge_item import KnowledgeItem, KnowledgeStatus

def should_publish_knowledge(unit: KnowledgeUnit) -> tuple[bool, str]:
    """Determine if knowledge should be auto-published or needs review"""
    if unit.confidence >= settings.knowledge_confidence_threshold:
        return True, "auto-published"
    return False, "needs review"
```

---

### `src/core/config.py` (update) (config, request-response)

**Analog:** `src/core/config.py` (existing)

**Password auth pattern** (from research):
```python
from pydantic import Field

class Settings(BaseSettings):
    # ... existing fields ...
    
    admin_password: str = Field(
        default="", 
        description="Admin panel password (plain text for simplicity)"
    )
    admin_session_timeout: int = Field(default=3600, description="Admin session timeout in seconds")

settings = Settings()
```

**Authentication middleware pattern**:
```python
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
from typing import Callable
from functools import wraps

# Simple session storage (use Redis or proper session store for production)
admin_sessions = {}

async def admin_middleware(request: Request, call_next: Callable):
    if request.url.path.startswith("/api/admin/"):
        # Check if path is login or already authenticated
        if request.url.path == "/api/admin/login":
            return await call_next(request)
        
        session_id = request.cookies.get("admin_session")
        if not session_id or session_id not in admin_sessions:
            return RedirectResponse(url="/api/admin/login")
        
        # Check session expiry
        session_data = admin_sessions[session_id]
        if datetime.utcnow() > session_data['expires']:
            del admin_sessions[session_id]
            return RedirectResponse(url="/api/admin/login")
        
        request.state.admin_user = session_data['user']
    
    response = await call_next(request)
    return response

@router.post("/api/admin/login")
async def admin_login(password: str):
    if password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    session_id = str(uuid4())
    admin_sessions[session_id] = {
        'user': 'admin',
        'expires': datetime.utcnow() + timedelta(seconds=settings.admin_session_timeout)
    }
    
    response = RedirectResponse(url="/")
    response.set_cookie(key="admin_session", value=session_id, httponly=True)
    return response

@router.post("/api/admin/logout")
async def admin_logout():
    session_id = request.cookies.get("admin_session")
    if session_id and session_id in admin_sessions:
        del admin_sessions[session_id]
    
    response = RedirectResponse(url="/api/admin/login")
    response.delete_cookie("admin_session")
    return response
```

## Shared Patterns

### Authentication
**Source:** `src/core/config.py` (update) and new middleware pattern
**Apply to:** All admin routes and templates
```python
# FastAPI middleware approach
app.add_middleware(admin_middleware)

# Session management in routes
@router.get("/api/admin/dashboard")
async def admin_dashboard(request: Request):
    if not hasattr(request.state, 'admin_user'):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"message": "Authenticated"}
```

### Error Handling
**Source:** `src/api/routes/ingest.py`
**Apply to:** All admin API routes
```python
def _validate_size(content: bytes):
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")

try:
    # Business logic here
    result = await some_operation()
    return {"success": True, "data": result}
except Exception as e:
    logger.error(f"Error in admin operation: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Database Operations
**Source:** `src/api/deps.py`
**Apply to:** All admin routes needing database access
```python
@router.get("/api/admin/sources")
async def get_sources(db: Session = Depends(get_db_session)):
    return {"sources": db.query(Source).all()}

@router.post("/api/admin/knowledge/approve")
async def approve_knowledge(
    item_ids: list[int],
    db: Session = Depends(get_db_session)
):
    try:
        items = db.query(KnowledgeItem).filter(KnowledgeItem.id.in_(item_ids)).all()
        for item in items:
            item.status = KnowledgeStatus.PUBLISHED
            item.processed_at = datetime.utcnow()
        db.commit()
        return {"success": True, "updated": len(items)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to approve knowledge")
```

### HTMX Progress Indicators
**Source:** Research examples
**Apply to:** All file upload operations
```html
<form hx-post="/api/admin/sources/upload" 
      hx-target="#upload-status"
      hx-swap="outerHTML"
      hx-indicator="#upload-progress">
    <input type="file" name="file" required>
    <button type="submit">Upload</button>
    <progress id="upload-progress" value="0" max="100" class="hidden"></progress>
    <div id="upload-status"></div>
</form>

<script>
// Show progress indicator
document.addEventListener('htmx:beforeRequest', (e) => {
    if (e.target.tagName === 'FORM' && e.target.action.includes('/upload')) {
        document.getElementById('upload-progress').classList.remove('hidden');
    }
});
</script>
```

## No Analog Found

Files with no close match in the codebase (new patterns from RESEARCH.md):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/api/templates/base.html` | component | request-response | First template in the codebase - new HTMX/Alpine.js base pattern needed |
| `src/api/templates/sidebar.html` | component | request-response | New navigation component with Alpine.js reactive state |
| `src/api/templates/sources/` | component | request-response | New source management UI with file uploads |
| `src/api/templates/knowledge/` | component | request-response | New knowledge review interface with filtering and bulk operations |
| `src/api/templates/users/` | component | request-response | New user management interface for admin panel |
| `src/api/templates/analytics/` | component | request-response | New dashboard with metrics visualization |

## Metadata

**Analog search scope:** src/api, src/models, src/core directories
**Files scanned:** 30 Python files in src
**Pattern extraction date:** 2026-04-19
**Base template patterns:** HTMX 1.9.x, Alpine.js 3.14.x, Tailwind CSS 3.4.x