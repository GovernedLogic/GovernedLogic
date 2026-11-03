#!/usr/bin/env python3
"""Regression tests for the reviewed website publication boundary.

The reviewed record of each page is its text, links, image sources, and
publication metadata, not its markup. A stylesheet, class, or layout-tag
change does not fail these guards. Title, Open Graph title, description
metadata, robots content (name=robots and any meta name ending in
bot, such as googlebot or bingbot), visible text (including image alt
text, the header, footer, and homepage text outside main), image
sources, and anchor labels and hrefs do.
Arrows are exact: ↗ and → are different. The reasoning exhibit is part
of the published homepage. v10.10/hero-narrative appends one reviewed
homepage digest (exhibit removed, Paul's narrative restored in section 01);
any other homepage still fails. v11/design-2026-10-31 appends one PROVISIONAL
homepage digest (WEB-228, WEB-233; C4 unruled); per Paul's C8 ruling (2026-11-01,
WEB-215) the homepage has no opening region and the hero headline is its h1;
Paul's previous homepage main is pinned at /page-two/ (WEB-205, WEB-231).
"""
from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_site  # noqa: E402
import render_site  # noqa: E402

# Whole-page text and links of the current interface. Not the retired HTML blob ids.
# v14 (Paul 2026-11-01 22:34 and 22:36): /articles/ and /the-truth-with-paul/ are reviewed pages too.
REVIEWED_PAGES = (*render_site.PAGES, "library/index.html", "publication/index.html", *render_site.PRINCIPLES.routes(),
                  "articles/index.html", "the-truth-with-paul/index.html")
