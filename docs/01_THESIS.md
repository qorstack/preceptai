# 01 — Product Thesis

## Two sentences ที่เป็นแกน

> **AI should not touch code before understanding the system.**
>
> **Knowledge is passive. Cognition must be enforced.**

ทุก feature ทุก decision ต้องสอบผ่าน 2 ประโยคนี้ — ถ้าไม่ผ่านคือไม่ใช่ Knowlyx

## What Knowlyx IS NOT

❌ AI coding assistant (Cursor/Copilot/Cline ทำดีกว่าแล้ว)
❌ Documentation generator
❌ Code search tool
❌ Linter
❌ Memory store เฉยๆ

## What Knowlyx IS

✅ **Enforcement layer** ที่ AI agents ต้องผ่านก่อนเขียน code
✅ **System cognition runtime** ที่ตอบคำถามแทน human ว่า "ระบบนี้ทำงานยังไง, ทำไม, ถ้าแก้แล้วกระทบไหน"
✅ **Decision gate** สำหรับ high-risk changes

## Why this matters

AI tools ปัจจุบันมี 3 อาการ:

1. **Generate ซ้ำของที่มีอยู่แล้ว** — เพราะไม่รู้ว่ามี `PaymentCard` component อยู่ ก็สร้าง `PaymentBox` ใหม่
2. **ละเมิด architecture conventions** — เพราะอ่าน CLAUDE.md ไม่ครบ ก็เขียน `fetch()` ตรงๆ แทนที่จะใช้ generated Swagger client
3. **Miss cross-repo impact** — แก้ `api` repo โดยไม่รู้ว่า `worker` repo consume DTO เดียวกัน

Knowlyx แก้ทั้ง 3 ข้อด้วยการ **บังคับ AI ให้ call MCP tools ก่อน** ไม่ใช่หวังว่า AI จะอ่าน markdown

## Core insight

AI ไม่ต้องการ **perfect memory** หรือ **full context**

AI ต้องการ **system intuition** แบบ senior engineer:
- "เออ feature นี้น่าจะเกี่ยวกับ payment domain"
- "payment เกี่ยว webhook + audit + notification"
- "มี shared `PaymentCard` แล้วนะ"
- "เปลี่ยนตรงนี้อาจกระทบ worker"

→ Knowlyx ให้ intuition นี้แบบ structured ผ่าน MCP

## Differentiator vs ตลาด

| Tool | Approach |
|---|---|
| AgentMemory / ctx0 / MemLayer | Persistent memory layer |
| Aictx | Repo context layer |
| **Knowlyx** | **Enforced cognition pipeline** (memory + reasoning + impact + risk + workflow) |

ตลาดส่วนใหญ่ solve "memory"
Knowlyx solve **"cognition + enforcement"** — ยังไม่มีใครทำดีจริง

## Real-world usage

**Scenario:** Dev บอก AI "เพิ่ม OTP login"

| Without Knowlyx | With Knowlyx |
|---|---|
| AI grep "auth" → เขียน OTP module ใหม่ | AI call `analyze_intent("เพิ่ม OTP login")` |
| ลืม rate limit | ได้ cognition pack `otp` → expiry, single-use, max retry, lockout |
| ใช้ axios ตรงๆ | ได้ conventions → ต้องใช้ generated client |
| ไม่รู้ว่ามี `OtpInput` component | ได้ reusable assets → reuse `OtpInput` |
| ไม่รู้ว่าต้อง notify ทาง SMS provider เจ้าไหน | ได้ memory → "บริษัทใช้ Twilio, fallback Infobip" |

→ จาก "AI เขียน OTP ผิด → human review 30 นาที" เหลือ "AI เขียนถูก first try"
