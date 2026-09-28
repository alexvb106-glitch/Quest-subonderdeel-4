---
description: Start de planningsfase voor een backlog-slice (subagent planner)
argument-hint: [slice-id]
---

Roep de planner-subagent aan voor slice $ARGUMENTS.

De planner leest de sliceomschrijving uit docs/Backlog.md plus relevante context uit docs/Architecture.md, docs/Interfaces.md en docs/Design.md, en schrijft een planbestand naar .claude/plans/$ARGUMENTS.md met status: draft.

Als de slice niet bestaat in docs/Backlog.md, of een keuze vereist die nog `[OPEN]` staat, stopt de planner en meldt dit in plaats van te gokken.
