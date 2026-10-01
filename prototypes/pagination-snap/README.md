# Five-door pagination prototype

Status: isolated prototype only; not promoted to production.

## What this tests

A web-native horizontal strip for the five existing primary destinations:

1. Governed Logic
2. On the Nature of Ultimate Grounding
3. Governed Intelligence
4. The Company
5. Research

The prototype changes presentation only. Every door remains an ordinary anchor to the existing canonical URL.

## Interaction evaluation

- **Mobile touch:** strong fit. Native horizontal pan plus `scroll-snap-type: x mandatory` gives a clear chapter-by-chapter gesture. The next card remains partially implied by the horizontal strip rather than hiding navigation behind app chrome.
- **Desktop trackpad:** strong fit. Native two-axis trackpad movement makes the strip feel natural without wheel interception.
- **Desktop mouse:** acceptable only with explicit previous/next buttons. A conventional mouse wheel is primarily vertical; hijacking vertical wheel movement to force horizontal paging was intentionally avoided.
- **Keyboard:** accessible without replacing normal link behavior. Tab reaches each real destination link and Enter opens it. When the strip itself is focused, Left/Right and Home/End move among doors.
- **Reduced motion:** smooth scrolling is disabled when `prefers-reduced-motion: reduce` is active.
- **Shareability / machine legibility:** preserved because destination URLs are unchanged real anchors. No SPA routing, synthetic state, or JavaScript-only destination model is used.

## Decision

**Do not promote yet.**

The interaction is promising for touch and trackpad users and does make the five destinations feel more like chapters in one ordered map. But it is not an unqualified usability improvement on desktop mouse input: it needs visible controls to compensate for the horizontal axis, and those controls add interface weight.

The safest next judgment is visual/usability comparison against the current five-door presentation rather than automatic promotion. The protected homepage opening and production files remain untouched.
