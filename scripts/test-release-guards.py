#!/usr/bin/env python3
"""Regression tests for the reviewed website publication boundary."""
from __future__ import annotations

import hashlib
import importlib.util
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

# Visible copy of the current interface. Not the retired HTML blob ids.
REVIEWED_PAGES = (*render_site.PAGES, "library/index.html", "publication/index.html")
REVIEWED_MAIN_DIGESTS = {
    "index.html": "e3e40c0e8bf9a86a56bf2310a23d02bd13759c7978939a8bc688b74b5e7b2894",
    "challenge/index.html": "35017d06fabc4af8fbff1673848242202494987eecc3743498eb030d06bc13d5",
    "company/index.html": "5ee0fce47fe19dbbadb23d2a8515cf169379304802d288904097164da2e4c4a4",
    "research/index.html": "6078f122ecb53179dd0307f1febc7a7065b73fb505575377c69a1cd6d5e4a8d4",
    "about/index.html": "71056e04e994a0cb95e9804e75faaeee22e7217693af779eb0861d0c967bcc83",
    "faq/index.html": "380120bf820b9da0aaa3336daed1ddd3422502dbf963b7eb8499a186f50a1b1b",
    "concepts/index.html": "c9701498a69abc8a3e0a6de96c387792d1cfff0dfcf36a44317f0ea81e524a55",
    "concepts/governed-logic/index.html": "4d26d0a33c800052f804662484e98fe1c928b95d2caf41408aa506a23aa6b43c",
    "concepts/governed-intelligence/index.html": "5c7575ece8c2f1847e93a1e3a813b6dbca0ddbe28684ec15f0c7048ae3a59173",
    "concepts/ultimate-grounding/index.html": "f3337fc850889a761084fdf3e05eb355b596d08532b46731d8ad768612c8cf3d",
    "concepts/alpha-and-omega-reasoning/index.html": "d95a8bcbe692044536b20f49a904b808b230a4af4300319d5d255108698e802d",
    "concepts/governing-referent/index.html": "0cd66a82bb9b41ca84a21e619db789943b71960ba4d5bc5fa275a82839c4c19c",
    "concepts/sufficient-grounding/index.html": "3409fdb0d2c1d5a98654cc884d5221960f397eeb2e3933d84b0bb979cca46c72",
    "mechanism.html": "4558a2a77d171498d6f5bd46563337124c65862d569362201963962023d65c86",
    "sources/index.html": "e283087216066871001f7dbb643b12f23d43f721b2bbf17cf795ac0a06b649de",
    "articles/why-anything/index.html": "136f7206671932935dd5fa67a6507c1758c553b961a1cecbccb269779a037771",
    "articles/integrity-in-artificial-intelligence/index.html": "410e7b0cea28fb3a4d617c5b8853e176ea0f8c0e514daf1d11daa251da2899e5",
    "library/index.html": "e4290fb0c62359a53ed885c4b63574f5f53bd7f12f87543618004ed89650c2a6",
    "publication/index.html": "64daa8358c86d35e8d34cbd715ee9ce5f25201b2ecc727fea44399696849d19c",
}
OPENING_DIGEST = "772b79516151d396c6ca24ec33c86d16fce65570c213c853d7b5061c5ceee1bf"
# The mechanism copy button is the only reviewed inline script.
REVIEWED_INLINE_SCRIPTS = {
    "mechanism.html": ("84459a6d22924c85b98b5c4405cde39de751c84672c6f4b3346c54c00e84182e",),
}
INLINE_SCRIPT = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.IGNORECASE | re.DOTALL)
EXTERNAL_SCRIPT = re.compile(r"\bsrc\s*=", re.IGNORECASE)
JSON_SCRIPT = re.compile(
    r"""type\s*=\s*['"]application/(?:ld\+json|json)['"]""", re.IGNORECASE
)


def assert_reviewed_copy(site: Path) -> None:
    """Reject unreviewed visible copy, an altered opening, or an inline script."""
    for relative in REVIEWED_PAGES:
        text = render_site.main_text((site / relative).read_text(encoding="utf-8"))
        digest = hashlib.sha256(text.encode()).hexdigest()
        if digest != REVIEWED_MAIN_DIGESTS[relative]:
            raise AssertionError(f"Unreviewed page copy differs: {relative}")
    html = (site / "index.html").read_text(encoding="utf-8")
    start = html.find('<div id="site"')
    end = html.find('<header class="site-bar"')
    if start < 0 or end < 0 or hashlib.sha256(html[start:end].encode()).hexdigest() != OPENING_DIGEST:
        raise AssertionError("Unreviewed opening copy")
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
                '<main class="home-content" id="content">',
                '<div class="home-content" id="content">',
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


if __name__ == "__main__":
    unittest.main()
