# Homepage copy register

Every visible string on the homepage (`/`, built from `components/home-bar.html`, `content/home.html`, the `index.html` opening and `components/footer.html`), in page order, with one status. Not published: `scripts/render_site.py` publishes only its explicit allowlist. This register changes no copy (D4).

Statuses:
- **LIBRARY-VERBATIM**: the string appears verbatim in the content library at the cited line(s).
- **MOCKUP-PROVISIONAL**: taken from the approved mockup (`docs/design/2026-10-31/approved-mockup.png`); no verbatim library source. Provisional until Paul supplies or approves the text.
- **EXISTING-SITE**: carried from the 64bf60f site and not verbatim in the library.

Library: `CONTENT_LIBRARY_2026-10-31.txt` (sha256 `f0b19e4caf6a89956588bb38debfa21b89b34d031ffda6e524b5190094191ce9`); line numbers are lines of that file, with the package file named. Mapping: Rigel's `GAP_REPORT.md` section 2A (rows H1-H59); its verdicts LIB/DRIFT/GAP are kept in the notes. Each LIBRARY-VERBATIM citation was checked line by line by the generator (`/workspace/crops/copy_register.py`), which also fails if any visible text on the built page is missing from this table.

Counts: 82 visible strings; LIBRARY-VERBATIM 33, MOCKUP-PROVISIONAL 48, EXISTING-SITE 1. CSS `text-transform` (uppercase eyebrows, subline and chain labels) is not counted as a change of text.

Band order on this branch: opening, header, hero, core and principles, problem, latest research, page-two route, footer. On `v11/design-problem-first` the problem band comes before the core band (WEB-222); the strings are identical.

