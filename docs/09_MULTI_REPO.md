# 09 — Multi-Repo Workspace

📂 [src/knowlyx/workspace/](../src/knowlyx/workspace/)

โปรเจกต์จริงไม่ใช่ repo เดียว — มี api + web + worker + admin + mobile
Knowlyx ต้องเห็นทั้งหมดและรู้ว่าใครคุยกับใคร

## knowlyx.toml

วางที่ root ของ workspace (โฟลเดอร์ที่ครอบทุก repo):

```toml
name = "my-product"

[[repos]]
name = "api"
path = "./api"
role = "backend"
domains = ["payment", "auth", "user"]
critical = true

[[repos]]
name = "web"
path = "./web"
role = "frontend"

[[repos]]
name = "worker"
path = "./worker"
role = "worker"
domains = ["payment", "notification"]

[[repos]]
name = "admin"
path = "./admin"
role = "frontend"

[[dependencies]]
from = "web"
to = "api"
type = "api"

[[dependencies]]
from = "worker"
to = "api"
type = "event"

[[dependencies]]
from = "admin"
to = "api"
type = "api"
```

## WorkspaceScanner

Scan ทุก repo **parallel** → build cross-repo NetworkX graph

**Inferred edges อัตโนมัติ:**
- Frontend ที่มี generated API client (เจอ `src/api/generated/`) → backend
- Worker ที่ share domain กับ source repo → source repo
- Declared dependencies จาก `knowlyx.toml`

## CrossRepoImpactAnalyzer

Input: `changed_repo + change description`
Output: รายการ repo ที่กระทบ + criticality

```python
analyzer.analyze(
    changed_repo="api",
    change="เปลี่ยน PaymentDTO.amount จาก int → decimal"
)
# →
# {
#   "directly_affected": ["api"],
#   "cascade_affected": ["web", "worker", "admin"],
#   "critical_repos_affected": ["api"],
#   "actions_required": [
#     "regenerate Swagger client in web",
#     "update worker deserialization",
#     "test admin payment charts"
#   ]
# }
```

## CLI

```bash
# Init knowlyx.toml อัตโนมัติ (Phase 4 — ยังไม่มี)
knowlyx workspace init

# Scan ทุก repo
knowlyx workspace scan

# Cross-repo impact
knowlyx workspace impact api --change "fix payment DTO"

# Graph
knowlyx workspace graph
knowlyx workspace graph react_flow --json
knowlyx workspace graph mermaid
```

## MCP tools

| Tool | use |
|---|---|
| `get_workspace_context(workspace_path)` | overview ทุก repo |
| `get_cross_repo_impact(changed_repo, change, workspace_path)` | blast radius |
| `export_graph("react_flow", workspace_path=...)` | visualize |

## Real-world usage

**Scenario:** Backend dev จะแก้ DTO

```bash
$ knowlyx workspace impact api --change "change PaymentDTO.amount int→decimal"

Workspace: my-product
Changed repo: api (CRITICAL)

Directly affected:
  - api/src/payment/dto.py
  - api/src/payment/service.py

Cascade affected:
  ⚠️ web (consumer via generated client)
    → must regenerate: npm run gen:api
    → must test: src/checkout/, src/refund/
  ⚠️ worker (consumer via event payload)
    → must update: jobs/payment_retry.py deserialization
    → fields touched: amount

  ℹ️ admin (consumer)
    → ChartJS payment dashboard uses amount as int — will break

Actions required:
  1. Update api DTO + migration
  2. Regenerate Swagger spec
  3. Update worker schema
  4. Update admin chart parser
  5. Deploy in order: api → worker → web/admin

Risk: HIGH → recommend approval queue
```

→ ก่อน Knowlyx: dev ลืม update worker → production crash 2 ชม.
→ หลัง Knowlyx: เห็นชัดก่อนเริ่ม
