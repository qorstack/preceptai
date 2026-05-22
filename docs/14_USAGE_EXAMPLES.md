# 14 — Real-world Usage Examples

7 scenarios ที่เจอบ่อยจริง — แต่ละอันมี: situation, ปกติทำยังไง (เจ็บ), ใช้ Knowlyx ทำยังไง (หาย)

## Scenario 1: Junior dev ใหม่เข้าทีม

**Situation:** Junior เพิ่ง clone repo backend ของบริษัท 80k LOC

**ปกติ:**
- ใช้เวลา 1-2 สัปดาห์อ่านโค้ด
- ถาม senior 30 ครั้ง/วัน
- ทำ PR แรก → review 2 รอบเพราะ miss convention

**Knowlyx:**
```bash
$ knowlyx scan .

Architecture: clean_architecture
Domains: payment(critical), auth(critical), order, notification, webhook
Frameworks: FastAPI, SQLAlchemy, Alembic
Conventions: 18 detected
  - Controllers in src/api/, services in src/domain/
  - DB access only via repositories
  - All payment calls require idempotency key
Reusable assets: 67 (services: 12, utils: 28, schemas: 27)
Forbidden: direct httpx (use src/clients/), print() (use logger)
```

5 นาที → เห็น mental model พื้นฐาน

```bash
$ knowlyx graph mermaid --repo . > arch.md
$ knowlyx pack payment
```

→ entire onboarding ลดเหลือ 2-3 วัน

---

## Scenario 2: AI assistant ทำ feature ใหม่

**Situation:** PM บอก "เพิ่ม OTP login ใน web + api"

**ปกติ (without Knowlyx):**
- Cursor gen OTP module ใหม่
- ลืม rate limit
- ใช้ axios ตรง (มี generated client อยู่)
- ไม่มี audit log
- → review 3 รอบ, +2 วัน

**With Knowlyx (Claude Code + MCP):**

User พิมพ์ในchat: "เพิ่ม OTP login"

Claude flow:
```text
1. tool call: analyze_intent("เพิ่ม OTP login", "/path/to/repo")

   Report returned:
   - Intent: auth domain, action: add
   - Cognition pack `otp`:
     • expiry 5-10 min
     • single-use
     • max 3 retry → lockout 15 min
     • notification provider required
   - Conventions:
     • Use src/api/generated/ for HTTP calls
     • Add audit log via AuditService
   - Reusable assets:
     • OtpInput component (web/src/shared/components/)
     • RateLimiter middleware (api/src/middleware/)
   - Memory:
     • "Twilio primary, Infobip fallback" (approved 2026-03-12)
   - Risk: MEDIUM → WARN

2. Claude writes:
   - api: OtpService using RateLimiter + Twilio client
   - web: form using OtpInput component + generated SwaggerClient.requestOtp
   - audit logs at every step
   - test: unit + integration
```

→ First-try correct, 30 นาที, review 1 รอบผ่าน

---

## Scenario 3: Backend แก้ DTO กระทบหลาย repo

**Situation:** "เปลี่ยน PaymentDTO.amount จาก int → decimal"

**ปกติ:**
- Backend แก้, deploy
- 30 นาทีต่อมา worker ตาย (deserialize error)
- 1 ชม.ต่อมา admin chart พัง
- Slack ระเบิด, rollback

**With Knowlyx:**

```bash
$ knowlyx workspace impact api --change "PaymentDTO.amount int→decimal"

Cascade affected:
  ⚠️ worker (jobs/payment_retry.py)
  ⚠️ web (regenerate swagger client)
  ⚠️ admin (ChartJS amount parser)

Risk: HIGH → submit approval

Actions required (in order):
  1. Update api DTO + migration
  2. Regenerate Swagger
  3. Update worker schema
  4. Update admin parser
  5. Deploy: api → worker → web/admin
```

Submit approval queue → tech lead approve → execute ตามลำดับ → zero incident

---

## Scenario 4: Tech lead บันทึก decision หลัง incident

**Situation:** Incident webhook ทำงานซ้ำ → ตัดสินใจ "ทุก webhook ต้องมี event_id check"