# Published homepage, exhibit included, arrows exact. Hero-narrative appends the one
# reviewed narrative homepage digest to this tuple and nothing else.
# index.html: four footer controls removed, the brand name is its visible text, and button href attributes are gone.
HOMEPAGE_DIGESTS = (
    "774fe282b185a30f204bda0131d37633f42b8fdf9058e6b1855fb12c835b68bb",
    # v10.10/hero-narrative (supersedes #27): reasoning exhibit removed, including its
    # description, five labels, title line, and captions; Paul's narrative restored after
    # the hero lead lines (Paul, 2026-10-26 01:00 EDT). Every restored line is Paul's own
    # text from 2a64a6b index.html or sources/01_Ultimate_Grounding PDF page 15.
    "271938e034bc528594130b0ecfefe208583c2f9de4cc36643b0e77c8e1b95a0a",
    # PROVISIONAL, NOT REVIEWED (WEB-228, WEB-233; C4 unruled): v11/design-2026-10-31 homepage
    # (Paul's approved 2026-10-31 mockup layout). Its copy is the mockup's provisional layout text
    # and may not ship as final public copy until Paul rules C4. Main ends with the /page-two/
    # button (WEB-205, WEB-231). WEB-215 + Paul's C8 ruling (2026-11-01 02:12 ET, "drop the old
    # opening"): this pin replaces 73f219e1...c7da; the record differs only by the removed opening
    # text that preceded the header (identity, caption, scroll invite). Header, main, footer,
    # metadata, JSON-LD and links are unchanged.
    # Content placement per Rigel's PLACEMENT_MAP.md (2026-11-01, WEB-227 FIFTH): this pin replaces
    # 00821284...99d6. Every homepage string in main and the header is now library-verbatim (see
    # COPY_REGISTER.md) except the kept "See what we are building"; title, meta and JSON-LD are unchanged.
    # Round 5b (WEB-227 FIFTH): N11 places the header CTA text "Explore the research method" (L21394);
    # this pin replaced 50779ff0...72a1. QA-4 (Round 5b) then restores the header About button
    # (/about/; label "About" from the approved mockup, MOCKUP-PROVISIONAL, first built in 6eb269e,
    # not on 64bf60f: QA-8); this pin replaces 43c67665...5925. Those two are
    # the only changes to text or links.
    # Round 6, Paul's hero ruling (Nov 1, 2026): the computer-head hero art is replaced by abstract
    # Seed of Life geometry; the hero img and its preload move from head-artwork.webp to
    # hero-geometry.svg. This pin replaces 27762159...adb7; text is unchanged, only that resource.
    # Paul's parity rule (Nov 1 2026) via Governor's 1:51 PM ET relay: JSON-LD aligned verbatim to the visible text (WebSite description = the hero lede); this pin replaces ad037f66...834d. Text, links, title,
    # meta and Open Graph are unchanged.
    # Governor's 2:01 PM ET rulings on Paul's parity rule (Nov 1 2026), ruling (c): meta description = the page's visible hero lede (= its JSON-LD description); this pin replaces a647098d...2dfd.
    "8f9a4d92a9b04e99a68824f95c819439eb384ee6ad3aa37b434c2a6d7397b0fc",
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) this pin replaces 8f9a4d92...b0fc.
    "b37d33638e305c8022703399b23c09a7868cb7ed85f2d265fa0b7c6bab71cb30",
    # v14.1 (Paul 2026-11-02 16:36 'Yes ... remove that'): homepage lede is Paul's line 441; this pin replaces b37d3363...cb30.
    "48b262212c38a0fdc0827499e533e674b701bfa65d1d355bbddedce441d74f63",
    # v14.1 (Paul 2026-11-01 22:34; Vera's nits): og:description and twitter tags; /articles/ lists each article once; this pin replaces 48b26221...4f63.
    "0fa6c918f51fb789348cc4ebd934c5ba7b9ba723d024e488a62157868e3bda15",
    # Visual refresh, structural part: hero Seed of Life and fly-up removed (Paul, first hand). The hero img
    # /assets/provisional/hero-geometry.svg is the only change in the record (its preload and the home-chime.js tag
    # are not recorded). Text, links, title, meta, Open Graph and JSON-LD are unchanged. This pin replaces 0fa6c918...da15.
    "09f382636c48b9634159568e913993e9b9ac84f179d5895c1a27a0d7ac49e387",
)
# Governor 2:16 PM ET ruling (Nov 1 2026; GL QA F15): page_record now also hashes JSON-LD names and meta author, so
# every page's current pin was re-pinned for that record change alone (no visible text, link, image, title, meta
# description, Open Graph or JSON-LD description changed). Older homepage variants above stay listed as history; they
# were pinned under the earlier record and do not match the new one.
REVIEWED_PAGE_DIGESTS = {
    # v12 site-wide look (Paul, Nov 1 2026: "the rest of the site needs to be updated to match the look and feel";
    # WEB-227 SIXTH): every pin below except the homepage was re-pinned once because the shared header's brand
    # image moves from /assets/governed-logic-mark.webp to the homepage mark /assets/provisional/seed-of-life.png.
    # That img src is the only change in each page record; text, links, title, meta and JSON-LD are unchanged.
    "index.html": HOMEPAGE_DIGESTS,
    # challenge/index.html: footer labels restored. The brand aria-label Governed Logic home is restored, so every page digest moved.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 008e049e...8814.
    # v14.1 (Paul 2026-11-01 22:34; Vera's nits): og:description and twitter tags; /articles/ lists each article once; replaces 600fd1fe...fbaf.
    "challenge/index.html": ("1aa46373d8d940857c6319f2c8de8fc1355961f55f2356d527176870c4d887c3",),
    # company/index.html: same restored footer labels.
    # Paul's parity rule (Nov 1 2026) via Governor's 1:51 PM ET relay: JSON-LD aligned verbatim to the visible text (three Thing descriptions = each section's first paragraph; Novelty name and description removed (not on the page)); replaces 83bd9692...eec8.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces b25a0ea5...9792.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 23612b23...d9c1.
    "company/index.html": ("5a216ec9b020e3d1617c4f53b23a7da031b3a7f97a86a5c2e1d16d4bc821e7f8",),
    # research/index.html: footer labels restored, plus the Why Anything? and Integrity buttons outside main.
    # Paul's parity rule (Nov 1 2026) via Governor's 1:51 PM ET relay: JSON-LD aligned verbatim to the visible text (Organization description removed (no visible passage on this page); names = the h1 and the #evaluation h2); replaces c2316f58...bb80.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces 54620889...82b7.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces df67d179...df65.
    "research/index.html": ("3809a73123d7f389cb6119edb92fec62a0555633ebb187b783af9131ca0eed38",),
    # about/index.html: same restored footer labels; L-BIO-1 removes the invented ending after "What governs the output?".
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces b6608ef8...497b.
    # v14.1 (Paul 2026-11-01 22:34; Vera's nits): og:description and twitter tags; /articles/ lists each article once; replaces 7d85b8ac...b9f2.
    "about/index.html": ("288c45eaadab5d51839aa3fbd58a02ba9f9a49b85e4a23f9c25b3de51e1b028d",),
    # faq/index.html: same restored footer labels.
    # Paul's parity rule (Nov 1 2026) via Governor's 1:51 PM ET relay: JSON-LD aligned verbatim to the visible text (WebPage description removed (the page has no lead or intro passage)); replaces 0cf2535c...f1bb.
    # Paul's parity rule, Governor's 2:01 PM ET ruling (c); Site Manager's 2:11 PM ET decision (Nov 1 2026): FAQ meta description
    # removed (no visible sentence fits it; nothing invented); replaces 16c09af5...ff0c.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 0881cf79...6852.
    "faq/index.html": ("05fe3990768ee97a1d251433d20618a827a3a4b63a2ade5b4c60045f2f12e3e9",),
    # concepts/index.html: footer labels restored, plus the Alpha and Omega Reasoning button outside main.
    # Paul's parity rule (Nov 1 2026) via Governor's 1:51 PM ET relay: JSON-LD aligned verbatim to the visible text (Truth DefinedTerm description = its visible h3 and p); replaces 24c631cb...0de3.
    # Paul 4:48 PM ET Nov 1, set B, publish as written (via Governor, verified): the five principle headings that
    # have a published page (Logic, Being, Meaning, Intelligibility, Obligation) link to it; markup only, words
    # unchanged; Truth stays unlinked. Replaces 759cc224...2154.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces bdffef82...9cac.
    "concepts/index.html": ("d390108365ac4708a3925ed8eb35d686c5c0051e1a7a0d2a7678168bc8dd2ec1",),
    # concepts/governed-logic/index.html: Public prototype form restored, plus the footer labels.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces 7dd18ad7...78d0.
    # Paul 5:29 PM ET Nov 1 (via QA/Governor, verified): the dated "Current website specification / Canonical website checklist · 27 September 2026" row is removed; replaces ded18af3...f64a.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 3455cd96...ae95.
    "concepts/governed-logic/index.html": ("8fa4047875730fced51895be36ce418bd546b2c9abc4342267f7cf688d92be9a",),
    # concepts/governed-intelligence/index.html: both prototype forms restored, plus the footer labels.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces 5771482f...e531.
    # Paul 5:29 PM ET Nov 1 (via QA/Governor, verified): the dated "Current website specification / Canonical website checklist · 27 September 2026" row is removed; replaces ae54685f...20ed.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces aceba944...24de.
    "concepts/governed-intelligence/index.html": ("6cbee63a47844b33f3929d25c3dea48cbe09d4d44f40269d8d47d272ccf20872",),
    # concepts/ultimate-grounding/index.html: same restored footer labels.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces fb801b1a...1a70.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 7287c630...6573.
    "concepts/ultimate-grounding/index.html": ("4cdccb9e39fedb7cfb498a466903399825db0187cf7421f83e6358e63b3fab48",),
    # concepts/alpha-and-omega-reasoning/index.html: same restored footer labels.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces f2f477ad...3cba.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 7abbeece...a27c.
    "concepts/alpha-and-omega-reasoning/index.html": ("6a6624bf8653ccb9ec90f04e46a2b7eba6bb349631cd70fa933cd3f50ef821f7",),
    # concepts/governing-referent/index.html: same restored footer labels.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces 8a917fea...443c.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 12c433bf...3194.
    "concepts/governing-referent/index.html": ("0c650a5dfe6944756e101230d585940fcc92275491645fa2d0ec89b92f8d4790",),
    # concepts/sufficient-grounding/index.html: same restored footer labels.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces 957a8840...4186.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces b1b42bb1...e435.
    "concepts/sufficient-grounding/index.html": ("a6d45394919bd75ff1450a29f38490ea25b849e17e598c4a88f05792d236e908",),
    # mechanism.html: same restored footer labels. In-body anchors stay / and #copy.
    # Paul's parity rule (Nov 1 2026) via Governor's 1:51 PM ET relay: JSON-LD aligned verbatim to the visible text (WebPage description = the lead paragraph); replaces 495816e5...3c10.
    # Governor's 2:01 PM ET rulings on Paul's parity rule (Nov 1 2026), ruling (c): meta description = the page's visible lead paragraph (= its JSON-LD description); replaces b6e89940...5a65.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 13448644...557d.
    # v14.1 (Paul 2026-11-01 22:34; Vera's nits): og:description and twitter tags; /articles/ lists each article once; replaces cb3fa39f...57d0.
    "mechanism.html": ("3a5068fcf394cde56067d181be6f0fa4f4e75593599cc65bcbd10b54463c3e81",),
    # sources/index.html: same restored footer labels.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 6286a2fd...0c6e.
    "sources/index.html": ("163070376e4b40c6281906255171c87206cb705370d25e9c27b8f2714595e7c7",),
    # articles/why-anything/index.html: same restored footer labels.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 014f1ebd...8e05.
    # v14.1 (Paul 2026-11-01 22:34; Vera's nits): og:description and twitter tags; /articles/ lists each article once; replaces f2f1103b...0e94.
    "articles/why-anything/index.html": ("3161f0b43cb8bbefe6be782932a88f7589062cf205b054ac600c1d5ea3fde531",),
    # articles/integrity-in-artificial-intelligence/index.html: same restored footer labels.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 83aa7f26...8131.
    # v14.1 (Paul 2026-11-01 22:34; Vera's nits): og:description and twitter tags; /articles/ lists each article once; replaces af8848a7...61eb.
    "articles/integrity-in-artificial-intelligence/index.html": ("2228c460c6b52923f634fa1ec22e4b6f7dd62053ad07c6190655b88788466a99",),
    # library/index.html: generated page picks up the restored footer labels.
    # page-two/index.html (WEB-205, WEB-231; shell and injection as in RL-FTC-1 3c768d4): the
    # 64bf60f homepage main, byte-identical, in its own shell.
    # Paul's parity rule (Nov 1 2026) via Governor's 1:51 PM ET relay: JSON-LD aligned verbatim to the visible text (WebPage description = the lede); replaces 9a386e37...f5d0.
    # Governor's 2:01 PM ET rulings on Paul's parity rule (Nov 1 2026), ruling (c): meta description = the page's visible lede (= its JSON-LD description); replaces 71804557...2489.
    # v14 (Paul 2026-11-01 22:34): page-two keeps its own header; only the shared footer gains the Articles link; replaces c674f328...3faf.
    "page-two/index.html": ("fee5369d0f6f537857c8d8cefeef8a5f2b4e6051fb78cb9a1dcc172a4baad4ef",),
    # library/index.html: generated page gains the /page-two/ entry (WEB-205, WEB-231).
    # Governor's 2:01 PM ET rulings on Paul's parity rule (Nov 1 2026), ruling (c): meta description = the page's visible lede; replaces 86061a5c...6e0e.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 278bac4a...3927.
    # v14 (Paul 2026-11-01 22:34): footer Articles link and the one header; listing text unchanged (v14 navigation is left out of record text); replaces fb62da91...b185.
    # v14.1 (Paul 2026-11-01 22:34; Vera's nits): og:description and twitter tags; /articles/ lists each article once; replaces 3e4d006b...dd4f.
    "library/index.html": ("a6349985e4ea2a0cbbbd10efa084418088a5468e8b1633308107d83573b69a61",),
    # publication/index.html: generated page picks up the restored footer labels.
    # publication/index.html: generated page gains the /page-two/ entry (WEB-205, WEB-231).
    # Governor's 2:01 PM ET rulings on Paul's parity rule (Nov 1 2026), ruling (c): meta description = the page's visible lede; replaces 7d942e16...b218.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 0bfe3a8b...4080.
    # v14 (Paul 2026-11-01 22:34): footer Articles link and the one header; listing text unchanged (v14 navigation is left out of record text); replaces 51f56ac0...1fb7.
    # v14.1 (Paul 2026-11-01 22:34; Vera's nits): og:description and twitter tags; /articles/ lists each article once; replaces 055804fc...e4e5.
    "publication/index.html": ("d420af842d029f1ea698e40005e63be2a1d969758fa57c501b9e67f7d37ed1fa",),
    # Principle pages, set B (Paul 4:48 PM ET Nov 1, set B, publish as written (via Governor, verified)): register text
    # verbatim (content/principle-register.md) with the documented code strip (content/principles.py); Supporting passages
    # where the register has them (Paul 5:29 PM ET Nov 1 (via QA/Governor, verified)).
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 3e40ad19...afb5.
    "principles/being/index.html": ("d0069a43ad157ae6f807720016ea4b9ddcc376e0b75607506c18cad5d71855d4",),
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 91838fcf...7d34.
    "principles/identity/index.html": ("56a624cdb695307dc26da029245c83b1c9f424b72e91ed50edf9601fc7511715",),
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces da49702c...4997.
    "principles/meaning/index.html": ("46f08d5179dd4f206bc936e33649a63fda881c62db3db145ee82be9efceb70d2",),
    # Paul 5:29 PM ET Nov 1 (via QA/Governor, verified): Supporting back as the register has it ("Inference must preserve ..." returns here; "Intelligibility is real. ..." returns to Obligation); replaces 910672b1...c3b4.
    # Paul 7:48 PM ET Nov 1 (via Governor, verified), v13.1: Supporting = library L17636-37 ("Intelligibility is real." / "Reality has apprehensible order ..."), per the corrected register; replaces 17625862...96d1.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 51a72130...9553.
    "principles/intelligibility/index.html": ("a289a6c2bbfa3ffc2e4f2ac9d0ed5ed460cde2f539cfb5dc03e0c71c43cbe2eb",),
    # Paul 5:29 PM ET Nov 1 (via QA/Governor, verified): Supporting back as the register has it ("Inference must preserve ..." returns to Intelligibility); replaces 3f52c58e...41b2.
    # Paul 7:48 PM ET Nov 1 (via Governor, verified), v13.1: Supporting = library L17633-34 ("Logic is binding and answerable to truth." / "Inference must preserve ..."), per the corrected register; replaces 71371afc...87a8.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 3f52c58e...41b2.
    "principles/logic/index.html": ("19ce765f194d482cd53394c5f4401713698e875dd9ab0d5206043f38f650ea85",),
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 4797de27...b2b6.
    "principles/correspondence/index.html": ("203e959768425060c222ab8baac9ff328896ffc56b4c95fd3d16410f7b953ba1",),
    # Paul 5:29 PM ET Nov 1 (via QA/Governor, verified): Supporting back as the register has it ("Intelligibility is real. ..." returns here); replaces d01104b9...0a7c.
    # Paul 7:48 PM ET Nov 1 (via Governor, verified), v13.1: Supporting = library L17639-40 ("Moral obligation is real and binding." / "Obligation is not reducible to ..."), per the corrected register; replaces 6c530c3a...95df.
    # v14 (Paul 2026-11-01 22:34 and 22:36): one header (homepage bar, The Truth with Paul nav item), footer Articles link, og/twitter tags, page-type art/tiles/bands; /company/ also loses four 'company' words (22:36) replaces 873102db...5a9d.
    "principles/obligation/index.html": ("eeb24bab7242cdab8e1945e9551cf92d32baf9fa26ada9dc9415922b55cd247e",),
    # v14 (Paul 2026-11-01 22:34 "Let's get this big push out."; 22:36 "It's not a company yet"): new page, pinned at first build.
    # v14.1 (Paul 2026-11-01 22:34; Vera's nits): og:description and twitter tags; /articles/ lists each article once; replaces 6c58e8ca...ada8.
    "articles/index.html": ("357bdee410659de0303cb7df77d7634376bf72e8093fa95c5e82889e3ac04186",),
    # v14 (Paul 2026-11-01 22:34 "Let's get this big push out."; 22:36 "It's not a company yet"): new page, pinned at first build.
    # v14.1 (Paul 2026-11-01 22:34; Vera's nits): og:description and twitter tags; /articles/ lists each article once; replaces 29cfff75...8d3a.
    "the-truth-with-paul/index.html": ("eaf3a91c4f1f3c83cf292597e3385c80a518921b70b6c4df4aca5645df40736b",),
}
# Retired by WEB-215 + Paul's C8 ruling (2026-11-01): the homepage has no opening region, and
# assert_reviewed_copy now rejects any. Kept for the record of the reviewed 64bf60f opening.
OPENING_DIGEST = "e4525a6b1741253a9ddf32a04e183588998f354f737189dab236a889f1f8c39d"
# Header skip/current script, plus the mechanism copy button after it.
# C1 reversed (Paul, Nov 1 2026, 12:31 PM ET): the header script marks the current page on <a href> links and no
# longer intercepts GET-form submits; this pin replaces 56aa3c97...6fcf.
_HEADER_SCRIPT = "779d09d285399c8aed6371c2f708588f7fc81525fea73b75788a3d8fe91e2640"
_COPY_SCRIPT = "84459a6d22924c85b98b5c4405cde39de751c84672c6f4b3346c54c00e84182e"
REVIEWED_INLINE_SCRIPTS = {
    relative: (_HEADER_SCRIPT, _COPY_SCRIPT) if relative == "mechanism.html" else (_HEADER_SCRIPT,)
    for relative in (*REVIEWED_PAGES,)
}
INLINE_SCRIPT = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.IGNORECASE | re.DOTALL)
EXTERNAL_SCRIPT = re.compile(r"\bsrc\s*=", re.IGNORECASE)
JSON_SCRIPT = re.compile(
    r"""type\s*=\s*['"]application/(?:ld\+json|json)['"]""", re.IGNORECASE
)
META_TAG = re.compile(r"<meta\b([^>]*)>", re.IGNORECASE)
IMG_TAG = re.compile(r"<img\b([^>]*)>", re.IGNORECASE)
META_ATTR = re.compile(r"""([\w:-]+)\s*=\s*(['"])(.*?)\2""", re.DOTALL)
NAME_TOKEN = re.compile(r"[\s,]+")
TITLE_TAG = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
WHITESPACE = re.compile(r"\s+")


