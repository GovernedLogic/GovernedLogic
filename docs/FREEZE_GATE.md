# Freeze Gate: standing process for governedlogic.com

Adopted: 2026-10-25 20:10:00 EDT (Governor, at Paul's instruction)
Applies to: every change to governedlogic.com from this point on, for the Developer, Architect, QA and Governor.
In-flight work: #25, #27, #30 and #31 were gated before adoption and are not re-gated.

Paul's instruction (2026-10-25 20:09 EDT, verbatim): "Implement the freeze gate as the team's standing process for the governedlogic.com project: before any code gets written, the requirement must be locked and signed off (by Paul or the designated approver), and if a requirement moves after that point, the change goes through a documented change request rather than silently rewriting the target."

## Rule 1: No code before the lock

No branch, commit or PR for a change until its requirement is LOCKED. A requirement is LOCKED when:

1. The Governor has written a Requirement Lock (template below) in the PR body, or in the tracking issue if there is no PR yet.
2. Paul, or an approver Paul has designated in his own words, has signed it off. The sign-off is quoted verbatim in the lock with a timestamp.

Designated approvers: none as of 2026-10-25 20:10 EDT. Only Paul's own words can add one, and they are recorded here verbatim.

Exploratory prototypes for creative work (Paul's build-first rule for visuals and animation) are allowed on a branch marked PROTOTYPE. A prototype never merges. Its result becomes the Requirement Lock, which Paul signs off before production code is written.

## Rule 2: Requirement Lock template

```
REQUIREMENT LOCK  RL-<PR or issue number>-<n>
Locked: YYYY-MM-DD HH:MM:SS EDT   Author: Governor
Goal: <one sentence>
Scope (files/areas in): ...
Out of scope: ...
Expected visible text diff: <exact strings added/removed, or "none">
Viewports and states to check: 1440, 390, 320 (+ any others)
Acceptance checks (2-3 specific to this change, plus the permanent gates): ...
Sign-off: "<approver's exact words>" (approver, YYYY-MM-DD HH:MM EDT)
```

## Rule 3: Moving a locked requirement requires a Change Request

After the lock, nobody (Governor included) rewrites the target in place, in chat, or by reinterpretation. Any change in scope, wording, layout target or acceptance is a Change Request, added under the lock:

```
CHANGE REQUEST  CR-<lock id>-<n>
Raised: YYYY-MM-DD HH:MM:SS EDT   By: <role>
What changes: <before> -> <after>
Why: ...
Impact: files, text diff, checks, schedule
Sign-off: "<approver's exact words>" (approver, YYYY-MM-DD HH:MM EDT)
```

Until a CR is signed off, the original lock governs. Work toward the new target stops. A CR is signed off only by Paul or a designated approver. A QA or Architect finding that needs no change to the target (a bug against the lock) is a fix, not a CR.

## Rule 4: Who does what

- Governor: writes the lock and any CRs, gets sign-off, and records it verbatim. The Governor is the only one who rules. It never changes a target without a CR.
- Developer: does not start until the lock shows sign-off. Builds only to the lock. Checks their own 1440 and 390 screenshots against it before handing off. Raises a CR instead of drifting.
- Architect: reviews against the lock and its CRs, not against relayed messages. Raises a CR when the lock itself is wrong.
- QA: gates against the lock's expected text diff, viewports and checks, plus the permanent gates. A PR with no signed-off lock, or with a change that has no signed-off CR, FAILS QA.
- Harriet: merges only PRs that carry a signed-off lock and a QA PASS.

## Rule 5: Evidence

Each PR body links its lock and every CR. PROJECT_STATE.txt lists only the lock id and status for each open PR.
