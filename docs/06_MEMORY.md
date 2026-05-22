# 06 — Memory Layer

📂 [src/knowlyx/memory/](../src/knowlyx/memory/)

Persistent memory ข้าม session — สำหรับเก็บ business context, team decisions, approved conventions

## 2 backends

### FileMemoryStore (default)
- เก็บเป็น JSON ใน `.knowlyx/memory.json` ภายใน project
- keyword scoring search
- zero dependency
- เหมาะ solo dev / small team

### QdrantMemoryStore (optional)
- ใช้ `qdrant-client` + `sentence-transformers` (all-MiniLM-L6-v2)
- semantic search (เข้าใจ synonym)
- install: `uv sync --extra vector`
- fallback ไป FileMemoryStore อัตโนมัติถ้า Qdrant unreachable
- เหมาะ team ขนาดกลาง-ใหญ่ที่ memory เยอะ

## Memory types

| Type | ตัวอย่าง |
|---|---|
| `business_context` | "ทุก payment ต้องมี idempotency key เพราะลูกค้าจ่ายซ้ำเดือนละ 50 case" |
| `approved_convention` | "ใช้ Twilio เป็น primary SMS, Infobip fallback" |
| `team_decision` | "เลิกใช้ Redis queue, ย้ายไป SQS หลัง 2026-Q1" |
| `reusable_asset` | "PaymentCard cover 90% cases — อย่าสร้างใหม่" |
| `risk_pattern` | "การ deploy webhook handler นอก maintenance window = incident" |
| `workflow` | "feature flag rollout: 5% → 25% → 100% over 1 week" |

## Human approval principle ⚠️ สำคัญ

```text
AI calls remember_business_context()
  → entry saved with approved=False
  → entry NOT injected into future analyses

Human runs: knowlyx memory approve <entry-id>
  → entry marked approved=True
  → entry NOW injected into analyze_intent reports
```

**ทำไม:** ป้องกัน AI ใส่ "ความรู้ผิด" เข้า system แล้วมั่วต่อไปเรื่อยๆ

ข้อยกเว้น: `remember_team_decision()` auto-approve (เพราะ human เป็นคนเรียก)

## API

```python
from knowlyx.memory import MemoryService

mem = MemoryService(repo_path="/path/to/repo")

# Save (AI flow)
entry_id = mem.save(
    type="business_context",
    domain="payment",
    title="Idempotency required",
    body="ทุก payment call ต้องมี idempotency key",
)

# Approve (human flow)
mem.approve(entry_id, approved_by="hello@maf.co.th")

# Recall (during analyze_intent)
results = mem.recall(query="payment idempotency", domain="payment")
```

## Real-world usage

```bash
# Solo dev → save แล้ว approve เอง
uv run knowlyx memory decide payment \
  "Idempotency keys required" \
  --body "ทุก payment call ต้องมี idempotency key เพราะลูกค้าจ่ายซ้ำ"

# List
uv run knowlyx memory list --repo .

# Search
uv run knowlyx memory recall "OTP expiry"

# Delete
uv run knowlyx memory forget <entry-id>
```

**Scenario จริง:** Tech lead ตัดสินใจหลัง incident
1. เกิด incident: webhook handler ทำงานซ้ำเพราะไม่มี idempotency
2. Lead post-mortem → ตัดสินใจ "ทุก webhook ต้องมี event_id check"
3. รัน `knowlyx memory decide webhook "Event ID idempotency" --body "..."`
4. สัปดาห์ต่อมา dev ใหม่ขอ AI เพิ่ม webhook handler
5. AI call `recall_context("webhook idempotency")` → ได้คำตอบทันที
6. AI gen code ถูก first try — ไม่ซ้ำ incident เดิม
