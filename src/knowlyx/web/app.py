"""
knowai dashboard — read-only web UI for monitoring memory entries,
syntheses, audit log, and supersession/merge activity.

Run: uvicorn knowlyx.web.app:app --host 0.0.0.0 --port 8080

Uses the same POSTGRES_* / KNOWAI_DB_SCHEMA env vars as the store, so a single
.env file drives both backend and dashboard.
"""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from knowlyx.memory.postgres_store import PostgresMemoryStore
from knowlyx.memory.schema import MemoryEntry, MemoryKind

from knowlyx.memory.postgres_store import _validate_schema_name

KINDS = [k.value for k in MemoryKind]


def _store() -> PostgresMemoryStore:
    """Lazy single store — reuses the same merge/audit/embedding logic as MCP."""
    global _STORE  # noqa: PLW0603
    try:
        return _STORE
    except NameError:
        _STORE = PostgresMemoryStore()
        return _STORE

_PKG = resources.files("knowlyx.web")
TEMPLATES = Jinja2Templates(directory=str(Path(str(_PKG / "templates"))))

app = FastAPI(title="knowai dashboard")
app.mount("/static", StaticFiles(directory=str(Path(str(_PKG / "static")))), name="static")


def _pool():
    """Reuse the store's connection pool for read queries."""
    return _store()._pool


