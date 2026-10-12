#!/usr/bin/env python3
"""Acceptance checks for the current Governed Logic public release."""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from build_site import PUBLIC_FILES, ROOT


ROUTES = {
    "/": "index.html",
    "/challenge/": "challenge/index.html",
    "/company/": "company/index.html",
    "/research/": "research/index.html",
    "/library/": "library/index.html",
    "/faq/": "faq/index.html",
}


# Git blob IDs are exact byte fingerprints for the reviewed HTML, not security credentials.
REVIEWED_HTML_BLOB_IDS = {
    "index.html": "7f93d377cd03477ff09dce902ad26cb276bf0c54",
    "challenge/index.html": "e089a8dd20eae386182ad6eaa2a2f505ead71fe0",
    "company/index.html": "3da275358597edcea7b1d05e35d83e904b9a6bf2",
    "research/index.html": "821d511aa44ff8abd08756a5c73b89532837698e",
    "library/index.html": "f7445f452dfbd3c2ad430f6f5e34747801102d14",
    "faq/index.html": "47bc58916df9b317ac21230e521fa9b8742a6000",
}

NAVIGATION = (
    ("/challenge/", "Follow the Chain"),
    ("/company/", "Company"),
    ("/research/", "Research"),
    ("/library/", "Canonical Library"),
    ("/faq/", "FAQ"),
)

INNER_PAGE_DOORS = {
    "/challenge/": ("/", "/company/"),
    "/company/": ("/", "/research/"),
    "/research/": ("/", "/library/"),
    "/library/": ("/", "/faq/"),
    "/faq/": ("/", "/challenge/"),
}

MACHINE_SURFACES = {
    "/challenge/": "/challenge/index.json",
    "/faq/": "/faq/index.json",
}

CHALLENGE_NOTICE = (
    "Challenge rules, inputs, outputs, examples, and evaluation criteria remain withheld "
    "pending source review and approval."
)
FAQ_NOTICE = "FAQ questions and answers remain withheld pending source review and approval."


REVIEWED_ROUTE_COPY = {
    "/": {
        "heading": ("h2", "Governed Logic"),
        "paragraphs": (
            "GROUND → TRUTH → LOGIC → REASONING → INTELLIGENCE",
            "The company website is being brought online in stages. "
            "Substantive material remains withheld until reviewed and approved.",
        ),
        "doors": (
            ("/challenge/", "Follow the Chain Challenge"),
            ("/company/", "The Company"),
            ("/research/", "Research"),
            ("/library/", "Canonical Library"),
        ),
    },
    "/challenge/": {
        "heading": ("h1", "Follow the Chain Challenge"),
        "paragraphs": (CHALLENGE_NOTICE,),
        "doors": (
            ("/", "Return to homepage"),
            ("/company/", "The Company"),
        ),
    },
    "/company/": {
        "heading": ("h1", "The Company"),
        "paragraphs": (
            "Governed Logic Reasoning Systems. Detailed company material remains under review.",
        ),
        "doors": (
            ("/", "Return to homepage"),
            ("/research/", "Research"),
        ),
    },
    "/research/": {
        "heading": ("h1", "Research"),
        "paragraphs": (
            "Research findings and demonstrations are not published here until source review and approval.",
        ),
        "doors": (
            ("/", "Return to homepage"),
            ("/library/", "Canonical Library"),
        ),
    },
    "/library/": {
        "heading": ("h1", "Canonical Library"),
        "paragraphs": (
            "This is the entry point for stable, machine-readable canonical publications. "
            "Unreviewed documents are not public.",
        ),
        "doors": (
            ("/", "Return to homepage"),
            ("/faq/", "FAQ"),
        ),
    },
    "/faq/": {
        "heading": ("h1", "Frequently Asked Questions"),
        "paragraphs": (FAQ_NOTICE,),
        "doors": (
            ("/", "Return to homepage"),
            ("/challenge/", "Follow the Chain"),
        ),
    },
}

