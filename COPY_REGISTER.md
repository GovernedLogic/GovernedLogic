# Homepage copy register

Every visible string on the homepage (`/`, built from `components/home-bar.html`, `content/home.html` and `components/footer.html`; the old opening was removed by Paul's C8 ruling, 2026-11-01, WEB-215), in page order, with one status. Not published: `scripts/render_site.py` publishes only its explicit allowlist. This register changes no copy (D4).

Statuses:
- **LIBRARY-VERBATIM**: the string appears verbatim in the content library at the cited line(s).
- **MOCKUP-PROVISIONAL**: taken from the approved mockup (`docs/design/2026-10-31/approved-mockup.png`); no verbatim library source. Provisional until Paul supplies or approves the text.
- **EXISTING-SITE**: carried from the 64bf60f site and not verbatim in the library.

Library: `CONTENT_LIBRARY_2026-10-31.txt` (sha256 `f0b19e4caf6a89956588bb38debfa21b89b34d031ffda6e524b5190094191ce9`); line numbers are lines of that file, with the package file named. Content placed per Rigel's `PLACEMENT_MAP.md` (2026-11-01) with its default verdicts; the Map slot column gives each slot, and skipped or unmapped strings are noted. Each LIBRARY-VERBATIM citation was checked line by line by the generator (`/workspace/crops/copy_register.py`), which also fails if any visible text on the built page is missing from this table.

Counts: 58 visible strings; LIBRARY-VERBATIM 56, MOCKUP-PROVISIONAL 1, EXISTING-SITE 1. CSS `text-transform` (uppercase eyebrows, subline and chain labels) is not counted as a change of text.

Band order on this branch: header, hero, core and principles, problem, published work, page-two route, footer. The shelved variant `v11/design-problem-first` was not updated.

| # | Band | Element | Visible string | Status | Library source | Map slot | Note |
|---|---|---|---|---|---|---|---|
| 1 | Header | skip link | Skip to content | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L21428 (WEB-24) |  | Not mapped (header component outside the map). |
| 2 | Header | brand name | Governed Logic | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20871 (WEB-13) | N1 | KEEP-EXISTING. |
| 3 | Header | brand subline | Reasoning Systems | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20872 (WEB-13) | N2 | KEEP-EXISTING. Shown uppercase by CSS. |
| 4 | Header | nav 1 | Home | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20107 (WEB-01) | N3 | KEEP-EXISTING. |
| 5 | Header | nav 2 | The problem | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20779 (WEB-12) | N4 | KEEP-EXISTING. |
| 6 | Header | nav 3 | Research | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L21435 (WEB-24) | N5 | KEEP-EXISTING. |
| 7 | Header | nav 4 (/concepts/governed-logic/) | Governed Logic | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L21431 (WEB-24) | N6 | KEEP-EXISTING. |
| 8 | Header | nav 5 | Company | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L21434 (WEB-24) | N9 | KEEP-EXISTING. |
| 9 | Header | CTA (text visually hidden below 390px and 900-1023px; still its accessible name) | Explore the Research | MOCKUP-PROVISIONAL |  | N11 | SKIPPED: the map's "Explore the research method" (L21394) is 46px wider and makes Search overlap the brand at 390-440px; the fix needs home.css, outside this placement round. |
| 10 | Hero | h1 | Governed Logic Reasoning Systems | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20763 (WEB-12) | H2 | KEEP-EXISTING. |
| 11 | Hero | lede | We are building Governed Intelligence: the artificial-intelligence instantiation of Governed Logic. A reasoning engine designed to generate and adjudicate candidate conclusions under explicit governing principles. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20766, L20767 (WEB-12) | H3 | KEEP-EXISTING; the two source lines joined by a space. The status line L20768 is not placed. |
| 12 | Hero | button 1 | Explore the research method | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L21394 (WEB-23) | H4 | KEEP-EXISTING (the source line's trailing space is not carried). |
| 13 | Hero | button 2 (/concepts/governed-logic/) | Governed Logic | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20848 (WEB-12) | H5 | KEEP-EXISTING. |
| 14 | Hero chain | label 1 | Truth | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20795 (WEB-12) | H6 | KEEP-EXISTING. Sublines H10-H13 dropped. "Ground" (Q4) not added: not a mapped slot. |
| 15 | Hero chain | label 2 | Logic | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20797 (WEB-12) | H7 | KEEP-EXISTING. |
| 16 | Hero chain | label 3 | Reasoning | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20799 (WEB-12) | H8 | KEEP-EXISTING. |
| 17 | Hero chain | label 4 | Intelligence | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20801 (WEB-12) | H9 | KEEP-EXISTING. |
| 18 | Core | h2 (three lines) | Truth governs logic. Logic governs reasoning. Intelligence is downstream. | LIBRARY-VERBATIM | 11_CONTENT_FOR_IMPLEMENTATION L27330, L27344, L27358 (FRAMEWORK-CHAIN-01, WEB-12) | C2 | PLACE (unchanged). Eyebrow C1 dropped. |
| 19 | Core | paragraph | Logic alone cannot determine truth. A valid argument can proceed from false premises. Truth therefore governs the admissibility of the premises and the correspondence of the conclusion to reality. Logic governs the relations of inference. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20806 (WEB-12) | C3 | KEEP-EXISTING. |
| 20 | Core | button | Explore the research method | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L21394 (WEB-23) | C4 | KEEP-EXISTING. |
| 21 | Principles | eyebrow | Six constitutive principles. One named referent. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L21510 (WEB-26) | P0 | KEEP-EXISTING. Five principles show while Truth (P2a/P2b) is held; see Q1/Q2. |
| 22 | Principles | name 1 | Being | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20813 (WEB-12) | P1a | KEEP-EXISTING. |
| 23 | Principles | line 1 | Being is real. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L21513 (WEB-26) | P1b | KEEP-EXISTING. |
| 24 | Principles | name 3 | Logic | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20815 (WEB-12) | P3a | KEEP-EXISTING. P2a/P2b (Truth) dropped, held for Paul. |
| 25 | Principles | line 3 | Logic is binding. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L21512 (WEB-26) | P3b | KEEP-EXISTING. |
| 26 | Principles | name 4 | Meaning | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20816 (WEB-12) | P4a | KEEP-EXISTING. |
| 27 | Principles | line 4 | Meaning is real. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L21514 (WEB-26) | P4b | KEEP-EXISTING. |
| 28 | Principles | name 5 | Intelligibility | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20817 (WEB-12) | P5a | KEEP-EXISTING. |
| 29 | Principles | line 5 | Intelligibility is real. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L21515 (WEB-26) | P5b | KEEP-EXISTING. |
| 30 | Principles | name 6 | Obligation | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20818 (WEB-12) | P6a | KEEP-EXISTING. |
| 31 | Principles | line 6 | Obligation is real and binding. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L21516 (WEB-26) | P6b | KEEP-EXISTING. |
| 32 | Problem | eyebrow | The problem | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20779 (WEB-12) | D1 | KEEP-EXISTING. |
| 33 | Problem | h2 | Large Language Model Defects | LIBRARY-VERBATIM | 02_THE_PROBLEM L3012 (LIB-21) | D2 | PLACE. |
| 34 | Problem | body | A system can become more capable without becoming better grounded. It can generate more fluent arguments, synthesize more information, perform longer inference chains, and imitate increasingly sophisticated human discourse while still lacking a stable governing referent for adjudicating the frameworks from which those outputs are produced. | LIBRARY-VERBATIM | 11_CONTENT_FOR_IMPLEMENTATION L27008 (HOME-PROBLEM-01, WEB-12) | D3 | PLACE. |
| 35 | Problem | button | Large Language Model Defects | LIBRARY-VERBATIM | 02_THE_PROBLEM L3012 (LIB-21) | D4 | PLACE. |
| 36 | Problem | panel 1 title | Truth, Evidence, And Admission Of Claims | LIBRARY-VERBATIM | 02_THE_PROBLEM L3017 (LIB-21) | D5 | PLACE. Panel descriptions D6/D8/D10/D12 dropped. |
| 37 | Problem | panel 2 title | Frameworks, Explanatory Grounds, And Reasoning Structure | LIBRARY-VERBATIM | 02_THE_PROBLEM L3036 (LIB-21) | D7 | PLACE. |
| 38 | Problem | panel 3 title | Meaning, Representation, And Referential Integrity | LIBRARY-VERBATIM | 02_THE_PROBLEM L3064 (LIB-21) | D9 | PLACE. |
| 39 | Problem | panel 4 title | Architecture And Evaluation Failure Points | LIBRARY-VERBATIM | 02_THE_PROBLEM L3117 (LIB-21) | D11 | PLACE. |
| 40 | Published work | eyebrow | Explore the published work | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20844 (WEB-12) | R1 | KEEP-EXISTING. R2 (View All Research) dropped. |
| 41 | Published work | card 1 label | The foundation | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20808 (WEB-12) | R3 | KEEP-EXISTING. |
| 42 | Published work | card 1 title | On the Nature of Ultimate Grounding | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20810 (WEB-12) | R4 | KEEP-EXISTING. |
| 43 | Published work | card 1 text | Why anything? | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20809 (WEB-12) | R5 | KEEP-EXISTING. Card 2 (R6-R8, HOLD) removed whole. |
| 44 | Published work | card 3 label | The architecture | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20847 (WEB-12) | R9 | KEEP-EXISTING. |
| 45 | Published work | card 3 title | Governed Logic | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20848 (WEB-12) | R10 | KEEP-EXISTING. R11 dropped. |
| 46 | Page two route | button | See what we are building | EXISTING-SITE |  | X1 | SKIPPED (kept): the map's text adds the opening's "↓" (L20761) to a button that goes to /page-two/; the map only notes the build dropped it, so placing the arrow is not clear. |
| 47 | Footer | name | Governed Logic | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20871 (WEB-13) |  | Not mapped (footer component). |
| 48 | Footer | name subline | Reasoning Systems | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20872 (WEB-13) |  |  |
| 49 | Footer | chain line 1 | Truth governs logic. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20873 (WEB-13) |  |  |
| 50 | Footer | chain line 2 | Logic governs reasoning. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20874 (WEB-13) |  |  |
| 51 | Footer | chain line 3 | Intelligence is downstream. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20875 (WEB-13) |  |  |
| 52 | Footer | nav | Definitions | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20876 (WEB-13) |  |  |
| 53 | Footer | nav | The prototype | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20877 (WEB-13) |  |  |
| 54 | Footer | nav | FAQ | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20878 (WEB-13) |  |  |
| 55 | Footer | nav | Sources & editions | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20879 (WEB-13) |  |  |
| 56 | Footer | nav | Publication record | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20880 (WEB-13) |  |  |
| 57 | Footer | credit | Paul André Couchoud · Founder and creator of Governed Logic | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20881 (WEB-13) |  |  |
| 58 | Footer | credit | Follow the chain. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20882 (WEB-13) |  |  |

## Accessible names and metadata (not visible text)

| Where | String | Status | Library source | Note |
|---|---|---|---|---|
| document title | Governed Logic Reasoning Systems | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20109 (WEB-01) |  |
| opening identity aria-label | Governed Logic Reasoning Systems | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20109 (WEB-01) |  |
| header search button aria-label | Search | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20575 (WEB-09) | H9; icon-only, so the name is not visible |
| header nav aria-label | Primary | EXISTING-SITE |  | 64bf60f header |
| footer nav aria-label | Explore | EXISTING-SITE |  | 64bf60f footer |