def _fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    with _pool().connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def _fetch_one(sql: str, params: tuple = ()) -> dict | None:
    rows = _fetch_all(sql, params)
    return rows[0] if rows else None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    stats = _fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM memory_entries WHERE superseded_by IS NULL) AS active_entries,
            (SELECT COUNT(*) FROM memory_entries WHERE superseded_by IS NOT NULL) AS superseded_entries,
            (SELECT COUNT(*) FROM memory_entries WHERE approved) AS approved_entries,
            (SELECT COUNT(*) FROM memory_syntheses) AS syntheses,
            (SELECT COUNT(*) FROM memory_syntheses WHERE stale) AS stale_syntheses,
            (SELECT COUNT(*) FROM memory_audit_log WHERE at > now() - interval '24 hours') AS audit_24h,
            (SELECT COUNT(*) FROM memory_audit_log WHERE action = 'merge') AS merges
        """,
    ) or {}

    by_domain = _fetch_all(
        """
        SELECT domain, COUNT(*) AS n
        FROM memory_entries
        WHERE superseded_by IS NULL
        GROUP BY domain
        ORDER BY n DESC
        LIMIT 10
        """,
    )

    by_kind = _fetch_all(
        """
        SELECT kind::text AS kind, COUNT(*) AS n
        FROM memory_entries
        WHERE superseded_by IS NULL
        GROUP BY kind
        ORDER BY n DESC
        """,
    )

    recent_activity = _fetch_all(
        """
        SELECT a.at, a.action, a.actor, a.entry_id, e.title, e.domain
        FROM memory_audit_log a
        LEFT JOIN memory_entries e ON e.id = a.entry_id
        ORDER BY a.at DESC
        LIMIT 15
        """,
    )

    return TEMPLATES.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "by_domain": by_domain,
            "by_kind": by_kind,
            "recent_activity": recent_activity,
            "active": "dashboard",
        },
    )


@app.get("/entries", response_class=HTMLResponse)
def entries(
    request: Request,
    domain: str = Query("", alias="domain"),
    kind: str = Query("", alias="kind"),
    q: str = Query("", alias="q"),
    show_superseded: bool = Query(False),
):
    where = []
    params: list = []
    if not show_superseded:
        where.append("superseded_by IS NULL")
    if domain:
        where.append("domain = %s")
        params.append(domain)
    if kind:
        where.append("kind = %s::memory_kind")
        params.append(kind)
    if q:
        where.append("search_tsv @@ plainto_tsquery('simple', %s)")
        params.append(q)
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    rows = _fetch_all(
        f"""
        SELECT id, kind::text AS kind, domain, title,
               approved, repo_path, created_at, updated_at,
               superseded_by, COALESCE((metadata->>'merge_count')::int, 0) AS merge_count
        FROM memory_entries
        {where_sql}
        ORDER BY updated_at DESC
        LIMIT 200
        """,
        tuple(params),
    )

    domains = [r["domain"] for r in _fetch_all(
        "SELECT DISTINCT domain FROM memory_entries ORDER BY domain"
    )]

    return TEMPLATES.TemplateResponse(
        "entries.html",
        {
            "request": request,
            "rows": rows,
            "domains": domains,
            "filter_domain": domain,
            "filter_kind": kind,
            "filter_q": q,
            "show_superseded": show_superseded,
            "active": "entries",
        },
    )


@app.get("/entries/{entry_id}", response_class=HTMLResponse)
def entry_detail(request: Request, entry_id: str):
    entry = _fetch_one(
        """
        SELECT id, kind::text AS kind, domain, title, body, tags,
               approved, approved_by, repo_path, metadata,
               created_at, updated_at, superseded_by, superseded_at
        FROM memory_entries
        WHERE id = %s
        """,
        (entry_id,),
    )
    audit = _fetch_all(
        "SELECT at, action, actor, diff FROM memory_audit_log WHERE entry_id = %s ORDER BY at DESC",
        (entry_id,),
    )
    return TEMPLATES.TemplateResponse(
        "entry_detail.html",
        {"request": request, "entry": entry, "audit": audit, "active": "entries"},
    )


@app.get("/syntheses", response_class=HTMLResponse)
def syntheses(request: Request):
    rows = _fetch_all(
        """
        SELECT s.domain, s.summary, s.key_themes, s.open_questions,
               s.synthesized_at, s.synthesized_by, s.entry_count_at_synthesis, s.stale,
               (SELECT COUNT(*) FROM memory_entries WHERE domain = s.domain AND superseded_by IS NULL) AS current_entries
        FROM memory_syntheses s
        ORDER BY s.stale DESC, s.synthesized_at DESC
        """,
    )
    return TEMPLATES.TemplateResponse(
        "syntheses.html",
        {"request": request, "rows": rows, "active": "syntheses"},
    )


@app.get("/audit", response_class=HTMLResponse)
def audit(
    request: Request,
    action: str = Query("", alias="action"),
    limit: int = Query(100, ge=1, le=500),
):
    where = []
    params: list = []
    if action:
        where.append("a.action = %s")
        params.append(action)
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    params.append(limit)

    rows = _fetch_all(
        f"""
        SELECT a.id, a.at, a.action, a.actor, a.entry_id, a.diff,
               e.title, e.domain
        FROM memory_audit_log a
        LEFT JOIN memory_entries e ON e.id = a.entry_id
        {where_sql}
        ORDER BY a.at DESC
        LIMIT %s
        """,
        tuple(params),
    )
    actions = ["insert", "update", "delete", "supersede", "approve", "merge"]
    return TEMPLATES.TemplateResponse(
        "audit.html",
        {
            "request": request,
            "rows": rows,
            "actions": actions,
            "filter_action": action,
            "limit": limit,
            "active": "audit",
        },
    )


# ---------------------------------------------------------------------------
# Team knowledge management — create / edit / approve / delete
# ---------------------------------------------------------------------------


def _author_from(request: Request, fallback: str = "") -> str:
    """Identity from sticky cookie set by /me. Fallback to form field or 'web'."""
    return request.cookies.get("knowai_author") or fallback or "web"


@app.get("/knowledge", response_class=HTMLResponse)
def knowledge(request: Request, domain: str = Query("")):
    """Team workspace: prominently shows the 'add knowledge' form + recent team entries."""
    clauses = ["superseded_by IS NULL"]
    params: list = []
    if domain:
        clauses.append("domain = %s")
        params.append(domain)
    where_sql = "WHERE " + " AND ".join(clauses)
    recent = _fetch_all(
        f"""
        SELECT id, kind::text AS kind, domain, title, approved, approved_by,
               updated_at, COALESCE((metadata->>'merge_count')::int, 0) AS merge_count
        FROM memory_entries
        {where_sql}
        ORDER BY updated_at DESC
        LIMIT 30
        """,
        tuple(params),
    )
    domains = [r["domain"] for r in _fetch_all(
        "SELECT DISTINCT domain FROM memory_entries ORDER BY domain"
    )]
    return TEMPLATES.TemplateResponse(
        "knowledge.html",
        {
            "request": request,
            "kinds": KINDS,
            "domains": domains,
            "filter_domain": domain,
            "recent": recent,
            "author": request.cookies.get("knowai_author", ""),
            "active": "knowledge",
        },
    )


@app.post("/knowledge/create")
def knowledge_create(
    request: Request,
    kind: str = Form(...),
    domain: str = Form(...),
    title: str = Form(...),
    body: str = Form(...),
    tags: str = Form(""),
    approved_by: str = Form(""),
    auto_approve: bool = Form(False),
):
    entry = MemoryEntry(
        id="",
        kind=MemoryKind(kind),
        domain=domain.strip(),
        title=title.strip(),
        body=body,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
        approved=bool(auto_approve),
        approved_by=_author_from(request, approved_by),
        repo_path="",
    )
    saved = _store().save(entry)
    return RedirectResponse(url=f"/entries/{saved.id}", status_code=303)


@app.post("/entries/{entry_id}/approve")
def entry_approve(request: Request, entry_id: str, approver: str = Form("")):
    actor = _author_from(request, approver)
    with _pool().connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE memory_entries SET approved = TRUE, approved_by = %s WHERE id = %s AND NOT approved",
            (actor, entry_id),
        )
        if cur.rowcount:
            cur.execute(
                "INSERT INTO memory_audit_log (entry_id, action, actor) VALUES (%s, 'approve', %s)",
                (entry_id, actor),
            )
    return RedirectResponse(url=f"/entries/{entry_id}", status_code=303)


@app.post("/entries/{entry_id}/delete")
def entry_delete(entry_id: str):
    _store().delete(entry_id)
    return RedirectResponse(url="/entries", status_code=303)


@app.get("/entries/{entry_id}/edit", response_class=HTMLResponse)
def entry_edit_form(request: Request, entry_id: str):
    entry = _fetch_one(
        "SELECT id, kind::text AS kind, domain, title, body, tags, approved, approved_by FROM memory_entries WHERE id = %s",
        (entry_id,),
    )
    return TEMPLATES.TemplateResponse(
        "entry_edit.html",
        {"request": request, "entry": entry, "kinds": KINDS, "active": "entries"},
    )


@app.post("/entries/{entry_id}/edit")
def entry_edit_submit(
    request: Request,
    entry_id: str,
    title: str = Form(...),
    body: str = Form(...),
    tags: str = Form(""),
    editor: str = Form(""),
):
    actor = _author_from(request, editor)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    with _pool().connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE memory_entries SET title = %s, body = %s, tags = %s WHERE id = %s",
            (title.strip(), body, tag_list, entry_id),
        )
        if cur.rowcount:
            cur.execute(
                "INSERT INTO memory_audit_log (entry_id, action, actor, diff) VALUES (%s, 'update', %s, %s::jsonb)",
                (entry_id, actor, '{"source":"web-edit"}'),
            )
    return RedirectResponse(url=f"/entries/{entry_id}", status_code=303)


@app.post("/me")
def set_author(name: str = Form(...)):
    """Sticky cookie so a team member doesn't retype their name on every form."""
    resp = RedirectResponse(url="/knowledge", status_code=303)
    resp.set_cookie("knowai_author", name.strip()[:64], max_age=60 * 60 * 24 * 365)
    return resp


@app.get("/healthz")
def healthz():
    try:
        with _pool().connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
