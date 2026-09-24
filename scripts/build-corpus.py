#!/usr/bin/env python3
"""Derive discovery from canonical HTML. No dependencies, network, or publication action.

Run from any directory: python scripts/build-corpus.py
The HTML contains the words and metadata; generated files are never editorial sources.
"""
from __future__ import annotations

import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET

SITE = "https://governedlogic.com"
ROOT = Path(__file__).resolve().parents[1]
ATOM = "http://www.w3.org/2005/Atom"
SITEMAP = "http://www.sitemaps.org/schemas/sitemap/0.9"
GENERATOR = "scripts/build-corpus.py v1"
TEXT_SCOPE = "main element and homepage hero; decoded text nodes; block separators; NFC; whitespace collapsed; UTF-8; extractor v1"
# These routes were already public at the v19.2 baseline. This is a migration
# boundary, not a second content registry. New objects must declare approval.
LEGACY_PATHS = {
    "index.html", "mechanism.html", "concepts/index.html", "sources/index.html",
    "publication/index.html", "concepts/governed-logic/index.html",
    "concepts/governed-intelligence/index.html",
    "concepts/alpha-and-omega-reasoning/index.html",
    "concepts/governing-referent/index.html",
    "concepts/sufficient-grounding/index.html", "concepts/ultimate-grounding/index.html",
}
GENERATED_PATHS = {"library/index.html"}
LEGACY_ASSETS = {"assets/releases/v18.1-alignment.jpg", "assets/releases/v18.2-origin.jpg",
                 "assets/governed-logic-mark.webp", "assets/business.css", "assets/the-groundless-machine.webp",
                 "assets/publication.css", "assets/gl-reasoning-systems.webp", "assets/origin.js"}
