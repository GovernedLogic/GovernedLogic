import { chromium } from "@playwright/test";
import { createHash } from "node:crypto";
import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const PROJECTS = ["desktop-1440", "mobile-320", "mobile-390"];
const ROUTES = ["home", "challenge", "company", "research", "library", "faq"];
const outputRoot = path.resolve("visual-qa");
const cards = [];
const missing = [];
const screenshots = [];

for (const project of PROJECTS) {
  for (const route of ROUTES) {
    const relativePath = path.join("screenshots", project, route + ".png");
    const absolutePath = path.join(outputRoot, relativePath);
    try {
      await access(absolutePath);
      const bytes = await readFile(absolutePath);
      const digest = createHash("sha256").update(bytes).digest("hex");
      screenshots.push({
        project,
        route,
        path: relativePath.replaceAll("\\", "/"),
        sha256: digest
      });
      cards.push(
        '<article><h3>' + project + " · " + route + "</h3>"
        + '<img alt="' + project + " " + route + '" src="data:image/png;base64,'
        + bytes.toString("base64") + '"></article>'
      );
    } catch {
      missing.push(relativePath.replaceAll("\\", "/"));
    }
  }
}

await mkdir(outputRoot, { recursive: true });
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({
    viewport: { width: 1600, height: 1000 },
    colorScheme: "dark",
    reducedMotion: "reduce"
  });
  await page.setContent(
    '<!doctype html><html><head><meta charset="utf-8"><style>'
    + '*{box-sizing:border-box}html{background:#080b0e;color:#f5f7f8;font-family:Arial,sans-serif}'
    + 'body{margin:0;padding:32px}h1{font-size:30px;margin:0 0 8px}'
    + 'p{color:#bdc7ce;margin:0 0 28px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}'
    + 'article{background:#111820;border:1px solid #34424d;border-radius:8px;padding:12px;overflow:hidden}'
    + 'h3{font-size:16px;margin:0 0 10px;color:#e6eef4}'
    + 'img{display:block;width:100%;height:720px;object-fit:contain;object-position:top center;background:#000}'
    + '.warning{color:#ffcc85}</style></head><body>'
    + '<h1>Governed Logic visual QA</h1>'
    + '<p>Reduced-motion, loopback-only Chromium render evidence. '
    + screenshots.length + " of " + (PROJECTS.length * ROUTES.length) + " expected captures."
    + (missing.length ? '<br><span class="warning">Missing: ' + missing.join(", ") + "</span>" : "")
    + '</p><section class="grid">' + cards.join("") + "</section></body></html>",
    { waitUntil: "load" }
  );
  await page.screenshot({
    path: path.join(outputRoot, "contact-sheet.jpg"),
    type: "jpeg",
    quality: 58,
    fullPage: true,
    animations: "disabled",
    caret: "hide"
  });
} finally {
  await browser.close();
}

await writeFile(
  path.join(outputRoot, "manifest.json"),
  JSON.stringify({
    mode: "Chromium with prefers-reduced-motion: reduce",
    limitation: "Stable responsive layout only; full opening-animation timing is not verified.",
    expectedScreenshotCount: PROJECTS.length * ROUTES.length,
    screenshotCount: screenshots.length,
    missing,
    screenshots
  }, null, 2) + "\n",
  "utf8"
);

console.log("Visual contact sheet contains " + screenshots.length + " screenshots.");
