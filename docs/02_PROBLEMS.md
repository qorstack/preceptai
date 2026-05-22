# 02 — Problems Knowlyx Solves

7 ปัญหา core ที่ AI coding tools ปัจจุบันแก้ไม่ได้

## P1 — Business Understanding

**ปัญหา:** AI ไม่รู้ว่า "OTP login" ในบริษัทนี้ต้องมีอะไรบ้าง — expiry, retry policy, lockout, provider

**Knowlyx แก้:** Cognition Packs (built-in 7 domains) + Memory (team-specific)

**ตัวอย่าง:**
```text
Request: "เพิ่ม OTP login"
→ Pack `otp` inject: expiry 5-10min, single-use, max retry, lockout
→ Memory inject: "เราใช้ Twilio + fallback Infobip" (approved by team)
```

## P2 — Architecture Awareness

**ปัญหา:** AI เขียน `fetch('/api/...')` ทั้งที่บริษัทมี generated Swagger client

**Knowlyx แก้:** `ConventionDetector` ตรวจ architecture pattern + forbidden patterns

**ตัวอย่าง:**
```text
Detected:
- architecture: clean_architecture
- frontend must use: src/api/generated/
- forbidden: direct axios/fetch
- enforce: controller → service → repository
```

## P3 — UX/UI Pattern Cognition

**ปัญหา:** AI gen modal ที่ spacing, color, dark mode ไม่ตรงกับ design system ที่ใช้อยู่

**Knowlyx แก้:** Design cognition (Phase 4) — ตรวจ tailwind tokens, component patterns, spacing system

**ตัวอย่าง:**
```text
Detected:
- spacing scale: 4/8/16/24 (no arbitrary values)
- modal pattern: <Sheet> from shared/ui (not raw Dialog)
- dark mode: class-based via next-themes
```

## P4 — Reuse Awareness

**ปัญหา:** AI สร้าง `PaymentBox.tsx` ใหม่ทั้งที่มี `PaymentCard.tsx` อยู่แล้ว

**Knowlyx แก้:** `AssetDetector` + `get_reusable_assets(domain)`

**ตัวอย่าง:**
```text
Request: "add payment summary card"
→ assets[payment]:
  - PaymentCard.tsx (used in 8 places)
  - usePaymentStatus.ts (hook)
  - paymentFormatter.ts (util)
→ AI: "reuse PaymentCard instead of creating new"
```

## P5 — Impact Awareness

**ปัญหา:** AI แก้ DTO ใน api repo โดยไม่รู้ว่า worker repo + frontend repo consume

**Knowlyx แก้:** `ImpactAnalyzer` + cross-repo graph + cascade rules

**ตัวอย่าง:**
```text
Change: "เปลี่ยน PaymentDTO.amount จาก int → decimal"
→ Impact:
  - api/payment-service ✓
  - worker/payment-retry-job ⚠️ (deserialize fail)
  - web/checkout (Swagger client regen needed)
  - admin/dashboard (chart breaks)
→ Decision: ASK (cross-repo critical)
```

## P6 — AI Intent Safety

**ปัญหา:** AI run `DROP TABLE` หรือ delete migration โดยไม่ pause ให้ human ดูก่อน

**Knowlyx แก้:** `RiskScorer` + `ApprovalQueue` — decision: `proceed/warn/ask/reject`

**ตัวอย่าง:**
```text
Request: "rewrite auth middleware"
→ Risk: HIGH (touches auth + sessions + 12 dependent endpoints)
→ Decision: ASK
→ Knowlyx submit approval gate
→ AI poll until human approves
→ proceed only after approval
```

## P7 — Multi-Repo System Awareness

**ปัญหา:** บริษัทจริงมี api + web + worker + admin + mobile — AI เห็นแค่ repo เดียว

**Knowlyx แก้:** Workspace (`knowlyx.toml`) + cross-repo graph + inferred dependencies

**ตัวอย่าง:**
```text
Workspace: knowlyx.toml
→ scan: api, web, worker, admin (parallel)
→ inferred edges:
  - web → api (generated client detected)
  - worker → api (shared domain: payment)
  - admin → api (declared)
→ AI ถาม "fix payment scan 501" → ได้คำตอบครบทุก repo
```

## ปัญหาที่ Knowlyx ยังไม่แก้ (Phase 4+)

| Problem | ใคร solve อยู่บ้าง |
|---|---|
| Business conflict detection (feature ใหม่ขัด policy เก่า) | ❌ ยังไม่มีใครทำดี |
| Business evolution (track ว่า rule เปลี่ยนเมื่อไหร่ ทำไม) | ❌ |
| AI self-review ก่อน submit code | 🟡 บางตัวเริ่ม |
| Design system enforcement | ❌ |

→ นี่คือช่องว่างที่ Knowlyx ควรเป็น winner