KINDS = {"article", "video", "transcript", "definition", "principle", "quote", "thought",
         "demonstration", "test", "research", "visualization", "presentation", "treatise",
         "business", "product", "service", "page", "concept"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
BLOCKS = {"address", "article", "aside", "blockquote", "br", "dd", "div", "dl", "dt", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "li", "main", "nav", "ol", "p", "pre", "section", "table", "td", "th", "tr", "ul", "textarea"}


def normalized(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class Node:
    def __init__(self, tag, attrs=(), parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()

    def find(self, tag=None, **attrs):
        return next((node for node in self.walk() if (tag is None or node.tag == tag)
                     and all(node.attrs.get(key) == value for key, value in attrs.items())), None)

    def text(self):
        if self.tag in {"script", "style", "template", "nav", "button"} or "hidden" in self.attrs or self.attrs.get("aria-hidden") == "true":
            return ""
        chunks = []
        for child in self.children:
            if isinstance(child, str):
                chunks.append(child)
            else:
                value = child.text()
                chunks.append((" " + value + " ") if child.tag in BLOCKS else value)
        return normalized("".join(chunks))

    def raw_text(self):
        return "".join(child if isinstance(child, str) else child.raw_text() for child in self.children)


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, value):
        self.stack[-1].children.append(value)


class ExtractV1(HTMLParser):
    """Preserve the published v19.1/v19.2 text hashing algorithm byte for byte."""
    def __init__(self):
        super().__init__(); self.active=False; self.parts=[]; self.skip=0; self.active_tag=None
    def handle_starttag(self,t,a):
        if t=='main' or (t=='header' and dict(a).get('class')=='hero'):
            self.active=True; self.active_tag=t
        if self.active and t in ('script','style'): self.skip+=1
        if self.active and t in ('p','br','h1','h2','h3','li','section','blockquote'): self.parts.append(' ')
    def handle_endtag(self,t):
        if t==self.active_tag: self.active=False; self.active_tag=None
        if self.active and t in ('script','style'): self.skip=max(0,self.skip-1)
        if self.active: self.parts.append(' ')
    def handle_data(self,d):
        if self.active and not self.skip: self.parts.append(d)


def text_hash(source):
    parser = ExtractV1()
    parser.feed(source)
    return digest(normalized("".join(parser.parts)).encode("utf-8"))


def route(path):
    name = path.as_posix() if isinstance(path, Path) else path
    if name == "index.html":
        return "/"
    if name.endswith("/index.html"):
        return "/" + name[:-10]
    return "/" + name


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def json_nodes(document):
    nodes = []
    for tag in document.root.walk():
        if tag.tag == "script" and tag.attrs.get("type") == "application/ld+json":
            payload = json.loads(tag.raw_text())
            values = payload if isinstance(payload, list) else [payload]
            for value in values:
                nodes.extend(value.get("@graph", [value]))
    return nodes


def types(node):
    value = node.get("@type", [])
    return [value] if isinstance(value, str) else value


def relative_url(url):
    parsed = urlsplit(url)
    return parsed.path + ("?" + parsed.query if parsed.query else "") + ("#" + parsed.fragment if parsed.fragment else "")


def version_library_assets(source, root=ROOT):
    """Version only the library's optional search assets on generated pages."""
    def version_asset(match):
        asset = match.group("asset")
        version = digest((root / "assets" / asset).read_bytes())[:16]
        return match.group("prefix") + "/assets/" + asset + "?v=" + version + match.group("quote")
    return re.sub(r'''(?P<prefix>\b(?:src|href)=["'])/assets/(?P<asset>library\.(?:css|js))(?:\?[^"']*)?(?P<quote>["'])''', version_asset, source)


def load_pages(root):
    pages, skipped, warnings = [], [], []
    for file in sorted(root.rglob("*.html")):
        path = file.relative_to(root).as_posix()
        if path in GENERATED_PATHS or any(part.startswith(".") for part in file.relative_to(root).parts):
            continue
        if file.relative_to(root).parts[0] in {"scripts", "tests", "templates", "node_modules", "drafts"}:
            skipped.append(path)
            continue
        source = file.read_text(encoding="utf-8")
        doc = Document(source)
        meta = {node.attrs.get("name", node.attrs.get("property")): node.attrs.get("content", "")
                for node in doc.root.walk() if node.tag == "meta"}
        status = meta.get("gl-status", "legacy-published" if path in LEGACY_PATHS else "draft")
        if status not in {"approved", "published", "legacy-published"}:
            skipped.append(path)
            continue
        if status == "legacy-published" and path not in LEGACY_PATHS:
            raise ValueError(f"{path}: legacy-published is reserved for the inspected v19.2 baseline")
        source = version_library_assets(source, root)
        doc = Document(source)
        canonical = next((node.attrs.get("href") for node in doc.root.walk()
                          if node.tag == "link" and "canonical" in node.attrs.get("rel", "").split()), None)
        if not canonical and path == "mechanism.html":
            canonical = SITE + route(path)
        if not canonical:
            raise ValueError(f"{path}: missing canonical URL")
        expected = SITE + route(path)
        if canonical != expected:
            raise ValueError(f"{path}: canonical {canonical!r} must match its stable route {expected!r}")
        ld = json_nodes(doc)
        entity = next((node for node in ld if node.get("url") == canonical and
                       any(kind in types(node) for kind in ["WebPage", "Article", "CreativeWork", "VideoObject", "ScholarlyArticle"])), {})
        page_nodes = [node for node in ld if node.get("url") == canonical or node.get("@id") == canonical + "#page"]
        combined = {}
        for node in page_nodes:
            combined.update(node)
        main = doc.root.find("main") or doc.root.find("body")
        if not main:
            raise ValueError(f"{path}: missing readable body")
        h1 = main.find("h1") or doc.root.find("h1")
        title = entity.get("name") or (h1.text() if h1 else None) or meta.get("og:title")
        if not title:
            raise ValueError(f"{path}: missing visible title")
        nodes = [node for node in doc.root.walk() if node.tag == "main" or
                 (node.tag == "header" and "hero" in node.attrs.get("class", "").split())]
        text = normalized(" ".join(node.text() for node in nodes)) or main.text()
        author = meta.get("author")
        published = meta.get("gl-date-published") or entity.get("datePublished")
        modified = meta.get("gl-date-modified") or entity.get("dateModified")
        description = meta.get("description", "")
        if description and normalized(description) not in text:
            if path not in LEGACY_PATHS:
                raise ValueError(f"{path}: description must be an exact visible sentence")
            warnings.append(f"Legacy metadata preserved: {path} description is not an exact visible passage; omitted from discovery excerpts.")
        if path not in LEGACY_PATHS:
            for label, value in {"author": author, "gl-type": meta.get("gl-type"), "datePublished": published,
                                 "dateModified": modified, "gl-approval": meta.get("gl-approval"),
                                 "description": description, "structured page": entity}.items():
                if not value:
                    raise ValueError(f"{path}: approved canonical HTML requires {label}")
            if meta["gl-type"] not in KINDS:
                raise ValueError(f"{path}: unsupported gl-type {meta['gl-type']!r}")
            if not h1 or normalized(title) != h1.text():
                raise ValueError(f"{path}: structured title must equal visible h1")
            for label, value in [("datePublished", published), ("dateModified", modified)]:
                if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:Z|[+-]\d\d:\d\d)", value):
                    raise ValueError(f"{path}: {label} requires an actual event timestamp with timezone")
                from datetime import datetime
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            if datetime.fromisoformat(modified.replace("Z", "+00:00")) < datetime.fromisoformat(published.replace("Z", "+00:00")):
                raise ValueError(f"{path}: revision date precedes publication date")
            identity = entity.get("author", {})
            if isinstance(identity, dict) and identity.get("@id"):
                identity = next((node for node in ld if node.get("@id") == identity["@id"] and node.get("name")), identity)
            author_name = identity.get("name") if isinstance(identity, dict) else identity
            if author_name != author:
                raise ValueError(f"{path}: HTML author and structured author must agree")
        for key, value in [("datePublished", published), ("dateModified", modified)]:
            if entity.get(key) and entity[key] != value:
                raise ValueError(f"{path}: {key} conflicts between HTML metadata and structured data")
        if meta.get("og:url", canonical) != canonical:
            raise ValueError(f"{path}: og:url differs from canonical URL")
        if entity.get("description") and description and entity["description"] != description:
            if path not in LEGACY_PATHS:
                raise ValueError(f"{path}: HTML and structured descriptions differ")
            warnings.append(f"Legacy metadata preserved: {path} HTML and structured descriptions differ.")
        kind = meta.get("gl-type") or ("concept" if any("DefinedTerm" in types(node) for node in ld) else "page")
        relations = {key: combined[key] for key in ["about", "citation", "isBasedOn", "isPartOf", "mainEntity", "associatedMedia", "hasPart"] if key in combined}
        links = sorted({urljoin(canonical, node.attrs["href"]) for node in main.walk()
                        if node.tag == "a" and node.attrs.get("href") and not node.attrs["href"].startswith(("mailto:", "tel:", "javascript:"))})
        record = {"id": canonical, "title": title, "url": canonical, "path": route(path), "type": kind,
                  "canonicalUrl": canonical, "sourcePath": path, "text": text,
                  "sha256_html": digest(source.encode("utf-8")), "sha256_text": text_hash(source),
                  "text_hash_scope": TEXT_SCOPE, "links": links}
        for key, value in {"author": author, "datePublished": published, "dateModified": modified,
                           "version": meta.get("gl-version"), "approvalReference": meta.get("gl-approval"),
                           "description": description if normalized(description) in text else None,
                           "relationships": relations or None}.items():
            if value:
                record[key] = value
        record["status"] = "published" if path in LEGACY_PATHS else status
        pages.append({"record": record, "document": doc, "source": source, "meta": meta})
    urls = [page["record"]["url"] for page in pages]
    if len(urls) != len(set(urls)):
        raise ValueError("Duplicate canonical URL")
    return pages, skipped, warnings


def discovery_records(pages):
    records = []
    for page in pages:
        record, doc = page["record"], page["document"]
        records.append(record)
        if record["sourcePath"] == "index.html":
            main = doc.root.find("main")
            if main:
                for node in main.walk():
                    anchor = node.attrs.get("id")
                    if not anchor or node.tag not in {"section", "article", "aside"}:
                        continue
                    heading = next((child for child in node.walk() if child.tag in {"h2", "h3"}), None)
                    if not heading:
                        continue
                    url = record["url"] + "#" + anchor
                    records.append({"id": url, "url": url, "path": "/#" + anchor, "title": heading.text(),
                                    "type": "section", "text": node.text(), "canonicalUrl": record["url"],
                                    "sourcePath": "index.html", "fragment": anchor, "status": "published"})
        if record["sourcePath"] == "sources/index.html":
            for node in doc.root.walk():
                if node.tag != "section" or not node.attrs.get("id"):
                    continue
                heading = node.find("h2")
                source = next((child for child in node.walk() if child.tag == "a" and
                               urlsplit(child.attrs.get("href", "")).path.lower().endswith((".pdf", ".txt"))), None)
                if not heading or not source:
                    continue
                url = urljoin(record["url"], source.attrs["href"])
                records.append({"id": url, "url": url, "path": relative_url(url), "title": heading.text(),
                                "type": "source", "text": node.text(), "canonicalUrl": url,
                                "recordUrl": record["url"] + "#" + node.attrs["id"],
                                "sourcePath": "sources/index.html", "status": "published"})
    return records


def library_html(records, root=ROOT):
    rows = []
    labels = {"concept": "Concept", "section": "Homepage section", "source": "Source edition", "page": "Page"}
    for record in records:
        title, path = html.escape(record["title"]), html.escape(record["path"], quote=True)
        label = labels.get(record["type"], record["type"].replace("-", " ").capitalize())
        detail = f'<span class="library-item-kind">{html.escape(label)}</span>'
        if record["type"] == "source":
            detail += f' · <a class="library-source-record" href="{html.escape(relative_url(record["recordUrl"]), quote=True)}">Source record</a>'
        rows.append(f'<li class="library-item" data-record="{html.escape(record["id"], quote=True)}" data-kind="{record["type"]}"><div>{detail}</div><a class="library-item-link" href="{path}">{title}<span aria-hidden="true">↗</span></a><span class="library-item-path">{html.escape(record["path"])}</span></li>')
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "@id": SITE + "/library/#page",
          "url": SITE + "/library/", "name": "Library", "isPartOf": {"@id": SITE + "/#website"},
          "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1,
               "name": record["title"], "url": record["url"]} for i, record in enumerate(records)]}}
    payload = json.dumps(ld, ensure_ascii=False).replace("<", "\\u003c")
    kinds = sorted({record["type"] for record in records})
    options = ''.join(f'<option value="{kind}">{html.escape(labels.get(kind, kind.capitalize()))}</option>' for kind in kinds)
    source = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Library — Governed Logic</title>
