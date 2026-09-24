#!/usr/bin/env python3
"""Static acceptance checks for the Governed Logic opening experience.

This checker deliberately avoids simulating a browser. It protects the authored
semantic contract; responsive visual review remains a separate approval gate.
"""
from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
SCRIPT = ROOT / "assets" / "origin-v17.js"
STYLES = ROOT / "assets" / "origin-v17.css"
LEDGER = ROOT / "assets" / "origin-scene.json"

PRINCIPLES = ["BEING", "TRUTH", "LOGIC", "MEANING", "INTELLIGIBILITY", "OBLIGATION"]
CHAIN = ["GROUND", "TRUTH", "LOGIC", "REASONING", "INTELLIGENCE"]
PROHIBITED_OPENING_LABELS = {"LOGOS", "ALPHA", "OMEGA", "0", "1", "EXPLORE"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class OpeningParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.opening_depth = 0
        self.current: dict[str, str] | None = None
        self.current_text: list[str] = []
        self.principles: list[tuple[str, str]] = []
        self.tokens: list[tuple[str, str]] = []
        self.chain: list[str] = []
        self.center_src: str | None = None
        self.architecture_depth = 0

    @staticmethod
    def classes(attributes: dict[str, str]) -> set[str]:
        return set(attributes.get("class", "").split())

    def handle_starttag(self, tag: str, attributes) -> None:
        self.depth += 1
        attrs = dict(attributes)
        classes = self.classes(attrs)
        if not self.opening_depth and "origin-experience" in classes:
            self.opening_depth = self.depth
        if not self.opening_depth:
            return
        if attrs.get("id") == "origin-center":
            self.center_src = attrs.get("src")
        if "origin-architecture" in classes:
            self.architecture_depth = self.depth
        if "origin-principle" in classes:
            self.current = {"kind": "principle", "key": attrs.get("data-principle", "")}
            self.current_text = []
        elif "origin-token" in classes:
            self.current = {"kind": "token", "key": attrs.get("data-token", "")}
            self.current_text = []
        elif tag == "li" and self.architecture_depth:
            self.current = {"kind": "chain", "key": ""}
            self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.current is not None and tag == "li":
            text = " ".join("".join(self.current_text).split())
            kind = self.current["kind"]
            if kind == "principle":
                self.principles.append((self.current["key"], text))
            elif kind == "token":
                self.tokens.append((self.current["key"], text))
            elif kind == "chain":
                self.chain.append(text)
            self.current = None
            self.current_text = []
        if self.architecture_depth == self.depth:
            self.architecture_depth = 0
        if self.opening_depth == self.depth:
            self.opening_depth = 0
        self.depth -= 1


def parse_relationships(script: str) -> set[tuple[str, str]]:
    match = re.search(r"const\s+RELATIONSHIPS\s*=\s*\[(.*?)\n\s*\];", script, re.S)
    require(match is not None, "Could not locate RELATIONSHIPS in origin-v17.js")
    return {
        (left, right)
        for left, right in re.findall(r'\[\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\]', match.group(1))
    }


def main() -> None:
    html = INDEX.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")
    styles = STYLES.read_text(encoding="utf-8")
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))

    parser = OpeningParser()
    parser.feed(html)

    principle_labels = [text for _, text in parser.principles]
    principle_keys = [key for key, _ in parser.principles]
    require(principle_labels == PRINCIPLES, f"Principles differ: {principle_labels}")
    require(principle_keys == [item.lower() for item in PRINCIPLES], f"Principle keys differ: {principle_keys}")
    require(parser.chain == CHAIN, f"Reasoning presentation differs: {parser.chain}")
    require(parser.center_src == "/assets/origin-radial.png", f"Wrong fixed-center asset: {parser.center_src}")

    token_labels = [text.upper() for _, text in parser.tokens]
    require(len(token_labels) <= 24, f"Desktop ambient token cap exceeded: {len(token_labels)}")
    require(len(token_labels) == len(set(token_labels)), "Duplicate ambient token labels")
    require(not (set(token_labels) & PROHIBITED_OPENING_LABELS),
            f"Prohibited opening label present: {sorted(set(token_labels) & PROHIBITED_OPENING_LABELS)}")

    mobile_true = set(re.findall(r"\b([a-z_]+):\s*\{[^{}]*?mobile:\s*true\b", script, re.S))
    desktop_false = set(re.findall(r"\b([a-z_]+):\s*\{[^{}]*?desktop:\s*false\b", script, re.S))
    token_keys = {key for key, _ in parser.tokens}
    desktop_visible = token_keys - desktop_false
    require(len(mobile_true) <= 12, f"Mobile ambient token cap exceeded: {len(mobile_true)}")
    require(len(desktop_visible) <= 24, f"Desktop ambient token cap exceeded: {len(desktop_visible)}")
    require(4 <= len(mobile_true) and 4 <= len(desktop_visible), "Too few visible vocabulary tokens")
    require(mobile_true <= token_keys,
            f"Mobile layout references unknown tokens: {sorted(mobile_true - token_keys)}")
    require(desktop_false <= token_keys,
            f"Desktop cull references unknown tokens: {sorted(desktop_false - token_keys)}")

    drawn_edges = parse_relationships(script)
    chain_edges = {(CHAIN[index].lower(), CHAIN[index + 1].lower()) for index in range(len(CHAIN) - 1)}
    ledger_edges = {(edge["from"], edge["to"]) for edge in ledger["edges"]}
    require(drawn_edges | chain_edges == ledger_edges,
            "Visible JS/chain edges differ from assets/origin-scene.json")

    for blocker in ("preventDefault(", "scrollTo(", "scrollIntoView("):
        require(blocker not in script, f"Scroll-blocking behavior found: {blocker}")
    for blocker in ("scroll-snap-type", "touch-action:none", "touch-action: none"):
        require(blocker not in styles, f"Scroll-blocking CSS found: {blocker}")

    require("--origin-stage-shift" not in script and "--origin-stage-shift" not in styles,
            "The active-stage handoff may not translate the fixed center")
    require("transform-origin:50%50%" in styles.replace(" ", ""),
            "The active-stage handoff must scale around the fixed center")
    stage_rule = re.search(r"\.origin-stage\s*\{([^}]*)\}", styles, re.S)
    stage_minimums = re.findall(r"min-height\s*:\s*([^;]+)", stage_rule.group(1) if stage_rule else "")
    require(stage_rule is not None and all(value.strip() in {"0", "0px"} for value in stage_minimums),
            "The sticky stage may not exceed the dynamic viewport height")

    require("@media(prefers-reduced-motion:reduce)" in styles.replace(" ", ""),
            "Reduced-motion media query missing")
    reduced = styles.split("@media(prefers-reduced-motion:reduce)", 1)[1]
    require(".origin-token{display:none}" in reduced.replace(" ", ""),
            "Reduced-motion state must remove ambient motion tokens")
    require(".origin-architecture{opacity:1}" in reduced.replace(" ", ""),
            "Reduced-motion state must show the reasoning presentation")
    require(".origin-enter{opacity:1;transition:none;animation:none}" in reduced.replace(" ", ""),
            "Reduced-motion state must disable the delayed entrance animation")
    require("gl-intro-failed" in html and "gl-intro-failed" in styles,
            "Static failure fallback is missing")
    require("IntersectionObserver" in script and "visibilitychange" in script,
            "Offscreen/document-hidden animation pausing is missing")

    print(
        "Origin acceptance passed: "
        f"{len(parser.principles)} principles, {len(parser.tokens)} authored vocabulary tokens "
        f"({len(desktop_visible)} desktop / {len(mobile_true)} mobile visible), "
        f"{len(ledger_edges)} authorized edges."
    )


if __name__ == "__main__":
    main()
