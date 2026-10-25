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
# index.html: #explore is a button, the two /mechanism.html forms are restored, and the brand aria-label is Governed Logic home.
HOMEPAGE_DIGESTS = (
    "a9067640f1aeb445d18e4cc039bc5805972da043b4d957faaedf460dd9438a6f",
)
REVIEWED_PAGE_DIGESTS = {
    "index.html": HOMEPAGE_DIGESTS,
    # challenge/index.html: footer labels restored. The brand aria-label Governed Logic home is restored, so every page digest moved.
    "challenge/index.html": ("ce5c0f7d1df0d68b577d98e3649b859669ed0ceba2718227aa25b9efe6918d66",),
    # company/index.html: same restored footer labels.
    "company/index.html": ("252d5ca42f6b476a5442b3f157b8c390b7342d3e3c9227201c707dba19ee0338",),
    # research/index.html: footer labels restored, plus the Why Anything? and Integrity buttons outside main.
    "research/index.html": ("29326e62eb14fe361f6d8a8fd97ec315d66633abe43d30961498660bf8041fa0",),
    # about/index.html: same restored footer labels.
    "about/index.html": ("326c05b69b9bbf5ad31f0aa45dbad432e056559ceb567f3ecf52f265509f0cd7",),
    # faq/index.html: same restored footer labels.
    "faq/index.html": ("a4ab45144403523b0187c539e09a5910d04d56c2a3e47f3756b3c16a50633ffb",),
    # concepts/index.html: footer labels restored, plus the Alpha and Omega Reasoning button outside main.
    "concepts/index.html": ("f36521869cd88280d6033b1380473ae4d291b54374edc4db263e2ad1d3e6a303",),
    # concepts/governed-logic/index.html: Public prototype form restored, plus the footer labels.
    "concepts/governed-logic/index.html": ("d525110511680e26a4d008b7bd957bdc7ae6fcc863ba5809dba80569e5a90156",),
    # concepts/governed-intelligence/index.html: both prototype forms restored, plus the footer labels.
    "concepts/governed-intelligence/index.html": ("df4309398cf9b52f87eab3b8901b4e90b8cb6d1be82442d10b3a665121453080",),
    # concepts/ultimate-grounding/index.html: same restored footer labels.
    "concepts/ultimate-grounding/index.html": ("a7cdf82ebba194e3235eb5955e33f525605dadc7af3094afddfb1ca704b4d64e",),
    # concepts/alpha-and-omega-reasoning/index.html: same restored footer labels.
    "concepts/alpha-and-omega-reasoning/index.html": ("b0b6652e00fe8c7dd3771f92a4bcd4c439ec989dfe4747c8a8f736afef53e62a",),
    # concepts/governing-referent/index.html: same restored footer labels.
    "concepts/governing-referent/index.html": ("b522484085dd5a67d60e2e50fffbd1ea140858df713929c940e40a73268eb1f3",),
    # concepts/sufficient-grounding/index.html: same restored footer labels.
    "concepts/sufficient-grounding/index.html": ("c509370d31674dc29f243d69b6d4a3e5a9b882ff72c273697f7496b85c5f3981",),
    # mechanism.html: same restored footer labels. In-body anchors stay / and #copy.
    "mechanism.html": ("09f803052a23b75e43c9c8731d643a26c1aef814acddca11dd9d0b7afd63ddc7",),
    # sources/index.html: same restored footer labels.
    "sources/index.html": ("b0675567b0a70b6e5123339f4f5d1e4e028cd9ed605056f8b7d6de575bd69c9e",),
    # articles/why-anything/index.html: same restored footer labels.
    "articles/why-anything/index.html": ("1d4e9f61d9b16a0aad309d5743b91f2d70e7322b06bf418a7fac54ecea3d0853",),
    # articles/integrity-in-artificial-intelligence/index.html: same restored footer labels.
    "articles/integrity-in-artificial-intelligence/index.html": ("a3cdef85b8ea657e99f73ddc9fc7d7d082bac6e650a5af9f066929297cd83b76",),
    # library/index.html: generated page picks up the restored footer labels.
    "library/index.html": ("b6e2987c626995e23be36176b73af4306c5638ccf3927970bc4c720fefa8c6dc",),
    # publication/index.html: generated page picks up the restored footer labels.
    "publication/index.html": ("656f01d4a3bfac4986cd87dbc537d4a269fe7073f7425ad9d574a368c46ed1f7",),
}
# Opening words are unchanged. The #explore anchor is no longer in the opening record.
OPENING_DIGEST = "e4525a6b1741253a9ddf32a04e183588998f354f737189dab236a889f1f8c39d"
# Header skip/current script, plus the mechanism copy button after it.
_HEADER_SCRIPT = "56aa3c97ea8b9ef40eee9611ac9dd6f3dda62f9acd1dd9c470b1bb0c34a46fcf"
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


