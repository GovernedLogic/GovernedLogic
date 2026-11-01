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
REVIEWED_PAGES = (*render_site.PAGES, "library/index.html", "publication/index.html", *render_site.PRINCIPLES.routes())
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
    "challenge/index.html": ("008e049e670c95e9726f68370a1f6106a51335bde4066c6681990623eb968814",),
    # company/index.html: same restored footer labels.
    # Paul's parity rule (Nov 1 2026) via Governor's 1:51 PM ET relay: JSON-LD aligned verbatim to the visible text (three Thing descriptions = each section's first paragraph; Novelty name and description removed (not on the page)); replaces 83bd9692...eec8.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces b25a0ea5...9792.
    "company/index.html": ("23612b23feaeb7cd7f760b84c8fd8ca31a894690ca5f7deb23523537b268d9c1",),
    # research/index.html: footer labels restored, plus the Why Anything? and Integrity buttons outside main.
    # Paul's parity rule (Nov 1 2026) via Governor's 1:51 PM ET relay: JSON-LD aligned verbatim to the visible text (Organization description removed (no visible passage on this page); names = the h1 and the #evaluation h2); replaces c2316f58...bb80.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces 54620889...82b7.
    "research/index.html": ("df67d1797ce39999853e63534271bed705f326871e6c4e5a562daed24428df65",),
    # about/index.html: same restored footer labels; L-BIO-1 removes the invented ending after "What governs the output?".
    "about/index.html": ("b6608ef81a67ee0dc37bc9c730a8dd26d73080f374462aeb2f5da81cfa8e497b",),
    # faq/index.html: same restored footer labels.
    # Paul's parity rule (Nov 1 2026) via Governor's 1:51 PM ET relay: JSON-LD aligned verbatim to the visible text (WebPage description removed (the page has no lead or intro passage)); replaces 0cf2535c...f1bb.
    # Paul's parity rule, Governor's 2:01 PM ET ruling (c); Site Manager's 2:11 PM ET decision (Nov 1 2026): FAQ meta description
    # removed (no visible sentence fits it; nothing invented); replaces 16c09af5...ff0c.
    "faq/index.html": ("0881cf79b2e45a973d5a24476642c453903a24b2ded9255e8db3205c5b336852",),
    # concepts/index.html: footer labels restored, plus the Alpha and Omega Reasoning button outside main.
    # Paul's parity rule (Nov 1 2026) via Governor's 1:51 PM ET relay: JSON-LD aligned verbatim to the visible text (Truth DefinedTerm description = its visible h3 and p); replaces 24c631cb...0de3.
    # Paul 4:48 PM ET Nov 1, set B, publish as written (via Governor, verified): the five principle headings that
    # have a published page (Logic, Being, Meaning, Intelligibility, Obligation) link to it; markup only, words
    # unchanged; Truth stays unlinked. Replaces 759cc224...2154.
    "concepts/index.html": ("bdffef8228403acfbfadecde153b1306d77d21b33c0a63a7dc9a83b18b479cac",),
    # concepts/governed-logic/index.html: Public prototype form restored, plus the footer labels.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces 7dd18ad7...78d0.
    "concepts/governed-logic/index.html": ("ded18af30b0e0fb062883f6423deec5e000bf064064793288a881af4c8fbf64a",),
    # concepts/governed-intelligence/index.html: both prototype forms restored, plus the footer labels.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces 5771482f...e531.
    "concepts/governed-intelligence/index.html": ("ae54685fa2db89a870c27795e3fff6e3465e67954a900179f598b370a1cb20ed",),
    # concepts/ultimate-grounding/index.html: same restored footer labels.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces fb801b1a...1a70.
    "concepts/ultimate-grounding/index.html": ("7287c63093d509e047e9e1daedb613461b9d8c36ef5ac784070a12171bc26573",),
    # concepts/alpha-and-omega-reasoning/index.html: same restored footer labels.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces f2f477ad...3cba.
    "concepts/alpha-and-omega-reasoning/index.html": ("7abbeecebca950643acff38a1159b7763baad59124f677fa7f8f0ab631bea27c",),
    # concepts/governing-referent/index.html: same restored footer labels.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces 8a917fea...443c.
    "concepts/governing-referent/index.html": ("12c433bfe881b12149cade83703b736e2dfcc5cbfd60c989e3d51f8cfa183194",),
    # concepts/sufficient-grounding/index.html: same restored footer labels.
    # Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the visible
    # "Published / modified" line is removed; replaces 957a8840...4186.
    "concepts/sufficient-grounding/index.html": ("b1b42bb1b7778db368950419c371af7915201d398479a22552d61ea9d40de435",),
    # mechanism.html: same restored footer labels. In-body anchors stay / and #copy.
    # Paul's parity rule (Nov 1 2026) via Governor's 1:51 PM ET relay: JSON-LD aligned verbatim to the visible text (WebPage description = the lead paragraph); replaces 495816e5...3c10.
    # Governor's 2:01 PM ET rulings on Paul's parity rule (Nov 1 2026), ruling (c): meta description = the page's visible lead paragraph (= its JSON-LD description); replaces b6e89940...5a65.
    "mechanism.html": ("134486440cbeed981c039bbbe4d4e10947ab9f1f12e7fbfc4c88e54a81a4557d",),
    # sources/index.html: same restored footer labels.
    "sources/index.html": ("6286a2fdcd67de1ef809ba24f263eaabe05dc4166dd11edd550609d134600c6e",),
    # articles/why-anything/index.html: same restored footer labels.
    "articles/why-anything/index.html": ("014f1ebd4106afcd2af9e7d9c5172f1afd2714f66b553be66e85013739c58e05",),
    # articles/integrity-in-artificial-intelligence/index.html: same restored footer labels.
    "articles/integrity-in-artificial-intelligence/index.html": ("83aa7f264ab5e90825f9f5f04818dc4c6757451f004ef0f9d1995fb011898131",),
    # library/index.html: generated page picks up the restored footer labels.
    # page-two/index.html (WEB-205, WEB-231; shell and injection as in RL-FTC-1 3c768d4): the
    # 64bf60f homepage main, byte-identical, in its own shell.
    # Paul's parity rule (Nov 1 2026) via Governor's 1:51 PM ET relay: JSON-LD aligned verbatim to the visible text (WebPage description = the lede); replaces 9a386e37...f5d0.
    # Governor's 2:01 PM ET rulings on Paul's parity rule (Nov 1 2026), ruling (c): meta description = the page's visible lede (= its JSON-LD description); replaces 71804557...2489.
    "page-two/index.html": ("c674f3283ef1cfe94b9e2cbf495af82c246132690c73fdc3174be5f891643faf",),
    # library/index.html: generated page gains the /page-two/ entry (WEB-205, WEB-231).
    # Governor's 2:01 PM ET rulings on Paul's parity rule (Nov 1 2026), ruling (c): meta description = the page's visible lede; replaces 86061a5c...6e0e.
    "library/index.html": ("278bac4ade6ec2d136a133fff9b973531143df8810d8c4806fe4fedb99ed3927",),
    # publication/index.html: generated page picks up the restored footer labels.
    # publication/index.html: generated page gains the /page-two/ entry (WEB-205, WEB-231).
    # Governor's 2:01 PM ET rulings on Paul's parity rule (Nov 1 2026), ruling (c): meta description = the page's visible lede; replaces 7d942e16...b218.
    "publication/index.html": ("0bfe3a8b37c0ecbdb8b66a5a6fb237638b8578e90d5174d0af3b4e4b66b24080",),
    # Principle pages, set B (Paul 4:48 PM ET Nov 1, set B, publish as written (via Governor, verified)): register text
    # verbatim (content/principle-register.md) with the documented code strip and Supporting relabel (content/principles.py).
    "principles/being/index.html": ("3e40ad19dc39d744008eab2760098c5371ddd5f43efe7c521dc118da5ac1afb5",),
    "principles/identity/index.html": ("91838fcff5362719cacdd3abc966fa7f5804a9baa49600033d89dff8e8d27d34",),
    "principles/meaning/index.html": ("da49702c1fffb3663e829e808e39f35c901c5f7282a46be065352c40625d4997",),
    "principles/intelligibility/index.html": ("910672b1d97b576326a3cdd5cb0d9d951d9e2830e5fd9517e0557ccdcb05c3b4",),
    "principles/logic/index.html": ("3f52c58edeba83961429e8948f1118eaf219009031f140c621b5a9bf463841b2",),
    "principles/correspondence/index.html": ("4797de278721e6951b1fdd5cd9ef6b001e846371d6263c6e625c3d67a229b2b6",),
    "principles/obligation/index.html": ("d01104b95f3c02edf44661de4b2f568bd911feb001458843cef5084c6c600a7c",),
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
                'content="Governed Logic Reasoning Systems — Company"',
                'content="Governed Logic Reasoning Systems — Firm"',
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
                 ("company/index.html", "</main>", "<dl><dt>Published / modified</dt><dd>24 September 2026</dd></dl></main>", "Visible page date line on company/index.html")]
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
            (lambda site: [self.replace_once(site, f"principles/{slug}/index.html", '<a href="/principles/identity/" class="gl-link">Identity</a>', 'Identity')
                           for slug in ("being", "meaning", "intelligibility", "logic", "correspondence", "obligation")], r"Principle page not linked from another page: principles/identity/index\.html"),
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