| # | Band | Element | Visible string | Status | Library source | Rigel row | Note |
|---|---|---|---|---|---|---|---|
| 1 | Opening | h1 (identity, drawn as metal title) | Governed Logic | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20755 (WEB-12) |  | Opening held (WEB-111..137). Same text also at L20756-20757 (SVG copies). |
| 2 | Opening | identity subline | Reasoning Systems | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20758 (WEB-12) |  |  |
| 3 | Opening | caption | Building Governed Intelligence. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20759 (WEB-12) |  |  |
| 4 | Opening | caption | Research · Development · Publishing · Education | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20760 (WEB-12) |  |  |
| 5 | Opening | scroll invite | See what we are building ↓ | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20761 (WEB-12) |  |  |
| 6 | Header | skip link | Skip to content | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L21428 (WEB-24) |  |  |
| 7 | Header | brand name | Governed Logic | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20871 (WEB-13) | H1 |  |
| 8 | Header | brand subline | Reasoning Systems | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20872 (WEB-13) | H2 | Shown uppercase by CSS, as in the mockup. |
| 9 | Header | nav 1 | Home | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20107 (WEB-01) | H3 |  |
| 10 | Header | nav 2 | The Problem | MOCKUP-PROVISIONAL |  | H4 | DRIFT (case): library has "The problem" L20779. Mockup label. |
| 11 | Header | nav 3 | Research | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L21435 (WEB-24) | H5 |  |
| 12 | Header | nav 4 | The Framework | MOCKUP-PROVISIONAL |  | H6 | GAP: mockup only. |
| 13 | Header | nav 5 (held, inert) | Applications | MOCKUP-PROVISIONAL |  | H7 | GAP: HOLD until Paul supplies content (L23750). Visible, not linked. |
| 14 | Header | nav 6 | About | MOCKUP-PROVISIONAL |  | H8 | GAP: mockup only. |
| 15 | Header | nav 7 | Company | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L21434 (WEB-24) |  | Kept from the 64bf60f header (WEB-223); not in the mockup. |
| 16 | Header | CTA (text visually hidden below 390px; still its accessible name) | Explore the Research | MOCKUP-PROVISIONAL |  | H10 | GAP: mockup only. Nearest library: "Explore the research method" L21394. |
| 17 | Hero | eyebrow | A Research Framework for Reality | MOCKUP-PROVISIONAL |  | H11 | GAP. |
| 18 | Hero | h2 | A Clearer Foundation for Intelligent Systems. | MOCKUP-PROVISIONAL |  | H12 | GAP: mockup quotation only (07 L22444). |
| 19 | Hero | lede | Governed Logic develops and tests a unified framework for reasoning about reality, integrating truth, logic, reasoning, and moral foundations to build more reliable human and artificial intelligence systems. | MOCKUP-PROVISIONAL |  | H13 | GAP. See R5 L26920. |
| 20 | Hero | button 1 | Explore the Research | MOCKUP-PROVISIONAL |  | H14 | GAP, as H10. |
| 21 | Hero | button 2 | View the Framework | MOCKUP-PROVISIONAL |  | H15 | GAP: mockup only (08 L23700). |
| 22 | Hero chain | label 1 | Truth | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20795 (WEB-12) | H16 | Word verbatim in the 64bf60f homepage chain (WEB-12). Rigel graded label+subline together as LIB (case, split) against L27330. |
| 23 | Hero chain | subline 1 | Governs Logic | MOCKUP-PROVISIONAL |  | H16 | Split/case form of "Truth governs logic." L27330; not verbatim. |
| 24 | Hero chain | label 2 | Logic | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20797 (WEB-12) | H17 | As label 1. |
| 25 | Hero chain | subline 2 | Governs Reasoning | MOCKUP-PROVISIONAL |  | H17 | Split/case form of "Logic governs reasoning." L27344; not verbatim. |
| 26 | Hero chain | label 3 | Reasoning | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20799 (WEB-12) | H18 | As label 1. |
| 27 | Hero chain | subline 3 | Enables Intelligence | MOCKUP-PROVISIONAL |  | H18 | GAP: L22484 says hold this subline. |
| 28 | Hero chain | label 4 | Intelligence | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20801 (WEB-12) | H19 | As label 1. |
| 29 | Hero chain | subline 4 | Is Downstream | MOCKUP-PROVISIONAL |  | H19 | Split/case form of "Intelligence is downstream." L27358; not verbatim. |
| 30 | Core | eyebrow | The Core Idea | MOCKUP-PROVISIONAL |  | H20 | GAP: mockup only. |
| 31 | Core | h2 (three lines) | Truth governs logic. Logic governs reasoning. Intelligence is downstream. | LIBRARY-VERBATIM | 11_CONTENT_FOR_IMPLEMENTATION L27330, L27344, L27358 (FRAMEWORK-CHAIN-01, WEB-12) | H21 | FRAMEWORK-CHAIN-01, READY_FOR_CONTENT_REVIEW. |
| 32 | Core | paragraph | Governed Logic provides a clear, structured framework for reasoning about reality, aligning artificial and human intelligence with truth, and examining the most fundamental questions about ultimate grounding, meaning, and moral obligation. | MOCKUP-PROVISIONAL |  | H22 | GAP. Nearest: L27312 (FRAMEWORK-01, HOLD). |
| 33 | Core | button | Read the Research | MOCKUP-PROVISIONAL |  | H23 | GAP: mockup only. |
| 34 | Principles | eyebrow | Six First Principles | MOCKUP-PROVISIONAL |  | H24 | DRIFT: "Six constitutive principles. One named referent." L21510; count UNRESOLVED (P1-02). |
| 35 | Principles | name 1 | Being / Existence | MOCKUP-PROVISIONAL |  | H25 | DRIFT: "BEING" L22739. |
| 36 | Principles | line 1 | Reality exists. | MOCKUP-PROVISIONAL |  | H26 | DRIFT: "Being is real." L21513. |
| 37 | Principles | name 2 | Binary Truth | MOCKUP-PROVISIONAL |  | H27 | DRIFT, FLAG for Paul (C-D1). |
| 38 | Principles | line 2 | Propositions are true or false. | MOCKUP-PROVISIONAL |  | H28 | DRIFT, FLAG for Paul: "Truth is binary and non-negotiable, grounded in Jesus Christ the Logos." L21511. |
| 39 | Principles | name 3 | Binding Logic | MOCKUP-PROVISIONAL |  | H29 | DRIFT: "LOGIC" L22741. |
| 40 | Principles | line 3 | Logic governs reasoning. | LIBRARY-VERBATIM | 11_CONTENT_FOR_IMPLEMENTATION L27344 (FRAMEWORK-CHAIN-01, WEB-12) | H30 | Verbatim sentence, but Rigel grades the slot DRIFT: the principle line is "Logic is binding." L21512, and this duplicates the Core h2. |
| 41 | Principles | name 4 | Meaning | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20816 (WEB-12) | H31 | Exact case at L20816 (WEB-12 principles list); Rigel cited "MEANING" L22742. |
| 42 | Principles | line 4 | Symbols refer to something. | MOCKUP-PROVISIONAL |  | H32 | DRIFT: "Meaning is real." L21514. |
| 43 | Principles | name 5 | Intelligibility | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20817 (WEB-12) | H33 | Exact case at L20817; Rigel cited "INTELLIGIBILITY" L22743. |
| 44 | Principles | line 5 | Reality is intelligible. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20989 (WEB-16) | H34 | First sentence of L20989 (WEB-16). |
| 45 | Principles | name 6 | Moral Obligation | MOCKUP-PROVISIONAL |  | H35 | DRIFT: "OBLIGATION" L22744. |
| 46 | Principles | line 6 | Moral truths binding on us. | MOCKUP-PROVISIONAL |  | H36 | DRIFT: "Obligation is real and binding." L21516; L23725 calls it unverified. |
| 47 | Problem | eyebrow | The Problem | MOCKUP-PROVISIONAL |  | H37 | DRIFT (case): "The problem" L20779. |
| 48 | Problem | h2 | Current AI Reasoning Has Fundamental Defects. | MOCKUP-PROVISIONAL |  | H38 | GAP. Nearest: L20780-20781. |
| 49 | Problem | body | Large language models can produce fluent, convincing, and useful answers, but they often lack a reliable grounding in truth, logic, and reality. This leads to systematic errors, false confidence, and unpredictable behavior. | MOCKUP-PROVISIONAL |  | H39 | GAP. Library text for this slot: HOME-PROBLEM-01 L27008 (READY_FOR_CONTENT_REVIEW). |
| 50 | Problem | button | Read: LLM Defects | MOCKUP-PROVISIONAL |  | H40 | GAP. Source title "Large Language Model Defects" L3012; display title UNRESOLVED (P1-01). |
| 51 | Problem | panel 1 title | LLM Defects | MOCKUP-PROVISIONAL |  | H41 | DRIFT: "Large Language Model Defects" L3012. |
| 52 | Problem | panel 1 text | A detailed analysis of current AI limitations. | MOCKUP-PROVISIONAL |  | H42 | GAP. |
| 53 | Problem | panel 2 title | Reasoning Chain Failures | MOCKUP-PROVISIONAL |  | H43 | GAP. |
| 54 | Problem | panel 2 text | Where and why LLM reasoning breaks down. | MOCKUP-PROVISIONAL |  | H44 | GAP. |
| 55 | Problem | panel 3 title | Grounding and Reality | MOCKUP-PROVISIONAL |  | H45 | GAP. |
| 56 | Problem | panel 3 text | The need for a governing referent. | MOCKUP-PROVISIONAL |  | H46 | GAP. |
| 57 | Problem | panel 4 title | Toward More Reliable AI | MOCKUP-PROVISIONAL |  | H47 | GAP; conflicts with R5 L26920. |
| 58 | Problem | panel 4 text | Research, testing, and real-world implications. | MOCKUP-PROVISIONAL |  | H48 | GAP. |
| 59 | Latest research | eyebrow | Latest Research | MOCKUP-PROVISIONAL |  | H49 | GAP: RESEARCH-CARDS-01 HOLD L27449. |
| 60 | Latest research | link button | View All Research | MOCKUP-PROVISIONAL |  | H50 | GAP: mockup only. |
| 61 | Latest research | card 1 label | Paper | MOCKUP-PROVISIONAL |  | H51 | GAP. |
| 62 | Latest research | card 1 title | On the Nature of Ultimate Grounding | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20493 (WEB-08) | H52 |  |
| 63 | Latest research | card 1 text | A formal examination of truth, logic, reasoning, and ultimate grounding. | MOCKUP-PROVISIONAL |  | H53 | DRIFT: L20515. |
| 64 | Latest research | card 2 label | Research | MOCKUP-PROVISIONAL |  | H54 | GAP for this role (the word itself is the nav label at L21435). |
| 65 | Latest research | card 2 title (held, inert) | Truth Governs Mathematics | MOCKUP-PROVISIONAL |  | H55 | DRIFT and HOLD (L26950, L23520). |
| 66 | Latest research | card 2 text | Why mathematics requires truth and correspondence with reality. | MOCKUP-PROVISIONAL |  | H56 | GAP. |
| 67 | Latest research | card 3 label | Note | MOCKUP-PROVISIONAL |  | H57 | GAP. |
| 68 | Latest research | card 3 title | The Governed Logic Framework | MOCKUP-PROVISIONAL |  | H58 | DRIFT: page title "Governed Logic" L21499. |
| 69 | Latest research | card 3 text | The chain, the six principles, and practical applications. | MOCKUP-PROVISIONAL |  | H59 | GAP. |
| 70 | Page two route | button | See what we are building | EXISTING-SITE |  |  | 64bf60f index.html scroll-invite label, without its arrow (WEB-205, WEB-231). Library L20761 has it with the arrow. |
| 71 | Footer | name | Governed Logic | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20871 (WEB-13) |  | Footer kept from 64bf60f (WEB-13). |
| 72 | Footer | name subline | Reasoning Systems | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20872 (WEB-13) |  |  |
| 73 | Footer | chain line 1 | Truth governs logic. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20873 (WEB-13) |  |  |
| 74 | Footer | chain line 2 | Logic governs reasoning. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20874 (WEB-13) |  |  |
| 75 | Footer | chain line 3 | Intelligence is downstream. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20875 (WEB-13) |  |  |
| 76 | Footer | nav | Definitions | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20876 (WEB-13) |  |  |
| 77 | Footer | nav | The prototype | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20877 (WEB-13) |  |  |
| 78 | Footer | nav | FAQ | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20878 (WEB-13) |  |  |
| 79 | Footer | nav | Sources & editions | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20879 (WEB-13) |  |  |
| 80 | Footer | nav | Publication record | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20880 (WEB-13) |  |  |
| 81 | Footer | credit | Paul André Couchoud · Founder and creator of Governed Logic | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20881 (WEB-13) |  |  |
| 82 | Footer | credit | Follow the chain. | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20882 (WEB-13) |  |  |

## Accessible names and metadata (not visible text)

| Where | String | Status | Library source | Note |
|---|---|---|---|---|
| document title | Governed Logic Reasoning Systems | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20109 (WEB-01) |  |
| opening identity aria-label | Governed Logic Reasoning Systems | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20109 (WEB-01) |  |
| header search button aria-label | Search | LIBRARY-VERBATIM | 05_WEBSITE_COPY_CURRENT L20575 (WEB-09) | H9; icon-only, so the name is not visible |
| header nav aria-label | Primary | EXISTING-SITE |  | 64bf60f header |
| footer nav aria-label | Explore | EXISTING-SITE |  | 64bf60f footer |
