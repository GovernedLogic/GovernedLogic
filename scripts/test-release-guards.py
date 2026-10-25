#!/usr/bin/env python3
"""Regression tests for the reviewed website publication boundary.

The reviewed record of each page is its text and links, not its markup.
A stylesheet, class, or layout-tag change does not fail these guards.
Title, description metadata, visible text (including the header, footer,
and homepage text outside main), and anchor labels and hrefs do.
Arrows are exact: ↗ and → are different. The reasoning exhibit is part
of the published homepage. v10.10/hero-exhibit may append one reviewed
exhibit-removed homepage digest; any other homepage still fails.
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
REVIEWED_PAGES = (*render_site.PAGES, "library/index.html", "publication/index.html")
# Published homepage, exhibit included, arrows exact. Hero appends the one
# reviewed exhibit-removed digest to this tuple and nothing else.
HOMEPAGE_DIGESTS = (
    "c226934b60fdc848e658993bcf27fc49da6580b250e8d0f9a8f3ed9fadd2fb6f",
)
REVIEWED_PAGE_DIGESTS = {
    "index.html": HOMEPAGE_DIGESTS,
    "challenge/index.html": ("979a16df6e31870360e89f18ead3c7d7b5599b1769f5bc4e9e097a0a053aa8b4",),
    "company/index.html": ("d0bb671871bc0434ef1fb0e2d252fb1da8dbd1451983ccd2038e81c5906d5de8",),
    "research/index.html": ("6102e05fb4d46844ef2f60b3d95b2048b91d419ce94f5b077213591994c99648",),
    "about/index.html": ("815700c55c9a58fb94f52922b781818426181f839d71196d34130a68a5e38247",),
    "faq/index.html": ("f33dd0e4f9a490588e66701c19c9c29ab3da842e2a151a5fedbc2445593132fe",),
    "concepts/index.html": ("766223284ad97d59d6f1c7e63d5f758f91e0ba7cbec839dd5bd122116cb504f6",),
    "concepts/governed-logic/index.html": ("17da84c6156497c1b4dcbf6f380193cd0897a46d97071c983781b22cf5511335",),
    "concepts/governed-intelligence/index.html": ("d0c3262b48bfaae9f0d4012a86dfabb654251349c926387179f6cda8941341e9",),
    "concepts/ultimate-grounding/index.html": ("2d3e8d5f510d0868a6c909ee823c09e8379616dbd743d5750d913e7d7e27b681",),
    "concepts/alpha-and-omega-reasoning/index.html": ("ac9b15215af6364dfba6f880a984aaebf5bdbe7f96cb440345cd7c60530f2bf2",),
    "concepts/governing-referent/index.html": ("288eade7ec0e38d4394e11c9176f79e97fa0fc4a32fe86f90b347c0eac716840",),
    "concepts/sufficient-grounding/index.html": ("55110ef98727f237f1fc9e6552106d9205b663b5d8a6a58c5fbe8295ac0c3e33",),
    "mechanism.html": ("9357022a64be9b7d2f0bab2bec3b02a790092b5cba297c6843e61b12e9a6822b",),
    "sources/index.html": ("17b794890d80e898ff76d6465f40846e3dbc9b7f08e0189b9535729e80b8accf",),
    "articles/why-anything/index.html": ("f084ba9012314f722fd7e7a116155974aedc08e230ffba0a24b649ca13fc451e",),
    "articles/integrity-in-artificial-intelligence/index.html": ("6bf2040d54d985946d6e2f05c60bf7e3a8c0a7a0505e3591addcd2b87e1ab1c4",),
    "library/index.html": ("0255134ce8da66b42e1b9ea404f42e2738dc83e6bec42f2f01d839cd8108255d",),
    "publication/index.html": ("39416cca3c4d1b382d0957fc07d78c40154ee5f9c92a3da7901b0ca9d31555eb",),
}
OPENING_DIGEST = "8d61ee828cf5dd5f1dd1ac060f7c0b74bd39a8be7b9e3745b86afdb247f7dba2"
# The mechanism copy button is the only reviewed inline script.
REVIEWED_INLINE_SCRIPTS = {
    "mechanism.html": ("84459a6d22924c85b98b5c4405cde39de751c84672c6f4b3346c54c00e84182e",),
}
INLINE_SCRIPT = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.IGNORECASE | re.DOTALL)
EXTERNAL_SCRIPT = re.compile(r"\bsrc\s*=", re.IGNORECASE)
JSON_SCRIPT = re.compile(
    r"""type\s*=\s*['"]application/(?:ld\+json|json)['"]""", re.IGNORECASE
)
META_TAG = re.compile(r"<meta\b([^>]*)>", re.IGNORECASE)
META_ATTR = re.compile(r"""([\w:-]+)\s*=\s*(['"])(.*?)\2""", re.DOTALL)
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

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        if tag == "body":
            self._body = True
        if tag in ("script", "style"):
            self._skip += 1
        if not self._body or self._skip:
            return
        if tag == "a" and "href" in attributes:
            self._anchors.append([attributes["href"], []])
        if attributes.get("aria-label"):
            self._add(f" {attributes['aria-label']} ")
        if attributes.get("alt"):
            self._add(f" {attributes['alt']} ")

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._body and not self._skip and self._anchors:
            href, parts = self._anchors.pop()
            label = WHITESPACE.sub(" ", "".join(parts)).strip()
            self.links.append(f"{href}\t{label}")
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


