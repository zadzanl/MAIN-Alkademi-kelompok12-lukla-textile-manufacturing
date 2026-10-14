# Implementation Plan: Install Apple Design Skill

## Metadata
- **Change Name:** `install-apple-design-skill`
- **Scope:** Workspace Skill Provisioning
- **Target Repository:** `c:\Projects\hackathon-MAIN-alkademi`
- **Source Specification:** [emilkowalski/skills: skills/apple-design/SKILL.md](https://raw.githubusercontent.com/emilkowalski/skills/main/skills/apple-design/SKILL.md)

---

## 1. Executive Summary & Intent
The objective is to install Emil Kowalski's `apple-design` skill into this repository workspace as an Antigravity-discoverable skill under `.agents/skills/apple-design/SKILL.md`. This equips pair-programming AI agents working in this repository with Apple Human Interface Guidelines and fluid motion physics (spring dynamics, interruptibility, 1:1 tracking, velocity projection) without adding any runtime dependencies or altering application source code.

---

## 2. Target Files & Schemas

### Target File
- **Path:** `c:\Projects\hackathon-MAIN-alkademi\.agents\skills\apple-design\SKILL.md`
- **Action:** Create new file (and parent directory `.agents/skills/apple-design/`) [doc: file:///C:/Users/lenovo/.gemini/antigravity/builtin/skills/agy-customizations/docs/skills.md#L9-L19]

### Schema / Frontmatter Specification
```yaml
---
name: apple-design
description: Apple's approach to interface design and fluid, physical motion, translated for the web. Use when building or reviewing gesture-driven UI, spring animations, drag/swipe/sheet interactions, momentum and interruptible transitions, translucent materials and depth, typography (optical sizing, tracking, leading), reduced-motion, or the design foundations (feedback, spatial consistency, restraint) behind Apple-style interfaces.
---
```

### Full Skill Content Structure
- Frontmatter (`name`, `description`)
- Initial greeting prompt guard
- Core Philosophy (Safety, understanding, achievement, joy)
- 8 Fluid Motion Principles:
  1. Response — kill latency
  2. Direct manipulation — 1:1 tracking (`setPointerCapture`)
  3. Interruptibility — presentation values, velocity blending
  4. Behavior over animation — springs (damping `1.0` vs `0.8`, response)
  5. Velocity handoff — seamless release
  6. Momentum projection — exponential decay formula (`project(initialVelocity, decelerationRate)`)
  7. Spatial consistency — symmetric paths, anchored origins
  8. Hint in the direction of the gesture

---

## 3. Step-by-Step Implementation Procedure

### Step 1: Directory Provisioning
- Ensure directory `c:\Projects\hackathon-MAIN-alkademi\.agents\skills\apple-design` exists.
- Command: `New-Item -ItemType Directory -Path "c:\Projects\hackathon-MAIN-alkademi\.agents\skills\apple-design" -Force`

### Step 2: Vendoring SKILL.md
- Fetch complete raw content from upstream:
  `https://raw.githubusercontent.com/emilkowalski/skills/main/skills/apple-design/SKILL.md`
- Verify integrity (character count > 20,000, line count > 200).
- Write to `c:\Projects\hackathon-MAIN-alkademi\.agents\skills\apple-design\SKILL.md`.

### Step 3: Stop Condition Guard
- If anything differs from this brief, return `BLOCKED: <what differs> | <evidence> | <question>`; do not choose for the user and do not widen scope.

---

## 4. Edge Cases & Safeguards

| Edge Case | Risk | Mitigation |
| :--- | :--- | :--- |
| Truncated upstream fetch | Corrupt or incomplete skill definition | Verification gate requires line count >= 200 and file size >= 20KB before proceeding. |
| Non-existent parent folders | File write failure | Recursive directory creation via `-Force`. |
| Unsolicited UI / CSS churn | Scope explosion / broken build | Strict YAGNI guard: zero modifications to `src/`, `package.json`, or `.openspec/` beyond the plan artifact. |

---

## 5. Verification Commands

1. **Verify File Exists:**
   ```powershell
   Test-Path "c:\Projects\hackathon-MAIN-alkademi\.agents\skills\apple-design\SKILL.md"
   # Expected: True
   ```

2. **Verify YAML Frontmatter:**
   ```powershell
   Get-Content "c:\Projects\hackathon-MAIN-alkademi\.agents\skills\apple-design\SKILL.md" -Head 6
   # Expected: contains 'name: apple-design' and 'description: ...'
   ```

3. **Verify Integrity & Size:**
   ```powershell
   $lines = (Get-Content "c:\Projects\hackathon-MAIN-alkademi\.agents\skills\apple-design\SKILL.md" | Measure-Object -Line).Lines
   Write-Output "Lines: $lines"
   # Expected: Lines >= 200
   ```