**ปกติ:**
- Post ใน Slack channel #engineering
- เขียนใน Notion (ไม่มีใครอ่าน)
- 3 เดือนต่อมา dev ใหม่เขียน webhook → ทำซ้ำเดิม

**With Knowlyx:**

```bash
$ knowlyx memory decide webhook \
    "Event ID idempotency required" \
    --body "ทุก webhook handler ต้องเช็ค event_id duplicate ก่อน process (incident 2026-04-15 ปัญหา Stripe retry ทำให้ charge ซ้ำ 47 cases)" \
    --repo /workspace/api
```

3 เดือนต่อมา dev ใหม่ขอ AI เพิ่ม webhook → `analyze_intent` → cognition report inject memory entry นี้อัตโนมัติ → AI gen code ที่ check idempotency → zero ซ้ำ incident

---

## Scenario 5: AI พยายามทำของอันตราย

**Situation:** Dev ขอ "rewrite auth middleware ให้ใช้ JWT แทน session"

**ปกติ:**
- AI gen code, dev commit, deploy
- Production: ทุก user ถูก logout
- 200 support tickets/ชั่วโมง

**With Knowlyx:**

```text
analyze_intent("rewrite auth middleware ให้ใช้ JWT แทน session")
  → Risk: CRITICAL
  → Decision: ASK
  → Reasons:
    - Critical domain: auth
    - Touches: 12 endpoints, all middleware
    - Breaking change: existing sessions invalidated
    - Memory entry: "Session-based intentional choice 2025-10 due to PCI scope reduction"

  → request_approval(...) auto-submitted

[AI tells user]
"⛔ CRITICAL change blocked. ดูเหตุผล:
- Auth domain (critical)
- จะ logout users ที่มี session อยู่
- เคยมี decision (2025-10) เลือก session intentional เพราะ PCI

Submitted approval queue. ต้องคุยกับ tech lead ก่อน"
```

→ Dev ไปคุย → realize เหตุผลเดิมยังใช้อยู่ → ไม่ทำ → ประหยัด disaster

---

## Scenario 6: Onboarding repo ใหม่เข้า workspace

**Situation:** บริษัท acquire startup → ต้อง integrate codebase

**Knowlyx:**

```bash
$ cd /workspace
$ knowlyx workspace init
  → detected: api/, web/, worker/, acquired-startup/
  → generated knowlyx.toml

$ vim knowlyx.toml
# เพิ่ม [[dependencies]] ที่ knowlyx ไม่ detect

$ knowlyx workspace scan
  → 4 repos scanned in 12s

$ knowlyx workspace graph mermaid > arch.md
$ knowlyx workspace impact acquired-startup --change "deprecate /v1 endpoints"
  → ไม่มีอะไรกระทบ (good — independent)
```

หัวหน้าฝ่าย integration เห็น context ภายในวันเดียว

---

## Scenario 7: AI self-review (Phase 4 — planned)

**Situation:** AI เพิ่ง gen `PaymentBox.tsx` ใหม่

**With Knowlyx Phase 4:**

```text
[Before writing file]
validate_generated_code(<PaymentBox code>, "/path/to/web", "typescript")

Violations:
  ❌ Duplicate of existing PaymentCard.tsx (95% similar)
     → suggestion: import { PaymentCard } from '@/components/payment'
  ❌ Uses arbitrary spacing p-[18px] (not in scale 4/8/16/24)
     → suggestion: use p-4 or p-6
  ⚠️ Direct axios.get('/api/...')
     → suggestion: use SwaggerClient.payment.getStatus()
  ❌ Missing dark mode classes
     → suggestion: add dark: variants for bg, text

Status: BLOCKED — fix violations before write
```

→ AI fix แล้ว validate ใหม่ → pass → write file → first PR ผ่าน

---

## สรุป pain → gain

| Pain (without) | Gain (with Knowlyx) |
|---|---|
| Onboarding 2 สัปดาห์ | 2 วัน |
| AI gen ผิด review 3 รอบ | first-try correct |
| Production incident จาก miss impact | block ก่อน deploy |
| Decision หายในประวัติ Slack | persistent + auto-inject |
| AI ทำของอันตราย | hard gate ผ่าน approval |
| Integration repo ใหม่ chaotic | structured workflow |
| AI gen duplicate code | self-review block |