BRAND_ATTRIBUTES = {"href": "/", "aria-label": "Governed Logic home"}
BRAND_TEXT = "GOVERNED LOGIC"
EYEBROW_TEXT = "GOVERNED LOGIC REASONING SYSTEMS"
FOOTER_TEXT = "Governed Logic Reasoning Systems · Home"
NAVIGATION_STYLESHEET = "/assets/site-navigation.css"

WITHHELD_URLS = (
    "/GOVERNEDLOGIC_COM_PRD.txt",
    "/requirements.txt",
    "/WEBSITE_CHECKLIST.txt",
    "/WEBSITE_ALIGNMENT_AUDIT_2026-10-02.txt",
    "/WEBSITE_INFORMATION_ARCHITECTURE_HANDOFF.txt",
    "/WEBSITE_NORTH_STAR.txt",
    "/WEBSITE_SOURCE_AUTHORITY_MAP.txt",
    "/scripts/check-origin.py",
    "/scripts/build_site.py",
    "/scripts/build-corpus.py",
    "/scripts/check-corpus.py",
    "/concepts/governed-logic/",
    "/concepts/ultimate-grounding/",
    "/concepts/governed-intelligence/",
    "/assets/origin-v17.js",
    "/assets/origin-v17.css",
    "/assets/origin-scene.json",
    "/assets/gl-reasoning-systems.webp",
    "/assets/gl-reasoning-systems.png",
    "/assets/releases/v18.1-alignment.jpg",
    "/assets/releases/v18.2-origin.jpg",
    "/paul-portrait.png",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


class Element:
    def __init__(self, tag: str, attrs: dict[str, str | None], parent: Element | None = None) -> None:
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: list[Element | str] = []

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Element):
                yield from child.walk()

    def text(self) -> str:
        return "".join(child.text() if isinstance(child, Element) else child for child in self.children)

    def element_children(self) -> list[Element]:
        return [child for child in self.children if isinstance(child, Element)]

    def has_class(self, class_name: str) -> bool:
        return class_name in (self.attrs.get("class") or "").split()


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def git_blob_id(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Element("document", {})
        self.stack = [self.root]
        self.links: list[str] = []
        self.current_links: list[tuple[str, str | None]] = []
        self.canonical: str | None = None
        self.robots: str | None = None
        self.stylesheets: list[str] = []
        self.scripts: list[str] = []
        self.json_alternates: list[str] = []

    def handle_starttag(self, tag: str, attributes) -> None:
        self._starttag(tag, attributes, push=tag not in VOID_ELEMENTS)

    def handle_startendtag(self, tag: str, attributes) -> None:
        self._starttag(tag, attributes, push=False)

    def _starttag(self, tag: str, attributes, push: bool) -> None:
        attrs = dict(attributes)
        element = Element(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(element)
        if push:
            self.stack.append(element)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
            if "aria-current" in attrs:
                self.current_links.append((attrs["href"], attrs["aria-current"]))
        relations = (attrs.get("rel") or "").split()
        if tag == "link" and "canonical" in relations:
            self.canonical = attrs.get("href")
        if tag == "link" and "stylesheet" in relations and attrs.get("href"):
            self.stylesheets.append(attrs["href"])
        if (
            tag == "link"
            and "alternate" in relations
            and attrs.get("type") == "application/json"
            and attrs.get("href")
        ):
            self.json_alternates.append(attrs["href"])
        if tag == "script" and attrs.get("src"):
            self.scripts.append(attrs["src"])
        if tag == "meta" and attrs.get("name", "").lower() == "robots":
            self.robots = attrs.get("content")

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)

    def elements(self, tag: str | None = None, class_name: str | None = None) -> list[Element]:
        return [
            element
            for element in self.root.walk()
            if element is not self.root
            and (tag is None or element.tag == tag)
            and (class_name is None or element.has_class(class_name))
        ]


def public_path(route: str, reference: str) -> str | None:
    if reference.startswith(("https://", "http://", "mailto:", "#")):
        return None
    joined = urljoin("https://governedlogic.com" + route, reference)
    return joined.removeprefix("https://governedlogic.com").split("?", 1)[0].split("#", 1)[0]


def shell_checks(parser: DocumentParser, route: str) -> None:
    headers = parser.elements("header", "site-bar")
    require(len(headers) == 1, f"Expected exactly one header.site-bar on {route}; found {len(headers)}")
    header = headers[0]
    require(header.attrs == {"class": "site-bar"}, f"Site header attributes differ on {route}: {header.attrs}")
    require(not normalized("".join(child for child in header.children if isinstance(child, str))),
            f"Unexpected direct text in site header on {route}")

    header_children = header.element_children()
    require([element.tag for element in header_children] == ["a", "nav"],
            f"Site header must contain one direct brand anchor followed by one primary nav on {route}")
    brand, navigation = header_children
    require(brand.attrs == BRAND_ATTRIBUTES, f"Brand-link attributes differ on {route}: {brand.attrs}")
    require(not brand.element_children(), f"Brand link must remain plain anchor text on {route}")
    require(normalized(brand.text()) == BRAND_TEXT, f"Brand-link text differs on {route}: {brand.text()!r}")

    primary_navigations = [
        element for element in parser.elements("nav") if element.attrs.get("aria-label") == "Primary"
    ]
    require(len(primary_navigations) == 1,
            f"Expected exactly one nav[aria-label='Primary'] on {route}; found {len(primary_navigations)}")
    require(navigation is primary_navigations[0], f"Primary navigation must be a direct site-header child on {route}")
    require(navigation.attrs == {"aria-label": "Primary"},
            f"Primary-navigation attributes differ on {route}: {navigation.attrs}")
    require(not normalized("".join(child for child in navigation.children if isinstance(child, str))),
            f"Unexpected direct text in primary navigation on {route}")

    navigation_children = navigation.element_children()
    require(all(element.tag == "a" for element in navigation_children),
            f"Primary-navigation items must be direct ordinary anchors on {route}")
    actual_navigation = tuple(
        (element.attrs.get("href"), normalized(element.text())) for element in navigation_children
    )
    require(actual_navigation == NAVIGATION,
            f"Primary-navigation order, destinations, or labels differ on {route}: {actual_navigation}")
    for element, (href, _) in zip(navigation_children, NAVIGATION):
        expected_attrs = {"href": href}
        if route != "/" and href == route:
            expected_attrs["aria-current"] = "page"
        require(element.attrs == expected_attrs,
                f"Primary-navigation anchor attributes differ for {href} on {route}: {element.attrs}")
    expected_current = [] if route == "/" else [(route, "page")]
    require(parser.current_links == expected_current,
            f"Current-page indication differs on {route}: {parser.current_links}")

    resolved_stylesheets = [public_path(route, reference) for reference in parser.stylesheets]
    require(resolved_stylesheets.count(NAVIGATION_STYLESHEET) == 1,
            f"Shared navigation stylesheet must appear exactly once on {route}: {parser.stylesheets}")

    eyebrows = parser.elements(class_name="eyebrow")
    require(len(eyebrows) == 1 and eyebrows[0].tag == "p",
            f"Expected exactly one p.eyebrow on {route}; found {len(eyebrows)}")
    eyebrow = eyebrows[0]
    require(eyebrow.attrs == {"class": "eyebrow"}, f"Eyebrow attributes differ on {route}: {eyebrow.attrs}")
    require(not eyebrow.element_children(), f"Eyebrow must remain plain text on {route}")
    require(normalized(eyebrow.text()) == EYEBROW_TEXT, f"Eyebrow text differs on {route}: {eyebrow.text()!r}")

    footers = parser.elements("footer", "site-footer")
    require(len(footers) == 1, f"Expected exactly one footer.site-footer on {route}; found {len(footers)}")
    footer = footers[0]
    require(footer.attrs == {"class": "site-footer"}, f"Footer attributes differ on {route}: {footer.attrs}")
    footer_children = footer.element_children()
    require(len(footer_children) == 1 and footer_children[0].tag == "a",
            f"Footer must contain exactly one ordinary Home anchor on {route}")
    footer_link = footer_children[0]
    require(footer_link.attrs == {"href": "/"}, f"Footer-link attributes differ on {route}: {footer_link.attrs}")
    require(not footer_link.element_children(), f"Footer link must remain plain anchor text on {route}")
    require(normalized(footer.text()) == FOOTER_TEXT, f"Footer text differs on {route}: {footer.text()!r}")


def machine_surface_checks(site_root: Path, parser: DocumentParser, route: str, html: str) -> None:
    actual_alternates = [public_path(route, reference) for reference in parser.json_alternates]
    expected_alternate = MACHINE_SURFACES.get(route)
    if expected_alternate is None:
        require(not actual_alternates, f"Unexpected machine alternate on {route}: {actual_alternates}")
        return

    require(
        actual_alternates == [expected_alternate],
        f"Machine alternate differs on {route}: {actual_alternates}",
    )
    manifest_path = site_root / expected_alternate.lstrip("/")
    require(manifest_path.is_file(), f"Machine surface is missing for {route}: {expected_alternate}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if route == "/faq/":
        expected_manifest = {
            "type": "faq",
            "canonical_url": "https://governedlogic.com/faq/",
            "publication_status": "withheld_pending_review",
            "notice": FAQ_NOTICE,
            "questions": [],
        }
        require("FAQPage" not in html, "FAQPage schema must remain absent until approved Q&A exists")
        require("application/ld+json" not in html, "FAQ JSON-LD must remain absent until approved Q&A exists")
    else:
        expected_manifest = {
            "type": "follow_the_chain_challenge",
            "canonical_url": "https://governedlogic.com/challenge/",
            "publication_status": "withheld_pending_review",
            "notice": CHALLENGE_NOTICE,
            "rules": [],
            "inputs": [],
            "outputs": [],
            "examples": [],
            "evaluation_criteria": [],
        }

    require(manifest == expected_manifest, f"Unreviewed machine content or shape on {route}: {manifest}")
    visible_paragraphs = [normalized(element.text()) for element in parser.elements("p")]
    require(
        manifest["notice"] in visible_paragraphs,
        f"Human and machine review notice differs on {route}",
    )


def publication_boundary_checks(parser: DocumentParser, route: str) -> None:
    """Freeze reviewed route copy and reject additional public claims."""
    bodies = parser.elements("body")
    require(len(bodies) == 1, f"Reviewed document must contain exactly one body on {route}")
    body = bodies[0]
    require(body.attrs == {}, f"Reviewed body attributes differ on {route}: {body.attrs}")
    require(
        not normalized("".join(child for child in body.children if isinstance(child, str))),
        f"Unexpected direct body text on {route}",
    )

    body_children = body.element_children()
    body_tags = [element.tag for element in body_children]
    if route == "/":
        require(
            body_tags == ["div", "header", "main", "footer"],
            f"Reviewed homepage landmarks differ: {body_tags}",
        )
        intro, _, content, _ = body_children
        require(
            intro.attrs == {"id": "site", "role": "region", "aria-label": "Governed Logic Reasoning Systems"},
            f"Reviewed opening container differs: {intro.attrs}",
        )
        expected_content_attrs = {"class": "site-content", "id": "explore"}
    else:
        require(
            body_tags == ["header", "main", "footer"],
            f"Reviewed page landmarks differ on {route}: {body_tags}",
        )
        _, content, _ = body_children
        expected_content_attrs = {"class": "inner-page"}

    require(
        len(parser.elements("main")) == 1 and parser.elements("main")[0] is content,
        f"Reviewed content must be the sole main landmark on {route}",
    )
    require(
        content.attrs == expected_content_attrs,
        f"Reviewed content attributes differ on {route}: {content.attrs}",
    )
    require(
        not normalized("".join(child for child in content.children if isinstance(child, str))),
        f"Unexpected direct reviewed-content text on {route}",
    )

    expected = REVIEWED_ROUTE_COPY[route]
    heading_tag, heading_text = expected["heading"]
    expected_tags = ["p", heading_tag, *(["p"] * len(expected["paragraphs"])), "div"]
    children = content.element_children()
    actual_tags = [element.tag for element in children]
    require(
        actual_tags == expected_tags,
        f"Reviewed content structure differs on {route}: {actual_tags}",
    )

    eyebrow, heading, *remainder = children
    require(
        eyebrow.attrs == {"class": "eyebrow"}
        and not eyebrow.element_children()
        and normalized(eyebrow.text()) == EYEBROW_TEXT,
        f"Reviewed eyebrow differs on {route}",
    )
    require(
        heading.attrs == {}
        and not heading.element_children()
        and normalized(heading.text()) == heading_text,
        f"Reviewed heading differs on {route}: {heading.text()!r}",
    )

    paragraphs = remainder[:-1]
    doors = remainder[-1]
    for paragraph, expected_text in zip(paragraphs, expected["paragraphs"]):
        require(
            paragraph.attrs == {}
            and not paragraph.element_children()
            and normalized(paragraph.text()) == expected_text,
            f"Reviewed paragraph text differs on {route}: {paragraph.text()!r}",
        )

    require(doors.attrs == {"class": "site-doors"}, f"Reviewed door group differs on {route}: {doors.attrs}")
    require(
        not normalized("".join(child for child in doors.children if isinstance(child, str))),
        f"Unexpected direct text in reviewed door group on {route}",
    )
    door_links = doors.element_children()
    require(
        len(door_links) == len(expected["doors"]) and all(link.tag == "a" for link in door_links),
        f"Reviewed door count or structure differs on {route}",
    )
    for link, (href, label) in zip(door_links, expected["doors"]):
        require(link.attrs == {"href": href}, f"Reviewed door attributes differ on {route}: {link.attrs}")
        link_children = link.element_children()
        require(
            len(link_children) == 1
            and link_children[0].tag == "span"
            and link_children[0].attrs == {}
            and not link_children[0].element_children()
            and normalized(link_children[0].text()) == "→"
            and normalized(link.text()) == f"{label} →",
            f"Reviewed door label or arrow differs for {href} on {route}: {link.text()!r}",
        )


def local_checks(site_root: Path, exact_artifact: bool) -> None:
    missing = [relative for relative in PUBLIC_FILES if not (site_root / relative).is_file()]
    require(not missing, "Missing public files: " + ", ".join(missing))

    if exact_artifact:
        actual = {
            path.relative_to(site_root).as_posix()
            for path in site_root.rglob("*")
            if path.is_file()
        }
        expected = set(PUBLIC_FILES)
        require(
            actual == expected,
            f"Artifact boundary differs; extra={sorted(actual - expected)}, missing={sorted(expected - actual)}",
        )

    for route, relative in ROUTES.items():
        html_path = site_root / relative
        html_bytes = html_path.read_bytes()
        actual_blob_id = git_blob_id(html_bytes)
        require(
            actual_blob_id == REVIEWED_HTML_BLOB_IDS[relative],
            f"Reviewed HTML bytes differ on {route}: {actual_blob_id}",
        )
        html = html_bytes.decode("utf-8")
        parser = DocumentParser()
        parser.feed(html)
        parser.close()
        expected_canonical = "https://governedlogic.com" + route
        require(parser.canonical == expected_canonical, f"Canonical differs for {route}: {parser.canonical}")
        expected_robots = "index,follow" if route == "/" else "noindex,follow"
        require(parser.robots == expected_robots, f"Robots directive differs for {route}: {parser.robots}")
        require(not any(link.lower().startswith("javascript:") for link in parser.links), f"Unsafe link on {route}")
        for reference in parser.stylesheets + parser.scripts:
            require(
                not reference.startswith(("http://", "https://", "//")),
                f"Unreviewed external runtime dependency {reference} on {route}",
            )
            path = public_path(route, reference)
            if path:
                require((site_root / path.lstrip("/")).is_file(), f"Missing asset {reference} used by {route}")
        shell_checks(parser, route)
        machine_surface_checks(site_root, parser, route, html)
        publication_boundary_checks(parser, route)

        if route == "/":
            require("#explore" in parser.links and 'id="explore"' in html, "Explore target is incomplete")
            require('class="semantic-title">Governed Logic' in html, "Semantic company identity is missing")
            require("Reasoning Systems" in html, "Company identity subtitle is missing")
            require(
                "GROUND → TRUTH → LOGIC → REASONING → INTELLIGENCE" in html,
                "Canonical reasoning sequence is missing",
            )
            doors = parser.elements("div", "site-doors")
            require(len(doors) == 1, "Homepage must contain exactly one primary door group")
            door_links = [
                element.attrs.get("href")
                for element in doors[0].element_children()
                if element.tag == "a"
            ]
            require(
                door_links == ["/challenge/", "/company/", "/research/", "/library/"],
                f"Homepage primary doors differ: {door_links}",
            )
        else:
            doors = parser.elements("div", "site-doors")
            require(len(doors) == 1, f"Expected exactly one page-flow door group on {route}")
            door_links = tuple(
                element.attrs.get("href")
                for element in doors[0].element_children()
                if element.tag == "a"
            )
            require(
                door_links == INNER_PAGE_DOORS[route],
                f"Page-flow destinations differ on {route}: {door_links}",
            )
            require(route not in door_links, f"Page-flow card must not link {route} to itself")

    sitemap = (site_root / "sitemap.xml").read_text(encoding="utf-8")
    require(sitemap.count("<url>") == 1, "Sitemap must expose only the indexed root route")
    require("<loc>https://governedlogic.com/</loc>" in sitemap, "Sitemap root URL differs")

    opening = (site_root / "assets/opening.js").read_text(encoding="utf-8")
    opening_css = (site_root / "assets/opening.css").read_text(encoding="utf-8").replace(" ", "")
    navigation_css = (site_root / "assets/site-navigation.css").read_text(encoding="utf-8").replace(" ", "")
    for contract in (
        "const TIMELINE",
        "starStart:2",
        "const globeReadability=sphere*(1-materialize);",
        "element.classList.add('is-finished')",
        "element.remove()",
        "catch{removeIntro();}",
        "prefers-reduced-motion: reduce",
    ):
        require(contract in opening, f"Opening contract missing: {contract}")
    require("@media(prefers-reduced-motion:reduce)" in opening_css, "Reduced-motion CSS bypass is missing")
    require("#glIntro{display:none!important}" in opening_css, "Reduced-motion overlay removal is missing")
    require("fetch(" not in opening and "new Image(" not in opening, "Opening may not load an unreviewed external asset")
    require(
        "const count=Math.min(window.innerWidth,window.innerHeight)<=600?3200:6000;" in opening,
        "Opening particle budget must use the smaller initial viewport dimension",
    )
    bypass_index = opening.index("if(motion.matches || document.hidden)return;")
    particle_index = opening.index("const count=Math.min(window.innerWidth,window.innerHeight)<=600?3200:6000;")
    frame_index = opening.index("function frame(now)")
    require(
        bypass_index < particle_index < frame_index,
        "Intro-only particles must initialize after the reduced-motion/hidden bypass and before rendering",
    )
    require('a[aria-current="page"]' in navigation_css, "Current-page navigation treatment is missing")
    require("min-height:44px" in navigation_css, "Mobile navigation tap target is undersized")
    require(
        "grid-template-columns:repeat(2,minmax(0,1fr))" in navigation_css,
        "Mobile navigation is not the reviewed two-column matrix",
    )
    require(
        'nava[href="/faq/"]{grid-column:1/-1;justify-self:center;width:calc(50%-4px)}' in navigation_css,
        "Mobile FAQ navigation item is not centered across the final row",
    )
    require("@media(forced-colors:active)" in navigation_css, "Forced-colors navigation fallback is missing")
    homepage = (site_root / "index.html").read_text(encoding="utf-8")
    opening_css_source = (site_root / "assets/opening.css").read_text(encoding="utf-8")
    earth_renderer = (site_root / "assets/earth-renderer.js").read_text(encoding="utf-8")
    require(
        'href="assets/materials/cinzel.ttf"' in homepage,
        "Homepage font preload differs from the reviewed asset graph",
    )
    require(
        "url('materials/cinzel.ttf')" in opening_css_source,
        "Opening font reference differs from the reviewed asset graph",
    )
    for texture in ("earth-day.jpg", "earth-night.jpg", "earth-clouds.jpg"):
        require(
            f"materials/{texture}" in earth_renderer,
            f"Earth renderer is missing reviewed texture {texture}",
        )
    timeline = {
        name: float(value)
        for name, value in re.findall(r"\b([a-zA-Z]+(?:Start|End|At)|deadline):(\d+(?:\.\d+)?)", opening)
    }
    required_times = {
        "starStart", "starEnd", "burstStart", "burstEnd", "orbitStart", "orbitEnd",
        "petalStart", "petalEnd", "greenStart", "greenEnd", "sphereStart", "sphereEnd",
        "materialStart", "materialEnd", "settleStart", "settleEnd", "identityStart",
        "identityEnd", "finalAt", "deadline",
    }
    require(required_times.issubset(timeline), "Opening timeline is incomplete")
    for start, end in (
        ("starStart", "starEnd"), ("burstStart", "burstEnd"), ("orbitStart", "orbitEnd"),
        ("petalStart", "petalEnd"), ("greenStart", "greenEnd"), ("sphereStart", "sphereEnd"),
        ("materialStart", "materialEnd"), ("settleStart", "settleEnd"),
        ("identityStart", "identityEnd"),
    ):
        require(timeline[start] < timeline[end], f"Opening timeline reverses {start}/{end}")
    require(10 <= timeline["finalAt"] <= 14.5, "Opening lifecycle is outside the bounded deliberate target")
    require(
        timeline["identityEnd"] < timeline["finalAt"] < timeline["deadline"]
        <= min(timeline["finalAt"] + 1.5, 15.5),
        "Opening completion or fail-open timing differs",
    )


def request_status(url: str) -> tuple[int, bytes]:
    request = Request(url, headers={"User-Agent": "GovernedLogic-release-check/1.0", "Cache-Control": "no-cache"})
    try:
        with urlopen(request, timeout=20) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()


def live_checks(base_url: str, attempts: int, delay: float) -> None:
    base = base_url.rstrip("/") + "/"
    last_errors: list[str] = []
    for attempt in range(1, attempts + 1):
        errors: list[str] = []
        cache_token = f"{int(time.time())}-{attempt}"
        try:
            for route in ROUTES:
                url = urljoin(base, route.lstrip("/")) + f"?release_check={cache_token}"
                status, _ = request_status(url)
                if status != 200:
                    errors.append(f"{route} returned {status}")
            for relative in PUBLIC_FILES:
                public_url = urljoin(base, relative) + f"?release_check={cache_token}"
                status, deployed = request_status(public_url)
                if status != 200:
                    errors.append(f"/{relative} returned {status}")
                    continue
                expected = (ROOT / relative).read_bytes()
                if deployed != expected:
                    errors.append(f"/{relative} differs from the reviewed artifact")
            for route in WITHHELD_URLS:
                url = urljoin(base, route.lstrip("/")) + f"?release_check={cache_token}"
                status, _ = request_status(url)
                if status != 404:
                    errors.append(f"withheld {route} returned {status}, expected 404")
        except (URLError, TimeoutError) as error:
            errors.append(str(error))
        if not errors:
            print(
                f"Live release boundary passed on attempt {attempt}: "
                f"{len(ROUTES)} routes available, {len(WITHHELD_URLS)} withheld paths absent."
            )
            return
        last_errors = errors
        if attempt < attempts:
            time.sleep(delay)
    raise AssertionError("Live checks failed: " + "; ".join(last_errors))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT), help="Repository or staged artifact root")
    parser.add_argument("--artifact", action="store_true", help="Require an exact allowlisted artifact")
    parser.add_argument("--live", help="Also verify the deployed base URL")
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--delay", type=float, default=10)
    args = parser.parse_args()
    local_checks(Path(args.root).resolve(), args.artifact)
    if args.live:
        live_checks(args.live, max(1, args.attempts), max(0, args.delay))
    print("Current public-release acceptance passed.")


if __name__ == "__main__":
    main()
