# 07 — Reasoning Layer

📂 [src/knowlyx/reasoning/](../src/knowlyx/reasoning/)

**Rule-based pipeline ไม่ใช้ LLM** — deterministic, fast (<100ms), free

## Files

| File | Input → Output |
|---|---|
| `intent_analyzer.py` | request (str) → `IntentAnalysis` |
| `impact_analyzer.py` | `IntentAnalysis` → `ImpactAnalysis` |
| `risk_scorer.py` | intent + impact → `RiskAssessment` |
| `engine.py` | request → `CognitionReport` (รวมทุกอย่าง) |

## Pipeline

```text
"fix payment scan 501"
   │
   ▼ IntentAnalyzer
   ├─ domain: payment           (keyword match)
   ├─ action: fix               (verb)
   ├─ requirements: [error handling, retry, audit log]
   └─ clarification_questions: ["which payment provider?", ...]
   │
   ▼ ImpactAnalyzer
   ├─ affected_domains: [payment, webhook, audit, notification]
   ├─ affected_services: [payment-service, notification-worker]
   ├─ affected_files: [12 files matched]
   └─ cascade_risks: ["webhook retry storm", "duplicate notification"]
   │
   ▼ RiskScorer
   ├─ level: HIGH
   ├─ decision: ASK
   ├─ warnings: ["critical domain", "cross-service impact"]
   └─ workflow: [
       "1. reproduce in staging",
       "2. add idempotency key",
       "3. regression test on webhook",
       "4. notify on-call before deploy"
     ]
   │
   ▼ ReasoningEngine (combine everything)
   └─ CognitionReport
       ├─ intent, impact, risk
       ├─ plan
       ├─ reusable_assets       ← จาก Scanner
       ├─ conventions           ← จาก Scanner
       ├─ packs                 ← จาก Packs layer
       └─ memory                ← จาก Memory layer (approved only)
```

## Risk decisions

| Decision | ความหมาย | AI ทำอะไรต่อ |
|---|---|---|
| `proceed` | ปลอดภัย, generate ได้เลย | เขียน code |
| `warn` | ต้องระวัง, แต่ผ่านได้ | เขียน code + แสดง warning |
| `ask` | ต้องถาม human ก่อน | submit approval queue, รอ approve |
| `reject` | ห้ามทำ | หยุด, อธิบายเหตุผล, propose alternative |

**Binding:** AI ห้ามข้าม `ask`/`reject` — Knowlyx ไม่มี LLM override กลไกนี้

## Risk scoring rules (current)

```text
+ critical domain (auth/payment/billing)    : +3
+ cross-repo impact                          : +2
+ touches forbidden patterns                 : +2
+ DB schema change                           : +2
+ public API change                          : +2
+ no existing tests in affected area         : +1
+ deploys outside maintenance window         : +1
─────────────────────────────────────────────
0-1  → proceed
2-3  → warn
4-5  → ask
6+   → reject
```

(Phase 4: เปลี่ยนเป็น ML-based scoring จาก historical incident data)

## Real-world usage

```bash
# CLI
uv run knowlyx analyze "add OTP login" --repo /path/to/repo

# Output:
# Intent:
#   Domain: auth
#   Action: add
#   Inferred requirements:
#     - OTP expiration policy
#     - Single-use enforcement
#     - Max retry + lockout
#     - Notification provider selection
#
# Impact:
#   Affected domains: auth, user, notification, audit
#   Affected services: auth-service, notification-worker
#   Cascade risks: brute force, OTP reuse, SMS cost spike
#
# Risk: MEDIUM (4) → ASK
# Workflow:
#   1. Choose SMS provider (Twilio? Infobip?)
#   2. Define expiry (5 or 10 min?)
#   3. Implement rate limiting
#   4. Add audit logs
#   5. Integration test with mocked SMS
```

**Scenario จริง:** Junior dev ขอ AI "fix login bug"
- AI call `analyze_intent("fix login bug")` → ได้ risk: HIGH, decision: ASK
- AI ตอบ junior: "ก่อนแก้ ขอถาม: bug เกิดที่ขั้นไหน? login form? session validate? token refresh?"
- Junior คิดจริงจัง → realize ตัวเองยังไม่รู้ scope
- ไม่มี code change มั่ว → ประหยัด review time
