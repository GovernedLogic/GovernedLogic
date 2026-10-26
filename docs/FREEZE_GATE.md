# Freeze Gate: standing process for governedlogic.com

Adopted: 2026-10-25 20:10:00 EDT (Governor, at Paul's instruction)
Applies to: every change to governedlogic.com from this point on, for the Developer, Architect, QA and Governor.
In-flight work: #25, #27, #30 and #31 were gated before adoption and are not re-gated.

Paul's instruction (2026-10-25 20:09 EDT, verbatim): "Implement the freeze gate as the team's standing process for the governedlogic.com project: before any code gets written, the requirement must be locked and signed off (by Paul or the designated approver), and if a requirement moves after that point, the change goes through a documented change request rather than silently rewriting the target."

## Rule 1: No code before the lock

No branch, commit or PR for a change until its requirement is LOCKED. A requirement is LOCKED when:

1. The Governor has written a Requirement Lock (template below) in the PR body, or in the tracking issue if there is no PR yet.
2. Harriet (the designated decision-maker) or Paul has signed it off. The sign-off is quoted verbatim in the lock, with a timestamp and where it was said (whose chat or file, plus a message or comment id if there is one), so it can be checked rather than just relayed.

Open questions: when a requirement depends on an open question, the Governor writes it into PROJECT_STATE.txt for Harriet. Harriet decides it by reasoning it through with governed logic, and her decision becomes the signed lock. No branch, commit or PR proceeds on an open question until Harriet has decided it and the lock is signed.

Designated approver: Harriet. Paul's words (2026-10-25 20:14 EDT, verbatim, in Governor's chat): "Update PROJECT_STATE.txt to make Harriet's role explicit as the decision-maker for the governedlogic.com project: she is the brains and the decision-maker, and she reasons through any open question using governed logic. Her decisions land as signed requirement locks under the freeze gate — no branch, commit, or pull request proceeds on an open question until Harriet has decided it and the lock is signed. The Governor remains the single point of communication with Harriet through the state file; the Architect, Developer, and QA report to the Governor, not to Harriet directly." Only Paul's own words can add or remove an approver.

Exploratory prototypes for creative work (Paul's build-first rule for visuals and animation) are allowed on a branch marked PROTOTYPE. A prototype never merges. Its result becomes the Requirement Lock, which Paul signs off before production code is written.

## Rule 2: Requirement Lock template

```
REQUIREMENT LOCK  RL-<PR or issue number>-<n>
Locked: YYYY-MM-DD HH:MM:SS EDT   Author: Governor
Goal: <one sentence>
Scope (files/areas in): ...
Out of scope: ...
Expected visible text diff: <exact strings added/removed, or "none">
Expected attribute diff: <aria-label, alt, title changes, or "none">
Expected machine-layer diff: <sitemap, JSON-LD, llms.txt, robots, manifest, or "none">
Viewports and states to check: 1440, 390, 320 (+ any others)
Acceptance checks (2-3 specific to this change, plus the permanent gates): ...
Sign-off: "<approver's exact words>" (approver, YYYY-MM-DD HH:MM EDT, where said)
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

Until a CR is signed off, the original lock governs. Work toward the new target stops. A CR is signed off only by Harriet or Paul. A QA or Architect finding that needs no change to the target (a bug against the lock) is a fix, not a CR.

## Rule 4: Who does what

- Harriet: decides open questions with governed logic and signs locks and CRs. Merges only PRs that carry a signed-off lock and a QA PASS.
- Governor: the single point of communication with Harriet, through PROJECT_STATE.txt. Drafts each lock and CR, puts it to Harriet, records her sign-off verbatim, and relays it. It never changes a target without a CR.
- The Architect, Developer and QA report to the Governor, not to Harriet directly.
- Developer: does not start until the lock shows sign-off. Builds only to the lock. Checks their own 1440 and 390 screenshots against it before handing off. Raises a CR instead of drifting.
- Architect: reviews against the lock and its CRs, not against relayed messages. Raises a CR when the lock itself is wrong.
- QA: gates against the lock's expected text diff, viewports and checks, plus the permanent gates. A PR with no signed-off lock, or with a change that has no signed-off CR, FAILS QA.

## Rule 5: Evidence

Each PR body links its lock and every CR. QA stays verify-only: it never comments on, commits to, pushes or merges PRs. QA sends its verdict to the Governor headed "QA VERDICT: PASS" or "QA VERDICT: FAIL", with the head SHA, the Validate run and its report path, and the Governor posts it verbatim as a PR comment. PROJECT_STATE.txt lists only the lock id and status for each open PR.

## Rule 6: Permanent gates (QA, every PR)

- CNAME blob b009e8da unchanged (automatic FAIL).
- Build succeeds with the expected path and page counts.
- check-restored --artifact, guards, check-corpus and check-origin pass; Validate green.
- Full visible-text and attribute diff against main matches the lock.
- Zero <a> elements sitewide (once #31 is on main).
- Screenshots at 1440, 390 and 320.
- After deploy: deploy job success via the jobs API, Pages serving the merge SHA, live byte-identical to the build, withheld paths return 404.

## Rule 7: Live breakage (hotfix)

When the live site breaks against an existing signed lock (as with #29), restoring the locked behavior is a fix, not a new requirement. The Governor writes a one-line hotfix lock citing the existing lock and records it in PROJECT_STATE.txt. The fix proceeds at once and still needs a QA PASS before merge. A hotfix that changes any requirement needs a signed CR.