def _attrs(source: str) -> dict[str, str]:
    return {key.lower(): value for key, _, value in META_ATTR.findall(source)}


def _collapse(value: str) -> str:
    return WHITESPACE.sub(" ", value).strip()


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


def visible(html: str) -> tuple[str, list[str]]:
    parser = Visible()
    parser.feed(html)
    parser.close()
    return _collapse("".join(parser.parts)), parser.links


def page_record(html: str) -> str:
    """Canonical text and links. Markup other than anchors is not recorded."""
    title = _collapse(TITLE_TAG.search(html).group(1) if TITLE_TAG.search(html) else "")
    meta: list[str] = []
    og: list[str] = []
    for raw in META_TAG.findall(html):
        attrs = _attrs(raw)
        if "description" in attrs.get("name", "").split():
            meta.append(attrs.get("content", ""))
        if attrs.get("property", "").lower() == "og:description":
            og.append(attrs.get("content", ""))
    jsonld: list[str] = []
    for attrs, body in INLINE_SCRIPT.findall(html):
        if not JSON_SCRIPT.search(attrs):
            continue
        _descriptions(json.loads(body), jsonld)
    text, links = visible(html)
    return "\n".join((
        "title: " + title,
        "meta: " + "\n".join(meta),
        "og: " + "\n".join(og),
        "jsonld: " + "\n".join(jsonld),
        "text: " + text,
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
    opening = hashlib.sha256(opening_record(homepage).encode()).hexdigest()
    if opening != OPENING_DIGEST:
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
            self.replace_once(
                site,
                "index.html",
                "See what we are building ↓",
                "See what we are building ↓ Substantive material remains withheld",
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

    def test_opening_asset_altered_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            path = site / "assets" / "opening.js"
            path.write_bytes(path.read_bytes() + b"\n")
            with self.assertRaises(AssertionError):
                check_restored.check(site)

    def test_reviewed_semantic_boundaries_pass_without_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            assert_reviewed_copy(self.build_artifact(directory))

    def test_classes_and_layout_markup_do_not_change_reviewed_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                'class="front-door"',
                'class="front-door redesigned" style="display:block"',
            )
            self.replace_once(
                site,
                "index.html",
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
                "index.html",
                "We are building Governed Intelligence: the artificial-intelligence instantiation of Governed Logic.",
                "An unreviewed homepage claim.",
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
                "index.html",
                "A reasoning engine designed to generate and adjudicate candidate conclusions under explicit governing principles.",
                "An unreviewed homepage claim.",
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs"):
                assert_reviewed_copy(site)

    def test_appended_opening_claim_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            opening = '<div id="site" role="region" aria-label="Governed Logic Reasoning Systems">'
            self.replace_once(site, "index.html", opening, opening + "<p>An unreviewed claim.</p>")
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

    def test_jsonld_description_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "company/index.html",
                "Novelty is a named part",
                "Newness is a named part",
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs: company/index.html"):
                assert_reviewed_copy(site)

    def test_footer_tagline_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                "<p>Truth governs logic.<br>Logic governs reasoning.<br>Intelligence is downstream.</p>",
                "<p>Truth governs logic.<br>Logic governs reasoning.<br>Intelligence is afterward.</p>",
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs"):
                assert_reviewed_copy(site)

    def test_nav_label_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                '<a href="/research/">Research</a>',
                '<a href="/research/">Studies</a>',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs"):
                assert_reviewed_copy(site)

    def test_footer_link_label_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                '<a href="/library/">Library</a>',
                '<a href="/library/">Archive</a>',
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
                "index.html",
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
                "index.html",
                'Explore the working prototype <span aria-hidden="true">↗</span>',
                'Explore the working prototype <span aria-hidden="true">→</span>',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs"):
                assert_reviewed_copy(site)


if __name__ == "__main__":
    unittest.main()
