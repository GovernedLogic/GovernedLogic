import { chromium } from "@playwright/test";
import { createHash } from "node:crypto";
import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const PROJECTS = ["desktop-1440", "mobile-320", "mobile-390"];
const MOTION_PROJECTS = ["desktop-1440", "mobile-390"];
const ROUTES = ["home", "challenge", "company", "research", "about", "faq", "concepts", "concepts-governed-logic", "concepts-governed-intelligence", "concepts-ultimate-grounding", "concepts-alpha-and-omega-reasoning", "concepts-governing-referent", "concepts-sufficient-grounding", "mechanism.html", "sources", "articles-why-anything", "articles-integrity-in-artificial-intelligence", "library", "publication"];
const outputRoot = path.resolve("visual-qa");
const cards = [];
const missing = [];
const screenshots = [];
const motionScreenshots = [];
const motionCards = [];

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

for (const project of MOTION_PROJECTS) {
  const relativeManifest = path.join("motion", project, "frames.json");
  try {
    const sequence = JSON.parse(await readFile(path.join(outputRoot, relativeManifest), "utf8"));
    if (sequence.frames.length !== 12) throw new Error("Incomplete opening sequence");
    const sequenceCards = [];
    for (const frame of sequence.frames) {
      const relativePath = path.join("motion", project, frame.path);
      const bytes = await readFile(path.join(outputRoot, relativePath));
      const digest = createHash("sha256").update(bytes).digest("hex");
      if (digest !== frame.sha256) throw new Error("Opening capture hash mismatch");
      motionScreenshots.push({
        project,
        phase: frame.label,
        milliseconds: frame.at,
        overlayPresent: frame.overlayPresent,
        path: relativePath.replaceAll("\\", "/"),
        sha256: digest
      });
      sequenceCards.push(
        '<article><h3>' + (frame.at / 1000).toFixed(2) + " s · " + frame.label + "</h3>"
        + '<img alt="' + project + " opening at " + (frame.at / 1000).toFixed(2)
        + ' seconds" src="data:image/png;base64,' + bytes.toString("base64") + '"></article>'
      );
    }
    motionCards.push('<section><h2>' + project + '</h2><div class="grid">' + sequenceCards.join("") + '</div></section>');
  } catch {
    missing.push(relativeManifest.replaceAll("\\", "/"));
  }
}

await mkdir(outputRoot, { recursive: true });
const browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_BIN ? { executablePath: process.env.CHROMIUM_BIN } : {}) });
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
  await page.setContent(
    '<!doctype html><html><head><meta charset="utf-8"><style>'
    + '*{box-sizing:border-box}html{background:#050708;color:#f4f7f8;font-family:Arial,sans-serif}'
    + 'body{margin:0;padding:32px}h1{font-size:30px;margin:0 0 8px}h2{margin:36px 0 18px;font-size:22px}'
    + 'p{color:#bdc7ce;margin:0 0 28px;max-width:950px;line-height:1.5}'
    + '.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}'
    + 'article{background:#090c0e;border:1px solid #25333c;padding:12px;overflow:hidden}'
    + 'h3{font-size:16px;font-weight:400;margin:0 0 10px;color:#e6eef4}'
    + 'img{display:block;width:100%;height:420px;object-fit:contain;background:#000}'
    + '</style></head><body><h1>Governed Logic opening · chronological frames</h1>'
    + '<p>Normal-motion rendering at the displayed elapsed times. Each row reads left to right. '
    + 'The browser clock advances through the actual opening code; no alternate animation or testing mode is used. '
    + 'Review these frames together with the live opening to judge pacing and transitions.</p>'
    + motionCards.join("") + '</body></html>',
    { waitUntil: "load" }
  );
  await page.screenshot({
    path: path.join(outputRoot, "motion-contact-sheet.jpg"),
    type: "jpeg",
    quality: 78,
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
    sourceSha: process.env.SOURCE_SHA || null,
    mode: "Chromium reduced-motion layouts and clock-controlled normal-motion opening frames",
    limitation: "Opening evidence verifies chronological frames and completion; visual pacing and transitions still require human review.",
    expectedScreenshotCount: PROJECTS.length * ROUTES.length,
    screenshotCount: screenshots.length,
    expectedMotionScreenshotCount: MOTION_PROJECTS.length * 12,
    motionScreenshotCount: motionScreenshots.length,
    missing,
    screenshots,
    motionScreenshots
  }, null, 2) + "\n",
  "utf8"
);

console.log("Visual contact sheet contains " + screenshots.length + " screenshots.");
console.log("Opening contact sheet contains " + motionScreenshots.length + " chronological frames.");
if (missing.length) {
  throw new Error("Visual evidence is incomplete: " + missing.join(", "));
}
