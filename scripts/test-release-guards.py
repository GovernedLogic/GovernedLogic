#!/usr/bin/env python3
"""Regression tests for the reviewed website publication boundary."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_site  # noqa: E402

CHECK_SPEC = importlib.util.spec_from_file_location("check_origin", SCRIPTS / "check-origin.py")
if CHECK_SPEC is None or CHECK_SPEC.loader is None:
    raise RuntimeError("Unable to load scripts/check-origin.py")
check_origin = importlib.util.module_from_spec(CHECK_SPEC)
CHECK_SPEC.loader.exec_module(check_origin)


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

    def assert_rejected(self, site: Path) -> None:
        with self.assertRaisesRegex(AssertionError, "Reviewed"):
            check_origin.local_checks(site, exact_artifact=True)

    @staticmethod
    def parsed_route(site: Path, route: str):
        html = (site / check_origin.ROUTES[route]).read_text(encoding="utf-8")
        parser = check_origin.DocumentParser()
        parser.feed(html)
        parser.close()
        return parser

    def assert_semantically_rejected(
        self, site: Path, route: str, expected_pattern: str
    ) -> None:
        parser = self.parsed_route(site, route)
        with self.assertRaisesRegex(AssertionError, expected_pattern):
            check_origin.publication_boundary_checks(parser, route)

    def test_reviewed_artifact_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            check_origin.local_checks(site, exact_artifact=True)

    def test_reviewed_semantic_boundaries_pass_without_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            for route in check_origin.ROUTES:
                with self.subTest(route=route):
                    check_origin.publication_boundary_checks(self.parsed_route(site, route), route)

    def test_semantic_guard_rejects_changed_paragraph(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                "The company website is being brought online in stages. "
                "Substantive material remains withheld until reviewed and approved.",
                "An unreviewed homepage claim.",
            )
            self.assert_semantically_rejected(site, "/", "Reviewed paragraph text differs")

    def test_semantic_guard_rejects_appended_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "company/index.html",
                "</main>",
                "<p>An unreviewed claim.</p></main>",
            )
            self.assert_semantically_rejected(
                site, "/company/", "Reviewed content structure differs"
            )

    def test_semantic_guard_rejects_changed_door_label(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                "The Company <span>→</span>",
                "About the Company <span>→</span>",
            )
            self.assert_semantically_rejected(
                site, "/", "Reviewed door label or arrow differs"
            )

    def test_semantic_guard_rejects_misplaced_main(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                '<main class="site-content" id="explore">',
                '<section class="site-content" id="explore">',
            )
            self.assert_semantically_rejected(
                site, "/", "Reviewed homepage landmarks differ"
            )

    def test_semantic_guard_rejects_duplicate_main(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "company/index.html",
                "</main><footer",
                '<main aria-label="Duplicate"></main></main><footer',
            )
            self.assert_semantically_rejected(site, "/company/", "sole main landmark")

    def test_altered_homepage_copy_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                "The company website is being brought online in stages. "
                "Substantive material remains withheld until reviewed and approved.",
                "An unreviewed homepage claim.",
            )
            self.assert_rejected(site)

    def test_appended_opening_claim_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            opening = '<div id="site" role="region" aria-label="Governed Logic Reasoning Systems">'
            self.replace_once(site, "index.html", opening, opening + "<p>An unreviewed claim.</p>")
            self.assert_rejected(site)

    def test_direct_door_group_text_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                '<div class="site-doors">',
                '<div class="site-doors">An unreviewed claim.',
            )
            self.assert_rejected(site)

    def test_added_inline_script_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site = self.build_artifact(directory)
            self.replace_once(
                site,
                "index.html",
                "</head>",
                "<script>document.body.dataset.unreviewed = 'claim';</script></head>",
            )
            self.assert_rejected(site)

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
                self.assert_rejected(site)


if __name__ == "__main__":
    unittest.main()