def visible(html: str) -> tuple[str, list[str]]:
    parser = Visible()
    parser.feed(html)
    parser.close()
    return _collapse("".join(parser.parts)), parser.links


def page_record(html: str) -> str:
    """Canonical text, links, image sources, and publication metadata.

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
    images = [
        f"{_collapse(attrs.get('src', ''))}\t{_collapse(attrs.get('alt', ''))}"
        for attrs in (_attrs(raw) for raw in IMG_TAG.findall(html))
    ]
    jsonld: list[str] = []
    for attrs, body in INLINE_SCRIPT.findall(html):
        if not JSON_SCRIPT.search(attrs):
            continue
        _descriptions(json.loads(body), jsonld)
    text, links = visible(html)
    return "\n".join((
        "title: " + title,
        "og-title: " + "\n".join(og_titles),
        "meta: " + "\n".join(meta),
        "robots: " + "\n".join(robots),
        "og: " + "\n".join(og),
        "jsonld: " + "\n".join(jsonld),
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

    def test_copy_guard_rejects_query_leaks_and_anchors(self) -> None:
        mutations = (
            (
                '<form class="gl-go" method="get" action="/company/"><button type="submit" href="/company/">Company</button>',
                '<form class="gl-go" method="post" action="/company/"><button type="submit" href="/company/">Company</button>',
                "Form method must be get",
            ),
            (
                '<button type="submit" href="/research/">Research</button>',
                '<button type="submit" name="x" value="1" href="/research/">Research</button>',
                "Button name or value",
            ),
            (
                '<form class="gl-go" method="get" action="/company/"><button type="submit" href="/company/">Company</button>',
                '<form class="gl-go" method="get" action="/company/"><input type="hidden" name="q" value="1"><button type="submit" href="/company/">Company</button>',
                "Hidden input",
            ),
            (
                '<form class="gl-go" method="get" action="/company/"><button type="submit" href="/company/">Company</button>',
                '<form class="gl-go" method="get" action="/company/" target="_blank"><button type="submit" href="/company/">Company</button>',
                "target=_blank",
            ),
            (
                '<button type="submit" href="/research/">Research</button>',
                '<a href="/research/">Research</a>',
                "Unexpected anchor",
            ),
        )
        for old, new, message in mutations:
            with self.subTest(message=message):
                with tempfile.TemporaryDirectory() as directory:
                    site = self.build_artifact(directory)
                    self.replace_once(site, "index.html", old, new)
                    with self.assertRaisesRegex(AssertionError, message):
                        check_restored.check(site)

    def test_anchor_set_rejects_planted_library_about_link(self) -> None:
        """Library listings are exactly the catalog paths. area and data-href count as anchors."""
        plants = (
            (
                "library/index.html",
                '<main class="document-main" id="content">',
                '<main class="document-main" id="content"><a href="/about/">About Paul</a>',
                "Unexpected anchor",
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
                "index.html",
                'src="/assets/the-groundless-machine.webp"',
                'src="/assets/unreviewed-cover.webp"',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs: index.html"):
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
                '<button type="submit" href="/research/">Research</button>',
                '<button type="submit" href="/research/">Studies</button>',
            )
            with self.assertRaisesRegex(AssertionError, "Unreviewed page copy differs"):
                assert_reviewed_copy(site)

    def test_footer_link_label_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                '<button type="submit" href="/faq/">FAQ</button>',
                '<button type="submit" href="/faq/">Questions</button>',
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