class Visible(HTMLParser):
    """Body text and anchors. Classes, style, and non-anchor tags are ignored."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[str] = []
        self._skip = 0
        self._body = False
        self._anchors: list[list] = []
        self._form_actions: list[str] = []
        self._buttons: list[list] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        if tag == "body":
            self._body = True
        if tag in ("script", "style"):
            self._skip += 1
        if not self._body or self._skip:
            return
        if tag == "form":
            self._form_actions.append(attributes.get("action", ""))
        if tag == "a" and "href" in attributes:
            self._anchors.append([attributes["href"], []])
        if tag == "button" and (attributes.get("type") or "submit").lower() == "submit" and self._form_actions:
            action = attributes.get("formaction") or self._form_actions[-1]
            self._buttons.append([action, []])
        if attributes.get("aria-label"):
            self._add(f" {attributes['aria-label']} ")
        if attributes.get("alt"):
            self._add(f" {attributes['alt']} ")

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._body and not self._skip and self._anchors:
            href, parts = self._anchors.pop()
            label = WHITESPACE.sub(" ", "".join(parts)).strip()
            self.links.append(f"{href}\t{label}")
        if tag == "button" and self._body and not self._skip and self._buttons:
            action, parts = self._buttons.pop()
            label = WHITESPACE.sub(" ", "".join(parts)).strip()
            self.links.append(f"{action}\t{label}")
        if tag == "form" and self._form_actions:
            self._form_actions.pop()
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        if tag == "body":
            self._body = False

    def handle_data(self, data: str) -> None:
        if self._body and not self._skip:
            self._add(data)

    def _add(self, data: str) -> None:
        self.parts.append(data)
        if self._anchors:
            self._anchors[-1][1].append(data)
        if self._buttons:
            self._buttons[-1][1].append(data)


def _attrs(source: str) -> dict[str, str]:
    return {key.lower(): value for key, _, value in META_ATTR.findall(source)}


def _collapse(value: str) -> str:
    return WHITESPACE.sub(" ", value).strip()


def _name_tokens(value: str) -> set[str]:
    return {part.strip().lower() for part in NAME_TOKEN.split(value) if part.strip()}


def _robots_meta(name: str) -> bool:
    """name=robots, or a crawler meta name ending in bot, any case."""
    for token in _name_tokens(name):
        if token == "robots" or token.endswith("bot"):
            return True
    return False


def _descriptions(node: object, found: list[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "description" and isinstance(value, str):
                found.append(value)
            else:
                _descriptions(value, found)
    elif isinstance(node, list):
        for item in node:
            _descriptions(item, found)


def _names(node: object, found: list[str]) -> None:
    # Governor 2:16 PM ET ruling (Nov 1 2026; GL QA F15): JSON-LD names are hashed too, not only descriptions.
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "name" and isinstance(value, str):
                found.append(value)
            else:
                _names(value, found)
    elif isinstance(node, list):
        for item in node:
            _names(item, found)


def visible(html: str) -> tuple[str, list[str]]:
    parser = Visible()
    parser.feed(html)
    parser.close()
    return _collapse("".join(parser.parts)), parser.links


def page_record(html: str) -> str:
    """Canonical text, links, image sources, and publication metadata.

    JSON-LD names and meta author are recorded with the descriptions (Governor 2:16 PM ET ruling, GL QA F15).
    Markup other than anchors and img sources is not recorded. Robots is
    the content of every meta name=robots and every meta whose name ends
    in "bot" (googlebot, bingbot, any case), in document order, so adding,
    editing, or removing that tag changes the record. Image alt text is
    also part of the visible text.
    """
    title = _collapse(TITLE_TAG.search(html).group(1) if TITLE_TAG.search(html) else "")
    meta: list[str] = []
    og_titles: list[str] = []
    og: list[str] = []
    robots: list[str] = []
    authors: list[str] = []
    for raw in META_TAG.findall(html):
        attrs = _attrs(raw)
        if "description" in attrs.get("name", "").split():
            meta.append(attrs.get("content", ""))
        if _robots_meta(attrs.get("name", "")):
            robots.append(_collapse(attrs.get("content", "")))
        property_name = attrs.get("property", "").lower()
        if property_name == "og:title":
            og_titles.append(_collapse(attrs.get("content", "")))
        if property_name == "og:description":
            og.append(attrs.get("content", ""))
        if "author" in attrs.get("name", "").lower().split():
            authors.append(_collapse(attrs.get("content", "")))
    images = [
        f"{_collapse(attrs.get('src', ''))}\t{_collapse(attrs.get('alt', ''))}"
        for attrs in (_attrs(raw) for raw in IMG_TAG.findall(html))
    ]
    jsonld: list[str] = []
    jsonld_names: list[str] = []
    for attrs, body in INLINE_SCRIPT.findall(html):
        if not JSON_SCRIPT.search(attrs):
            continue
        data = json.loads(body)
        _descriptions(data, jsonld)
        _names(data, jsonld_names)
    text, links = visible(html)
    return "\n".join((
        "title: " + title,
        "og-title: " + "\n".join(og_titles),
        "meta: " + "\n".join(meta),
        "robots: " + "\n".join(robots),
        "og: " + "\n".join(og),
        "jsonld: " + "\n".join(jsonld),
        "jsonld-names: " + "\n".join(jsonld_names),
        "meta-author: " + "\n".join(authors),
        "text: " + text,
        "images:",
        *images,
        "links:",
        *links,
    ))


def page_digest(html: str) -> str:
    return hashlib.sha256(page_record(html).encode()).hexdigest()


def opening_record(html: str) -> str:
    start = html.find('<div id="site"')
    end = html.find('<header class="site-bar"')
    if start < 0 or end < 0:
        raise AssertionError("Unreviewed opening copy")
    text, links = visible("<body>" + html[start:end] + "</body>")
    return text + "\n" + "\n".join(links)


def without_exhibit(html: str) -> tuple[str, str | None]:
    """Test helper. The reviewed digest does not call this."""
    start = html.find('<div class="reasoning-exhibit">')
    if start < 0:
        return html, None
    index = start
    depth = 0
    while index < len(html):
        open_at = html.find("<div", index)
        close_at = html.find("</div>", index)
        if close_at < 0:
            break
        if open_at != -1 and open_at < close_at:
            depth += 1
            index = open_at + 4
            continue
        depth -= 1
        index = close_at + len("</div>")
        if depth == 0:
            return html[:start] + html[index:], html[start:index]
    raise AssertionError("Unreviewed page copy differs: index.html")


def assert_reviewed_copy(site: Path) -> None:
    """Reject unreviewed text, links, metadata, opening copy, or an inline script."""
    homepage = (site / "index.html").read_text(encoding="utf-8")
    # WEB-215 + Paul's C8 ruling (2026-11-01, "drop the old opening"): no opening region may return.
    if '<div id="site"' in homepage:
        raise AssertionError("Unreviewed opening copy")
    for relative in REVIEWED_PAGES:
        html = (site / relative).read_text(encoding="utf-8")
        if page_digest(html) not in REVIEWED_PAGE_DIGESTS[relative]:
            raise AssertionError(f"Unreviewed page copy differs: {relative}")
    for path in sorted(site.rglob("*.html")):
        relative = path.relative_to(site).as_posix()
        bodies = []
        for attrs, body in INLINE_SCRIPT.findall(path.read_text(encoding="utf-8")):
            if EXTERNAL_SCRIPT.search(attrs) or JSON_SCRIPT.search(attrs):
                continue
            bodies.append(hashlib.sha256(body.encode()).hexdigest())
        expected = REVIEWED_INLINE_SCRIPTS.get(relative, ())
        if tuple(bodies) != expected:
            raise AssertionError(f"Unreviewed inline script: {relative}")


CHECK_SPEC = importlib.util.spec_from_file_location("check_origin", SCRIPTS / "check-origin.py")
if CHECK_SPEC is None or CHECK_SPEC.loader is None:
    raise RuntimeError("Unable to load scripts/check-origin.py")
check_origin = importlib.util.module_from_spec(CHECK_SPEC)
CHECK_SPEC.loader.exec_module(check_origin)


# Paul's parity rule (Nov 1 2026; Governor's 1:51 PM ET relay): check-parity has no allowlist.
PARITY_SPEC = importlib.util.spec_from_file_location("check_parity", SCRIPTS / "check-parity.py")
if PARITY_SPEC is None or PARITY_SPEC.loader is None:
    raise RuntimeError("Unable to load scripts/check-parity.py")
check_parity = importlib.util.module_from_spec(PARITY_SPEC)
PARITY_SPEC.loader.exec_module(check_parity)


RESTORED_SPEC = importlib.util.spec_from_file_location("check_restored", SCRIPTS / "check-restored.py")
if RESTORED_SPEC is None or RESTORED_SPEC.loader is None:
    raise RuntimeError("Unable to load scripts/check-restored.py")
check_restored = importlib.util.module_from_spec(RESTORED_SPEC)
RESTORED_SPEC.loader.exec_module(check_restored)


class ReleaseGuardTests(unittest.TestCase):
    def build_artifact(self, directory: str) -> Path:
        site = Path(directory) / "site"
        build_site.build(site)
        return site

    @staticmethod
    def replace_once(site: Path, relative: str, old: str, new: str) -> None:
        path = site / relative
        content = path.read_text(encoding="utf-8")
        if content.count(old) != 1:
            raise AssertionError(f"Test fixture marker differs in {relative}: {old!r}")
        path.write_text(content.replace(old, new, 1), encoding="utf-8")

    def test_release_root_imports(self) -> None:
        self.assertEqual(check_origin.ROOT, ROOT)
        self.assertTrue(check_origin.ROOT.is_dir())

    def test_reviewed_artifact_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            check_restored.check(self.build_artifact(directory))

    def test_placeholder_phrase_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            # Fixture marker moved off the removed opening text (WEB-215 + Paul's C8 ruling, 2026-11-01)
            # to the same words on the /page-two/ button; the guarded phrase is unchanged.
            self.replace_once(
                site,
                "index.html",
                ">See what we are building<",
                ">See what we are building Substantive material remains withheld<",
            )
            with self.assertRaises(AssertionError):
                check_restored.check(site)

    def test_missing_main_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                '<main class="home-content" id="content" tabindex="-1">',
                '<div class="home-content" id="content" tabindex="-1">',
            )
            with self.assertRaises(AssertionError):
                check_restored.check(site)

    def test_extra_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            (site / "unreviewed.html").write_text("unreviewed", encoding="utf-8")
            with self.assertRaises(AssertionError):
                check_restored.check(site)

    def test_copy_guard_rejects_query_leaks_and_anchors(self) -> None:
        # C1 reversed (Paul, Nov 1 2026, 12:31 PM ET): navigation is <a href>; the only form left is the library search,
        # so the form plants move to it (was: the homepage Company GET form). The anchor plant became target=_blank.
        mutations = (
            (
                '<form class="library-search" role="search" action="/library/">',
                '<form class="library-search" role="search" method="post" action="/library/">',
                "Form method must be get",
            ),
            (
                '<button id="library-clear" type="button" hidden>',
                '<button id="library-clear" type="button" name="x" value="1" hidden>',
                "Button name or value",
            ),
            (
                '<form class="library-search" role="search" action="/library/">',
                '<form class="library-search" role="search" action="/library/"><input type="hidden" name="q" value="1">',
                "Hidden input",
            ),
            (
                '<form class="library-search" role="search" action="/library/">',
                '<form class="library-search" role="search" action="/library/" target="_blank">',
                "target=_blank",
            ),
            (
                '<a href="/research/" class="gl-link">Research</a>',
                '<a href="/research/" class="gl-link" target="_blank">Research</a>',
                "Internal target=_blank",
            ),
        )
        for old, new, message in mutations:
            with self.subTest(message=message):
                with tempfile.TemporaryDirectory() as directory:
                    site = self.build_artifact(directory)
                    self.replace_once(site, "index.html" if "gl-link" in old else "library/index.html", old, new)
                    with self.assertRaisesRegex(AssertionError, message):
                        check_restored.check(site)

    def test_anchor_set_rejects_planted_library_about_link(self) -> None:
        """C1 reversed (Paul, Nov 1 2026, 12:31 PM ET): links are allowed, but only to published routes and files.
        Was: any anchor on the library failed. area and data-href are still rejected."""
        plants = (
            (
                "library/index.html",
                '<main class="document-main" id="content">',
                '<main class="document-main" id="content"><a href="/assets/opening.js">Opening</a>',
                "Link to an unpublished or withheld path",
            ),
            (
                "index.html",
                '<main class="home-content" id="content" tabindex="-1">',
                '<main class="home-content" id="content" tabindex="-1"><area href="/about/">',
                "Unexpected anchor",
            ),
            (
                "index.html",
                '<main class="home-content" id="content" tabindex="-1">',
                '<main class="home-content" id="content" tabindex="-1"><span data-href="/about/"></span>',
                "Unexpected anchor",
            ),
        )
        for relative, old, new, message in plants:
            with self.subTest(relative=relative, message=message):
                with tempfile.TemporaryDirectory() as directory:
                    site = self.build_artifact(directory)
                    self.replace_once(site, relative, old, new)
                    with self.assertRaisesRegex(AssertionError, message):
                        check_restored.check(site)

    def test_opening_asset_altered_fails(self) -> None:
        # v12 round 2 (QA L1; WEB-227 SIXTH): opening.js is no longer published, so the plant is now the retired
        # file reappearing in the artifact (was: a byte appended to the published opening.js). Still must fail.
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            path = site / "assets" / "opening.js"
            path.write_bytes((ROOT / "assets" / "opening.js").read_bytes())
            with self.assertRaisesRegex(AssertionError, "Retired asset published: assets/opening.js"):
                check_restored.check(site)

    def test_reviewed_semantic_boundaries_pass_without_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            assert_reviewed_copy(self.build_artifact(directory))

    def test_classes_and_layout_markup_do_not_change_reviewed_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                # WEB-205/WEB-231: this homepage copy now lives at /page-two/.
                "page-two/index.html",
                'class="front-door"',
                'class="front-door redesigned" style="display:block"',
            )
            self.replace_once(
                site,
                # WEB-205/WEB-231: this homepage copy now lives at /page-two/.
                "page-two/index.html",
                '<div class="front-copy">',
                '<section class="layout-only"><div class="front-copy">',
            )
            css = site / "assets" / "restored-site.css"
            css.write_text(css.read_text(encoding="utf-8") + "\n/* redesign */\n", encoding="utf-8")
            assert_reviewed_copy(site)

    def test_semantic_guard_rejects_changed_paragraph(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                # WEB-205/WEB-231: this homepage copy now lives at /page-two/.
                "page-two/index.html",
                # The visible lede; its JSON-LD copy (Paul's parity rule, Nov 1 2026) is not the marker.
                '<p class="lede">We are building Governed Intelligence: the artificial-intelligence instantiation of Governed Logic.',
                '<p class="lede">An unreviewed homepage claim.',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs"):
                assert_reviewed_copy(site)

    def test_semantic_guard_rejects_appended_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "company/index.html",
                "</main>",
                "<p>An unreviewed claim.</p></main>",
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs"):
                assert_reviewed_copy(site)

    def test_semantic_guard_rejects_duplicate_main(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "company/index.html",
                "</main>",
                '<main aria-label="Duplicate"></main></main>',
            )
            with self.assertRaisesRegex(AssertionError, "Main landmark count"):
                check_restored.check(site)

    def test_altered_homepage_copy_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                # WEB-205/WEB-231: this homepage copy now lives at /page-two/.
                "page-two/index.html",
                "A reasoning engine designed to generate and adjudicate candidate conclusions under explicit governing principles.",
                "An unreviewed homepage claim.",
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs"):
                assert_reviewed_copy(site)

    def test_appended_opening_claim_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            # WEB-215 + Paul's C8 ruling (2026-11-01): the opening is gone, so re-adding one must fail.
            opening = '<div id="site" role="region" aria-label="Governed Logic Reasoning Systems">'
            # The homepage <body> carries id="website" (Governor's 2:01 PM ET ruling (a): the #website JSON-LD anchor).
            self.replace_once(site, "index.html", '<body class="gl-home-page" id="website">', '<body class="gl-home-page" id="website">' + opening + "<p>An unreviewed claim.</p></div>")
            with self.assertRaisesRegex(AssertionError, "Unreviewed opening copy"):
                assert_reviewed_copy(site)

    def test_added_inline_script_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                "</head>",
                "<script>document.body.dataset.unreviewed = 'claim';</script></head>",
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed inline script"):
                assert_reviewed_copy(site)

    def test_appended_inner_route_claims_fail(self) -> None:
        for relative in (
            "challenge/index.html",
            "company/index.html",
            "research/index.html",
            "library/index.html",
            "faq/index.html",
        ):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                site = self.build_artifact(directory)
                self.replace_once(site, relative, "</main>", "<p>An unreviewed claim.</p></main>")
                with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs"):
                    assert_reviewed_copy(site)

    def test_title_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "company/index.html",
                "<title>Company — Governed Logic Reasoning Systems</title>",
                "<title>Firm — Governed Logic Reasoning Systems</title>",
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs: company/index.html"):
                assert_reviewed_copy(site)

    def test_og_title_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "company/index.html",
                '<meta property="og:title" content="A reasoning systems company.">',
                '<meta property="og:title" content="A reasoning systems firm.">',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs: company/index.html"):
                assert_reviewed_copy(site)

    def test_added_robots_noindex_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                "</head>",
                '<meta name="robots" content="noindex"></head>',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs: index.html"):
                assert_reviewed_copy(site)

    def test_googlebot_noindex_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                "</head>",
                '<meta name="googlebot" content="noindex"></head>',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs: index.html"):
                assert_reviewed_copy(site)

    def test_bingbot_noindex_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                "</head>",
                '<meta name="bingbot" content="noindex"></head>',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs: index.html"):
                assert_reviewed_copy(site)

    def test_removed_robots_tag_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                '<meta name="robots" content="index,follow">',
                "",
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs: index.html"):
                assert_reviewed_copy(site)

    def test_img_src_swap_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                # WEB-205/WEB-231: this homepage copy now lives at /page-two/.
                "page-two/index.html",
                'src="/assets/the-groundless-machine.webp"',
                'src="/assets/unreviewed-cover.webp"',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs: page-two/index.html"):
                assert_reviewed_copy(site)

    def test_og_description_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "company/index.html",
                '<meta property="og:description" content="Governed Logic Reasoning Systems is a reasoning systems company.">',
                '<meta property="og:description" content="Governed Logic Reasoning Systems is a reasoning systems firm.">',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs: company/index.html"):
                assert_reviewed_copy(site)

    # Paul's parity rule (Nov 1 2026; Governor's 1:51 PM ET relay): every machine claim is identical to the visible
    # claim, with no allowlist. A seeded mismatch in pre-existing JSON-LD (not a v13 surface) must fail check-parity.
    def parity(self, site: Path) -> tuple[int, str]:
        import contextlib, io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_parity.main(site)
        return code, out.getvalue()

    def assert_parity_fails(self, site: Path, message: str) -> None:
        # Fails, and fails for the seeded reason (not for another mismatch elsewhere).
        code, out = self.parity(site)
        self.assertEqual(code, 1)
        self.assertIn(message, out)

    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): no page date in any form,
    # and the source edition dates stay on /sources/ (visible and ScholarlyArticle), /library/ and /publication/.
    def test_built_site_has_no_page_dates_and_keeps_edition_dates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.assertNotIn("<lastmod>", (site / "sitemap.xml").read_text(encoding="utf-8"))
            for path in sorted(site.rglob("*.html")):
                html = path.read_text(encoding="utf-8")
                self.assertNotIn("Published / modified", html, path)
                self.assertNotIn('name="gl-date-', html, path)
                self.assertNotIn("dateModified", html, path)
                self.assertNotIn("Canonical website checklist ·", html, path)
                self.assertIsNone(re.search(r'name="gl-approval[^"]*" content="[^"]*\d{4}', html), path)
                if path.relative_to(site).as_posix() != "sources/index.html":
                    self.assertNotIn("datePublished", html, path)
            sources = (site / "sources/index.html").read_text(encoding="utf-8")
            self.assertEqual(sources.count('"datePublished": "2026-09-22"'), 4)
            for shown in ("Paul André Couchoud · 22 September 2026", "23 September 2026 · Selected supplied text and corrections"):
                self.assertIn(shown, sources)
            for page in ("library/index.html", "publication/index.html"):
                self.assertIn("Governed Logic · September 2026", (site / page).read_text(encoding="utf-8"))

    def test_parity_fails_on_seeded_page_dates(self) -> None:
        seeds = [("sitemap.xml", "/about/</loc></url>", "/about/</loc><lastmod>2026-09-24</lastmod></url>", "sitemap.xml carries a lastmod"),
                 ("about/index.html", "</head>", '<meta name="gl-date-modified" content="2026-10-28T08:25:19-04:00"></head>', "gl-date meta on about/index.html"),
                 ("research/index.html", '"@type": "WebPage",', '"@type": "WebPage", "dateModified": "2026-09-27",', "JSON-LD dateModified on research/index.html"),
                 ("company/index.html", "</main>", "<dl><dt>Published / modified</dt><dd>24 September 2026</dd></dl></main>", "Visible page date line on company/index.html"),
                 # Paul 5:29 PM ET Nov 1 (via QA/Governor, verified): approval dates and the dated checklist line.
                 ("research/index.html", 'approval of separated HTML pages">', 'approval of separated HTML pages · 24 September 2026">', "Dated gl-approval meta on research/index.html"),
                 ("concepts/governed-logic/index.html", "<dt>Canonical URL</dt>", "<dt>Current website specification</dt><dd>Canonical website checklist · 27 September 2026</dd><dt>Canonical URL</dt>", "Dated checklist line on concepts/governed-logic/index.html")]
        for page, old, new, message in seeds:
            with self.subTest(page=page), tempfile.TemporaryDirectory() as directory:
                site = self.build_artifact(directory)
                self.replace_once(site, page, old, new)
                self.assert_parity_fails(site, message)

    def test_parity_fails_on_removed_edition_date(self) -> None:
        seeds = [("sources/index.html", '"datePublished": "2026-09-22", "url": "https://governedlogic.com/sources/01_', '"datePublished": "2026-09-23", "url": "https://governedlogic.com/sources/01_', "Source edition date missing from JSON-LD"),
                 ("library/index.html", "Governed Logic · September 2026", "Governed Logic", "Edition date not shown on library/index.html"),
                 ("publication/index.html", "original September 2026 edition dates", "original edition dates", "Edition-date sentence missing")]
        for page, old, new, message in seeds:
            with self.subTest(page=page), tempfile.TemporaryDirectory() as directory:
                site = self.build_artifact(directory)
                self.replace_once(site, page, old, new)
                self.assert_parity_fails(site, message)

    def test_parity_passes_on_reviewed_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.parity(self.build_artifact(directory))[0], 0)

    def test_parity_fails_on_seeded_jsonld_description_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(site, "company/index.html", 'other software systems and AI applications.",', 'other software systems.",')
            self.assert_parity_fails(site, 'JSON-LD description not visible on company/index.html')

    def test_parity_fails_on_restored_pre_existing_jsonld_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(site, "research/index.html", '"name": "Coherence is not correspondence.",', '"name": "Reasoning-system and governing-referent evaluation",')
            self.assert_parity_fails(site, 'JSON-LD name not visible on research/index.html: Reasoning-system')

    def test_parity_fails_on_seeded_jsonld_keyword(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(site, "index.html", '"governed intelligence"]', '"superintelligence"]')
            self.assert_parity_fails(site, 'JSON-LD keyword not visible on index.html: superintelligence')

    def test_parity_fails_on_jsonld_url_to_missing_anchor(self) -> None:
        # Governor's 2:01 PM ET ruling (a) on Paul's parity rule: no JSON-LD @id or url may point at a missing anchor.
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(site, "company/index.html", '"url": "https://governedlogic.com/company/#reasoning-api"', '"url": "https://governedlogic.com/company/#novelty"')
            self.assert_parity_fails(site, 'points at a missing anchor: https://governedlogic.com/company/#novelty')

    # Governor's 2:01 PM ET ruling (c) on Paul's parity rule: meta, og and twitter descriptions are machine claims.
    def test_parity_fails_on_seeded_og_description_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(site, "company/index.html", '<meta property="og:description" content="Governed Logic Reasoning Systems is a reasoning systems company.">', '<meta property="og:description" content="Governed Logic Reasoning Systems is a reasoning company.">')
            self.assert_parity_fails(site, 'og:description not visible on company/index.html')

    def test_parity_fails_on_meta_description_other_than_jsonld(self) -> None:
        # Visible on the page, but not the page's JSON-LD description: still a mismatch.
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(site, "research/index.html", '<meta name="description" content="The objective is not confirmation. The objective is truth.">', '<meta name="description" content="Coherence is not correspondence.">')
            self.assert_parity_fails(site, 'description differs from the JSON-LD description on research/index.html')

    # Governor 2:16 PM ET ruling (Nov 1 2026; GL QA F15): page digests hash JSON-LD names, not only descriptions.
    # v14 (Paul 2026-11-01 22:34; WEB-070 parity): og/twitter tags and Article JSON-LD equal the visible text.
    def test_parity_fails_on_seeded_social_tag_mismatch(self) -> None:
        import shutil
        seeds = [("about/index.html", lambda site: self.replace_once(site, "about/index.html", '<meta property="og:title" content="', '<meta property="og:title" content="Meet '), "og:title on about/index.html is not its visible h1"),
                 ("faq/index.html", lambda site: self.replace_once(site, "faq/index.html", '<meta name="twitter:card" content="summary_large_image">', ''), "twitter:card on faq/index.html: expected exactly one, found 0"),
                 ("research/index.html", lambda site: self.replace_once(site, "research/index.html", '<meta property="og:image" content="https://governedlogic.com/assets/og/research.png"', '<meta property="og:image" content="/assets/og/research.png"'), "og:image on research/index.html is not an absolute"),
                 ("company/index.html", lambda site: shutil.copyfile(site / "assets/og/home.png", site / "assets/og/company.png"), "og:image on company/index.html draws 'Governed Logic Reasoning Systems'"),
                 ("articles/why-anything/index.html", lambda site: self.replace_once(site, "articles/why-anything/index.html", '"headline": "Why Anything?"', '"headline": "Why Anything at All?"'), "Article headline/name on articles/why-anything/index.html is not its h1"),
                 ("articles/integrity-in-artificial-intelligence/index.html", lambda site: self.replace_once(site, "articles/integrity-in-artificial-intelligence/index.html", '"@type": "Article", ', '"@type": "Article", "datePublished": "2026-10-14", '), "Article JSON-LD on articles/integrity-in-artificial-intelligence/index.html carries a date"),
                 ("articles/index.html", lambda site: (site / "articles/index.html").write_text((site / "articles/index.html").read_text(encoding="utf-8").replace("Why does anything exist at all rather than nothing?</p>", "Why anything?</p>"), encoding="utf-8"), "/articles/ card for articles/why-anything/index.html does not carry its first paragraph verbatim"),
                 ("the-truth-with-paul/index.html", lambda site: self.replace_once(site, "the-truth-with-paul/index.html", '<meta name="twitter:card" content="summary_large_image">', '<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="New episodes weekly">'), "twitter:title not visible on the-truth-with-paul/index.html")]
        for page, seed, message in seeds:
            with self.subTest(page=page), tempfile.TemporaryDirectory() as directory:
                site = self.build_artifact(directory)
                seed(site)
                self.assert_parity_fails(site, message)

    # v14.1 (Paul 2026-11-01 22:34; Vera's nits a-d): og:description is the visible lede, twitter tags equal og, RSS item
    # descriptions are the visible ledes, /articles/ lists each article once.
    def test_parity_fails_on_seeded_v14_1_nits(self) -> None:
        def dup_card(site):
            f = site / "articles/index.html"; raw = f.read_text(encoding="utf-8")
            card = re.search(r'<article class="gl-card gl-card-featured">[\s\S]*?</article>', raw).group(0)
            f.write_text(raw.replace('<div class="gl-rail" tabindex="0" role="region" aria-labelledby="gl-latest-title">', '<div class="gl-rail" tabindex="0" role="region" aria-labelledby="gl-latest-title">' + card.replace(' gl-card-featured', ''), 1), encoding="utf-8")
        seeds = [(lambda site: self.replace_once(site, "about/index.html", '<meta name="twitter:image" content="https://governedlogic.com/assets/og/', '<meta name="twitter:image" content="https://governedlogic.com/assets/og/x-'), "twitter:image on about/index.html is not its og:image"),
                 (lambda site: (site / "challenge/index.html").write_text(re.sub(r'<meta property="og:description" content="[^"]*">', '', (site / "challenge/index.html").read_text(encoding="utf-8")), encoding="utf-8"), "og:description on challenge/index.html is not its visible lede"),
                 (lambda site: self.replace_once(site, "feed.xml", "<description>The objective is not confirmation. The objective is truth.</description>", "<description>The objective is truth.</description>"), "feed.xml item https://governedlogic.com/research/: description is not the page's visible lede"),
                 (dup_card, "/articles/ lists articles/why-anything/index.html 2 times")]
        for seed, message in seeds:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                site = self.build_artifact(directory)
                seed(site)
                self.assert_parity_fails(site, message)

    # v14 (Paul 2026-11-01 22:36): The Truth with Paul is exactly its three strings, linked from the header, in the sitemap.
    def test_truth_with_paul_guards(self) -> None:
        import contextlib, io
        twp = "the-truth-with-paul/index.html"
        cases = [
            (lambda site: self.replace_once(site, twp, '<p class="gl-twp-soon">Coming soon</p>', '<p class="gl-twp-soon">Coming soon</p><p>New episodes every week.</p>'), r"The Truth with Paul copy is not exactly its three strings"),
            (lambda site: self.replace_once(site, twp, 'href="https://www.youtube.com/@TheTruthwithPaul"', 'href="https://www.youtube.com/@SomeoneElse"'), r"Subscribe on YouTube is not a plain link"),
            (lambda site: self.replace_once(site, twp, "<h1>The Truth with Paul</h1>", "<h1>The Truth</h1>"), r"The Truth with Paul h1 is not the channel name"),
            (lambda site: self.replace_once(site, "sitemap.xml", "<url><loc>https://governedlogic.com/the-truth-with-paul/</loc></url>", ""), r"Page missing from sitemap: the-truth-with-paul/index\.html"),
            (lambda site: self.replace_once(site, "index.html", '<span class="gl-go"><a href="/the-truth-with-paul/" class="gl-link">The Truth with Paul</a></span>', ""), r"The Truth with Paul is not in the header nav"),
        ]
        for seed, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                site = self.build_artifact(directory)
                seed(site)
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(AssertionError, message):
                    check_restored.check(site)

    # v14.2 (Paul 2026-11-02 18:08 voice call; v14.2.1 Grace relay 6:56 PM Nov 2: named by the h1): the homepage video band is
    # ready to play, never autoplays, and its media sit at ?v=<sha256[:8]> URLs (v14.2.2). v14.3 (Grace relay 8:42 AM Nov 3,
    # Paul voice call): no captions, so a <track> or a .vtt coming back must fail.
    def test_homepage_video_guards(self) -> None:
        import contextlib, io
        cases = [
            (lambda site: self.replace_once(site, "index.html", '<video controls playsinline', '<video autoplay muted controls playsinline'), r"must not autoplay"),
            (lambda site: self.replace_once(site, "index.html", '"></video>', '"><track kind="captions" srclang="en" label="English" src="/assets/video/gl-home-explainer.en.vtt"></video>'), r"must have no <track> element"),
            (lambda site: (site / "assets/video/gl-home-explainer.en.vtt").write_text("WEBVTT\n", encoding="utf-8"), r"No \.vtt may be published or referenced"),
            (lambda site: self.replace_once(site, "index.html", ' aria-labelledby="organization"', ''), r'named by aria-labelledby="organization" only'),
            (lambda site: self.replace_once(site, "index.html", ' aria-labelledby="organization"', ' aria-labelledby="organization" aria-label="Video"'), r'named by aria-labelledby="organization" only'),
            # v14.2.2: replaced media without a new ?v= is a stale cache-busting URL.
            (lambda site: (site / "assets/video/gl-home-explainer.mp4").write_bytes(b"replaced"), r"Homepage video source is not /assets/video/gl-home-explainer\.mp4\?v=[0-9a-f]{8}"),
            (lambda site: self.replace_once(site, "index.html", ".webp?v=44763991", ".webp"), r"Homepage video lacks poster"),
            (lambda site: self.replace_once(site, "index.html", '<section class="gl-video"><video', '<section class="gl-video"><h2>Watch</h2><video'), r"adds words to the page"),
            (lambda site: (site / "assets/video/gl-home-explainer-poster.webp").write_bytes(b"not an image"), r"poster is not a WebP image"),
        ]
        for seed, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                site = self.build_artifact(directory)
                seed(site)
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(AssertionError, message):
                    check_restored.check(site)

    # Visual refresh, structural part: guarded attributes on the existing homepage video (one mp4 source, width and
    # height), and a media swap at the same path is the new file plus one ?v= edit in content/home.html.
    def test_homepage_video_guarded_attributes(self) -> None:
        import contextlib, io
        cases = [
            (lambda site: self.replace_once(site, "index.html", ' width="1280" height="720"', ''), r"Homepage video lacks width"),
            (lambda site: self.replace_once(site, "index.html", ' height="720"', ''), r"Homepage video lacks height"),
            (lambda site: self.replace_once(site, "index.html", ' type="video/mp4"></video>', ' type="video/mp4"><source src="/assets/video/gl-home-explainer.mp4" type="video/mp4"></video>'), r"exactly one <source>"),
            (lambda site: self.replace_once(site, "index.html", '<video controls playsinline', '<video playsinline'), r"Homepage video lacks controls"),
        ]
        for seed, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                site = self.build_artifact(directory)
                seed(site)
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(AssertionError, message):
                    check_restored.check(site)
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            home = (site / "index.html").read_text(encoding="utf-8")
            old = check_restored.video_url(site, check_restored.VIDEO)
            (site / "assets/video/gl-home-explainer.mp4").write_bytes(b"a later cut of the video")
            new = check_restored.video_url(site, check_restored.VIDEO)
            self.assertEqual(home.count(old), 1)
            (site / "index.html").write_text(home.replace(old, new), encoding="utf-8")
            self.assertEqual(check_restored.video_errors(site), [])

    # Visual refresh, structural part: no fly-up, no hero Seed of Life, the empty signature field, the signature on the
    # homepage only, colours as custom properties, motion only without reduced motion, and the gl-cool switch.
    def test_signature_guards(self) -> None:
        import contextlib, io
        def append(site: Path, relative: str, text: str) -> None:
            path = site / relative
            path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")
        js, css = "assets/home-signature.js", "assets/home-signature.css"
        cases = [
            (lambda site: (site / "assets/home-chime.js").write_text("", encoding="utf-8"), r"Logo fly-up script published"),
            (lambda site: self.replace_once(site, "index.html", '<script src="/assets/home-signature.js" defer></script>', '<script src="/assets/home-signature.js" defer></script><script src="/assets/home-chime.js" defer></script>'), r"Logo fly-up referenced: index\.html"),
            (lambda site: self.replace_once(site, "index.html", '<script src="/assets/home-signature.js" defer></script>', '<link rel="preload" href="/assets/provisional/hero-geometry.svg" as="image"><script src="/assets/home-signature.js" defer></script>'), r"still preloads the hero Seed of Life"),
            (lambda site: self.replace_once(site, "index.html", '<div class="gl-hero-art" aria-hidden="true"></div>', '<div class="gl-hero-art" aria-hidden="true"><img src="/assets/provisional/hero-geometry.svg" alt="" width="1004" height="894"></div>'), r"must be empty"),
            (lambda site: self.replace_once(site, "index.html", '<div class="gl-hero-art" aria-hidden="true"></div>', ''), r"expected exactly one div\.gl-hero-art"),
            (lambda site: self.replace_once(site, "index.html", '<script src="/assets/home-signature.js" defer></script>', ''), r"does not load the signature script"),
            (lambda site: self.replace_once(site, "about/index.html", '</head>', '<script src="/assets/home-signature.js" defer></script></head>'), r"Signature loaded outside the homepage: about/index\.html"),
            (lambda site: append(site, js, "/*" + "x" * 3000 + "*/"), r"over 3000"),
            (lambda site: self.replace_once(site, js, "setAttribute('aria-hidden','true')", "setAttribute('role','img')"), r"SVG is not aria-hidden"),
            (lambda site: self.replace_once(site, js, "if(run){try{if(sessionStorage.getItem('gl-sig'))run=false;else sessionStorage.setItem('gl-sig','1');}catch(e){}}", ""), r"once per session"),
            (lambda site: self.replace_once(site, js, "art.appendChild(svg);", "svg.style.color='#ff0000';art.appendChild(svg);"), r"script hard-codes a colour"),
            (lambda site: self.replace_once(site, js, "art.appendChild(svg);", "art.appendChild(svg);art.insertAdjacentText('beforeend','Truth');"), r"may add words"),
            (lambda site: self.replace_once(site, js, "art.appendChild(svg);", "art.appendChild(svg);setInterval(build,4000);"), r"must not loop"),
            (lambda site: self.replace_once(site, css, "fill:var(--gl-sig-node)", "fill:#9cc8ff"), r"stylesheet hard-codes a colour"),
            (lambda site: self.replace_once(site, css, "--gl-warm-glow:rgba(200,225,255,.9)", "--gl-warm-glow:rgba(255,226,170,.9)"), r"gl-cool does not set --gl-warm-glow"),
            (lambda site: append(site, css, "body.gl-home-page .gl-chain li{animation:gl-align 1.2s both}"), r"outside prefers-reduced-motion"),
            (lambda site: append(site, css, "@media (prefers-reduced-motion:no-preference){body.gl-home-page .gl-sig circle{animation:gl-node 600ms infinite}}"), r"must not loop"),
            (lambda site: append(site, css, 'body.gl-home-page .gl-hero-art::after{content:"Truth"}'), r"adds words"),
        ]
        for seed, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                site = self.build_artifact(directory)
                seed(site)
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(AssertionError, message):
                    check_restored.check(site)

    # /page-two/ is frozen: its HTML (with its stylesheet ?v= values) and every file it loads match the d1ba24d build.
    def test_page_two_frozen_guards(self) -> None:
        import contextlib, io
        def append(site: Path, relative: str, text: str) -> None:
            path = site / relative
            path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")
        cases = [
            (lambda site: append(site, "assets/home.css", "\n/* edit */\n"), r"/page-two/ is frozen, but assets/home\.css differs"),
            (lambda site: append(site, "assets/site.css", "\n"), r"/page-two/ is frozen, but assets/site\.css differs"),
            (lambda site: (site / "assets/provisional/grain.png").write_bytes(b"x"), r"/page-two/ is frozen, but assets/provisional/grain\.png differs"),
            (lambda site: self.replace_once(site, "page-two/index.html", "</head>", '<link rel="stylesheet" href="/assets/v14.css"></head>'), r"/page-two/ is frozen, but (assets/v14\.css|page-two/index\.html) differs"),
        ]
        for seed, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                site = self.build_artifact(directory)
                seed(site)
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(AssertionError, message):
                    check_restored.check(site)

    def test_jsonld_name_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(site, "company/index.html", '"name": "Home"', '"name": "Start"')
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs: company/index.html"):
                assert_reviewed_copy(site)

    # Governor 2:16 PM ET ruling (Nov 1 2026; GL QA F12): the live probe requires every unpublished /principles/
    # route to be 404, as a file and as a directory URL. Served locally here; the real probe runs against the live site.
    def test_live_probe_fails_on_served_principle_route(self) -> None:
        import functools, http.server, threading, contextlib, io, shutil
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site))
            handler.log_message = lambda *args: None
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{server.server_address[1]}/"
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    check_restored.live(site, base, 1, 0)
                # Paul 4:48 PM ET Nov 1, set B, publish as written (via Governor, verified): set B is published, so the
                # set-A page not in B (Truth) is the withheld route that must 404; a published page must be served.
                (site / "principles" / "truth").mkdir(parents=True)
                (site / "principles" / "truth" / "index.html").write_text("<!doctype html><title>Truth</title>", encoding="utf-8")
                with self.assertRaisesRegex(AssertionError, r"Internal file exposed: principles/truth/index\.html(.|\n)*Internal file exposed: principles/truth/"):
                    check_restored.live(site, base, 1, 0)
                (site / "principles" / "truth" / "index.html").unlink()
                (site / "principles" / "truth").rmdir()
                expected = Path(directory) / "expected"
                shutil.copytree(site, expected)
                shutil.rmtree(site / "principles" / "being")
                with self.assertRaisesRegex(AssertionError, r"principles/being/index\.html: HTTP Error 404(.|\n)*principles/being/: HTTP Error 404"):
                    check_restored.live(expected, base, 1, 0)
            finally:
                server.shutdown()
                server.server_close()

    # Paul 4:48 PM ET Nov 1, set B, publish as written (via Governor, verified): the seven pages each have one h1 that is
    # the principle's name and an inbound link; no other /principles/ page may be built.
    def test_principle_page_guards(self) -> None:
        import contextlib, io
        cases = [
            (lambda site: self.replace_once(site, "principles/identity/index.html", "<h1>Identity</h1>", "<h1>Identity is foundational.</h1>"), r"Principle h1 is not exactly its name: principles/identity/index\.html"),
            (lambda site: ((site / "principles" / "truth").mkdir(), (site / "principles" / "truth" / "index.html").write_text("<!doctype html><title>Truth</title>", encoding="utf-8")), r"Unpublished principle page in the artifact: principles/truth/index\.html"),
            # v14: the related-principles band carries each name with its tile, on principle and concept pages alike.
            (lambda site: [p.write_text(re.sub(r'<a href="/principles/identity/"[^>]*>[\s\S]*?</a>', 'Identity', p.read_text(encoding="utf-8")), encoding="utf-8")
                           for p in site.rglob("*.html") if p.relative_to(site).as_posix() != "principles/identity/index.html"], r"Principle page not linked from another page: principles/identity/index\.html"),
        ]
        for seed, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                site = self.build_artifact(directory)
                seed(site)
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(AssertionError, message):
                    check_restored.check(site)

    def test_jsonld_description_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "company/index.html",
                # Novelty's JSON-LD was removed under Paul's parity rule (Nov 1 2026; Governor 1:51 PM ET relay).
                'governing principles.",',
                'governing principle.",',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs: company/index.html"):
                assert_reviewed_copy(site)

    def test_footer_tagline_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                # WEB-205/WEB-231: this homepage copy now lives at /page-two/.
                "page-two/index.html",
                "<p>Truth governs logic.<br>Logic governs reasoning.<br>Intelligence is downstream.</p>",
                "<p>Truth governs logic.<br>Logic governs reasoning.<br>Intelligence is afterward.</p>",
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs"):
                assert_reviewed_copy(site)

    def test_anchor_element_fails(self) -> None:
        # C1 reversed (Paul, Nov 1 2026, 12:31 PM ET). Was: any <a> failed. Now each link-coverage rule must fail on a plant:
        # a withheld path, a missing route, GET-form navigation coming back, and an orphaned page.
        plants = (
            ('<a href="/GOVERNEDLOGIC_COM_PRD.txt" class="gl-link">PRD</a>', "Link to an unpublished or withheld path"),
            ('<a href="/assets/materials/earth-day.jpg" class="gl-link">Earth</a>', "Link to an unpublished or withheld path"),
            ('<a href="/no-such-page/" class="gl-link">Nowhere</a>', "Broken link/asset"),
            ('<form class="gl-go" method="get" action="/about/"><button type="submit">About</button></form>', "GET-form navigation remains"),
        )
        for plant, message in plants:
            with self.subTest(message=message, plant=plant):
                with tempfile.TemporaryDirectory() as directory:
                    site = self.build_artifact(directory)
                    self.replace_once(
                        site,
                        "index.html",
                        '<main class="home-content" id="content" tabindex="-1">',
                        '<main class="home-content" id="content" tabindex="-1">' + plant,
                    )
                    with self.assertRaisesRegex(AssertionError, message):
                        check_restored.check(site)

    def test_orphan_page_fails(self) -> None:
        # C1 reversed (Paul, Nov 1 2026, 12:31 PM ET): every published page needs an inbound link.
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            for path in site.rglob("*.html"):
                html = path.read_text(encoding="utf-8")
                if 'href="/faq/"' in html:
                    path.write_text(html.replace('href="/faq/"', 'href="/"'), encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, r"Orphan page \(no inbound link\): /faq/"):
                check_restored.check(site)

    def test_button_href_fails(self) -> None:
        # C1 reversed: the plant moves to the skip button (was: the homepage Research GET-form button).
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                '<button type="button" class="skip-link">',
                '<button type="button" class="skip-link" href="/research/">',
            )
            with self.assertRaisesRegex(AssertionError, "Button href is not allowed"):
                check_restored.check(site)

    def test_nav_label_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                # C1 reversed (Paul, Nov 1 2026, 12:31 PM ET): the nav label is now a link's text.
                '<a href="/research/" class="gl-link">Research</a>',
                '<a href="/research/" class="gl-link">Studies</a>',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs"):
                assert_reviewed_copy(site)

    def test_footer_link_label_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                # C1 reversed (Paul, Nov 1 2026, 12:31 PM ET): the footer label is now a link's text.
                '<a href="/faq/" class="gl-link">FAQ</a>',
                '<a href="/faq/" class="gl-link">Questions</a>',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs"):
                assert_reviewed_copy(site)

    def test_homepage_text_outside_main_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                "</header>",
                "</header><p>Unreviewed aside.</p>",
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs"):
                assert_reviewed_copy(site)

    def test_removed_exhibit_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            path = site / "index.html"
            html = path.read_text(encoding="utf-8")
            if '<div class="reasoning-exhibit">' not in html:
                self.skipTest("reviewed exhibit-removed homepage")
            stripped, exhibit = without_exhibit(html)
            self.assertIsNotNone(exhibit)
            path.write_text(stripped, encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs: index.html"):
                assert_reviewed_copy(site)

    def test_added_northeast_arrow_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                # WEB-205/WEB-231: this homepage copy now lives at /page-two/.
                "page-two/index.html",
                'Examine the upstream problem <span aria-hidden="true">→</span>',
                'Examine the upstream problem <span aria-hidden="true">↗</span>',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs"):
                assert_reviewed_copy(site)

    def test_removed_northeast_arrow_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                # WEB-205/WEB-231: this homepage copy now lives at /page-two/.
                "page-two/index.html",
                'Explore the working prototype <span aria-hidden="true">↗</span>',
                'Explore the working prototype <span aria-hidden="true">→</span>',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs"):
                assert_reviewed_copy(site)


if __name__ == "__main__":
    unittest.main()