<meta name="theme-color" content="#050505"><meta name="gl-generated" content="{GENERATOR}"><link rel="canonical" href="{SITE}/library/">
<link rel="alternate" type="application/atom+xml" href="/feed.xml" title="Governed Logic publications"><link rel="alternate" type="application/json" href="/publication/catalog.json" title="Canonical catalog">
<link rel="stylesheet" href="/assets/publication.css"><link rel="stylesheet" href="/assets/library.css">
<script type="application/ld+json">{payload}</script><script defer src="/assets/library.js"></script></head>
<body class="document-page library-page"><a class="skip-link" href="#library-main">Skip to content</a>
<header class="document-header"><a href="/">Governed Logic<br>Reasoning Systems</a><a href="/concepts/">Follow the chain →</a></header>
<main class="document-main library-main" id="library-main"><div class="eyebrow">Governed Logic Reasoning Systems</div><h1>Library</h1>
<form class="library-search" role="search" action="/library/" method="get"><div class="library-query"><label for="library-query">Search pages, sections, and source editions</label><input id="library-query" type="search" name="q" placeholder="Enter words or a title" autocomplete="off" spellcheck="false" aria-controls="library-results" aria-describedby="library-search-mode"></div><div class="library-filter"><label for="library-kind">Show</label><select id="library-kind" name="type" aria-controls="library-results"><option value="">Everything</option>{options}</select></div><button type="submit">Search</button></form>
<p class="library-search-mode" id="library-search-mode">All published records are linked below. Search is available when JavaScript is enabled.</p>
<div class="library-result-bar"><p id="library-count" role="status" aria-live="polite" aria-atomic="true">{len(records)} records</p><button type="button" id="library-clear" hidden>Clear search</button></div>
<ul class="library-results" id="library-results">{''.join(rows)}</ul><p class="library-empty" id="library-empty" hidden>No matching records. Try another word or clear the search.</p>
</main><footer class="document-footer"><span>Governed Logic Reasoning Systems</span><span><a href="/sources/">Sources</a> · <a href="/publication/">Publication record</a> · <a href="/publication/catalog.json">Catalog</a></span></footer>
</body></html>
'''
    return version_library_assets(source, root).encode("utf-8")


def feed_bytes(root, pages):
    ET.register_namespace("", ATOM)
    tag = lambda name: "{" + ATOM + "}" + name
    old = ET.parse(root / "feed.xml").getroot()
    old_entries = {entry.findtext(tag("id")): entry for entry in old.findall(tag("entry"))}
    feed = ET.Element(tag("feed"))
    for child in old:
        if child.tag != tag("entry"):
            feed.append(child)
    updates = []
    for page in pages:
        record = page["record"]
        previous = old_entries.get(record["url"])
        if previous is not None:
            # Preserve release-event precision that legacy HTML records only by day.
            entry = ET.fromstring(ET.tostring(previous))
            entry.find(tag("title")).text = record["title"]
            summary = entry.find(tag("summary"))
            if summary is not None and record.get("description"):
                summary.text = record["description"]
            for field in ("published", "updated"):
                date_key = "datePublished" if field == "published" else "dateModified"
                explicit = record.get(date_key)
                element = entry.find(tag(field))
                if explicit and "T" in explicit:
                    element.text = explicit
            feed.append(entry)
            updates.append(entry.findtext(tag("updated")))
        elif record.get("datePublished") and "T" in record["datePublished"]:
            entry = ET.SubElement(feed, tag("entry"))
            for name, value in [("id", record["url"]), ("title", record["title"]),
                                ("published", record["datePublished"]), ("updated", record["dateModified"])]:
                ET.SubElement(entry, tag(name)).text = value
            ET.SubElement(entry, tag("link"), {"href": record["url"]})
            author = ET.SubElement(entry, tag("author"))
            ET.SubElement(author, tag("name")).text = record["author"]
            if record.get("description"):
                ET.SubElement(entry, tag("summary")).text = record["description"]
            updates.append(record["dateModified"])
    # Build time is not a publication event. Keep the actual latest source event.
    if updates:
        from datetime import datetime
        key = lambda value: datetime.fromisoformat(value.replace("Z", "+00:00"))
        feed.find(tag("updated")).text = max(updates, key=key)
    return ET.tostring(feed, encoding="UTF-8", xml_declaration=True) + b"\n"


def sitemap_bytes(pages):
    ET.register_namespace("", SITEMAP)
    tag = lambda name: "{" + SITEMAP + "}" + name
    root = ET.Element(tag("urlset"))
    for page in pages:
        record = page["record"]
        item = ET.SubElement(root, tag("url"))
        ET.SubElement(item, tag("loc")).text = record["url"]
        if record.get("dateModified"):
            ET.SubElement(item, tag("lastmod")).text = record["dateModified"]
    item = ET.SubElement(root, tag("url"))
    ET.SubElement(item, tag("loc")).text = SITE + "/library/"
    return ET.tostring(root, encoding="UTF-8", xml_declaration=True) + b"\n"


def outputs(root):
    pages, skipped, warnings = load_pages(root)
    records = discovery_records(pages)
    manifest = json.loads((root / "publication/manifest.json").read_text(encoding="utf-8"))
    catalog = {"version": 1, "corpusVersion": manifest["version"], "generator": GENERATOR,
               "source": "Canonical HTML; generated views are not editorial sources.",
               "records": [{key: value for key, value in record.items() if key != "text"} for record in records]}
    search = {"version": 1, "corpusVersion": manifest["version"], "generator": GENERATOR, "records": records}
    generated = {"library/index.html": library_html(records, root),
                 "publication/catalog.json": json_bytes(catalog), "publication/search-index.json": json_bytes(search),
                 "feed.xml": feed_bytes(root, pages), "sitemap.xml": sitemap_bytes(pages)}
    previous = {page["path"]: page for page in manifest["pages"]}
    preserved_order = {page["path"]: i for i, page in enumerate(manifest["pages"])}
    new_pages = []
    for page in sorted(pages, key=lambda page: (preserved_order.get(page["record"]["sourcePath"], 10000), page["record"]["sourcePath"])):
        record = page["record"]
        item = dict(previous.get(record["sourcePath"], {}))
        item.update({"url": record["url"], "path": record["sourcePath"], "title": record["title"],
                     "sha256_html": record["sha256_html"], "sha256_text": record["sha256_text"], "text_hash_scope": TEXT_SCOPE})
        for key in ["datePublished", "dateModified", "version"]:
            if record.get(key):
                item[key] = record[key]
        if record.get("description"):
            item["definition"] = record["description"]
        if record["sourcePath"] not in LEGACY_PATHS:
            item["status"] = "approved"
            item["approvalReference"] = record["approvalReference"]
        new_pages.append(item)
    manifest["pages"] = new_pages
    manifest["discovery"] = {"generator": GENERATOR, "contentVersion": manifest["version"],
                              "releaseChannel": "production",
                              "catalog": SITE + "/publication/catalog.json", "searchIndex": SITE + "/publication/search-index.json",
                              "library": SITE + "/library/", "recordCount": len(records),
                              "generatedFiles": [{"path": path, "sha256": digest(raw)} for path, raw in generated.items()]}
    generated["publication/manifest.json"] = json_bytes(manifest)
    generated.update({page["record"]["sourcePath"]: page["source"].encode("utf-8") for page in pages})
    return generated, {"pages": len(pages), "records": len(records), "skipped": skipped, "warnings": warnings}


def local_path(root, url):
    parsed = urlsplit(url)
    if parsed.scheme not in {"", "http", "https"} or (parsed.netloc and parsed.netloc != "governedlogic.com"):
        return None
    path = unquote(parsed.path).lstrip("/")
    target = (root / path).resolve()
    if target != root.resolve() and root.resolve() not in target.parents:
        raise ValueError(f"Local URL leaves publication root: {url}")
    if target.is_dir() or parsed.path.endswith("/") or not path:
        target = target / "index.html"
    return target


def referenced_urls(source, base_url):
    document = Document(source)
    urls = set()
    for node in document.root.walk():
        for attr in ("href", "src", "poster", "data"):
            if node.attrs.get(attr):
                urls.add(urljoin(base_url, node.attrs[attr]))
        if node.attrs.get("srcset"):
            for candidate in node.attrs["srcset"].split(","):
                if candidate.strip():
                    urls.add(urljoin(base_url, candidate.strip().split()[0]))
    for value in re.findall(r'''url\(\s*['"]?([^\s)'";]+)''', source):
        urls.add(urljoin(base_url, value))
    return urls


def stage_site(root, target):
    """Create a fresh deployment package, never copy draft files or source tools."""
    import shutil
    root, target = root.resolve(), target.resolve()
    if target == root or root in target.parents:
        raise ValueError("The staging directory must be outside the authoring repository")
    if target.exists() and any(target.iterdir()):
        raise ValueError("Staging directory must be new or empty; reuse cannot leave stale unpublished files")
    pages, _, _ = load_pages(root)
    allowed_html = {page["record"]["sourcePath"] for page in pages} | GENERATED_PATHS
    paths = allowed_html | LEGACY_ASSETS | {"publication/catalog.json", "publication/search-index.json",
             "publication/manifest.json", "sitemap.xml", "feed.xml", "robots.txt"}
    paths |= {name for name in ["CNAME", ".nojekyll"] if (root / name).is_file()}
    queue = list(paths)
    visited = set()
    while queue:
        path = queue.pop()
        if path in visited:
            continue
        visited.add(path)
        file = root / path
        if not file.is_file():
            raise ValueError(f"Required public file missing: {path}")
        if file.suffix.lower() not in {".html", ".css"}:
            continue
        source = file.read_text(encoding="utf-8")
        for url in referenced_urls(source, SITE + route(path)):
            local = local_path(root, url)
            if local is None:
                continue
            rel = local.relative_to(root).as_posix()
            if local.suffix.lower() == ".html" and rel not in allowed_html:
                raise ValueError(f"{path}: public link reaches unapproved HTML {rel}")
            if rel not in paths:
                paths.add(rel)
                queue.append(rel)
    target.mkdir(parents=True, exist_ok=True)
    for path in sorted(paths):
        destination = target / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / path, destination)
    # GitHub Pages should serve these exact static bytes, without a Jekyll pass.
    (target / ".nojekyll").touch()
    return len(paths | {".nojekyll"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", help="Fail if generated views differ; write nothing.")
    parser.add_argument("--stage", type=Path, help="Create a fresh public-file-only deployment directory outside this repository.")
    args = parser.parse_args()
    if args.check and args.stage:
        parser.error("--check cannot write a staging directory")
    generated, report = outputs(args.root.resolve())
    changed = []
    for path, raw in generated.items():
        target = args.root / path
        if not target.exists() or target.read_bytes() != raw:
            changed.append(path)
            if not args.check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
    report.update({"mode": "check" if args.check else "build", "changed": changed})
    if args.stage:
        report["stagedFiles"] = stage_site(args.root, args.stage)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.check and changed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
