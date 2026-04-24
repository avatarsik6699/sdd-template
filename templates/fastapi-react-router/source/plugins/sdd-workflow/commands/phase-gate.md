---
description: Run the SDD gate checks for a phase. Usage: /phase-gate 01
---

# /phase-gate

Execute the canonical playbook: [workflow/docs/playbooks/phase-gate.md](../../../workflow/docs/playbooks/phase-gate.md). Resolve the active gate helper/docs pair with `sdd gate resolve`; `docs/STACK.md#gate-commands` remains the human-readable command source.

The matching skill lives at [skills/phase-gate/SKILL.md](../skills/phase-gate/SKILL.md).

Read-only. Do not edit code, do not commit. Return PASS only when automated checks are green and no unchecked architect review notes remain.
