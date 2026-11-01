import { expect, test } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const BASE_ORIGIN = "http://127.0.0.1:4173";
const ROUTES = [
  { path: "/", slug: "home" },
  { path: "/challenge/", slug: "challenge" },
  { path: "/concepts/ultimate-grounding/", slug: "ultimate-grounding" },
  { path: "/company/", slug: "company" },
  { path: "/research/", slug: "research" },
  { path: "/library/", slug: "library" },
  { path: "/faq/", slug: "faq" },
  // WEB-205/WEB-231: Paul's previous homepage main, kept byte-as-is.
  { path: "/page-two/", slug: "page-two" }
];
const EXPECTED_NAVIGATION = [
  { href: "/concepts/governed-logic/", label: "Governed Logic" },
  { href: "/concepts/ultimate-grounding/", label: "Ultimate Grounding" },
  { href: "/concepts/governed-intelligence/", label: "Governed Intelligence" },
  { href: "/company/", label: "Company" },
  { href: "/research/", label: "Research" }
];
// WEB-228/C9: the homepage carries the approved 2026-10-31 mockup header (provisional targets).
// Applications is on hold (C9, WEB-217): a visible, inert button outside any form, so it is not listed.
// WEB-223: Company (/company/) is one click from the homepage header at every width.
const HOME_NAVIGATION = [
  { href: "/", label: "Home" },
  { href: "/index.html#the-problem", label: "The Problem" },
  { href: "/research/", label: "Research" },
  { href: "/concepts/governed-logic/", label: "The Framework" },
  { href: "/about/", label: "About" },
  { href: "/company/", label: "Company" }
];

for (const routeDefinition of ROUTES) {
  test(routeDefinition.path + " has a usable reviewed shell", async ({ page }, testInfo) => {
    const blockedRequests = [];
    const consoleErrors = [];
    const pageErrors = [];
    const localRequestFailures = [];

    page.on("console", message => {
      if (message.type() === "error") {
        consoleErrors.push(message.text());
      }
    });
    page.on("pageerror", error => {
      pageErrors.push(error.message);
    });
    page.on("requestfailed", request => {
      if (request.url().startsWith(BASE_ORIGIN)) {
        localRequestFailures.push(request.url() + ": " + (request.failure()?.errorText || "unknown failure"));
      }
    });
    await page.route("**/*", async requestRoute => {
      const requestUrl = requestRoute.request().url();
      let origin;
      try {
        origin = new URL(requestUrl).origin;
      } catch {
        blockedRequests.push(requestUrl);
        await requestRoute.abort("blockedbyclient");
        return;
      }
      if (origin !== BASE_ORIGIN) {
        blockedRequests.push(requestUrl);
        await requestRoute.abort("blockedbyclient");
        return;
      }
      await requestRoute.continue();
    });

    const response = await page.goto(routeDefinition.path, { waitUntil: "networkidle" });
    expect(response, "navigation must return a response").not.toBeNull();
    expect(response.ok(), "route must return a successful response").toBe(true);
    await page.evaluate(async () => {
      await document.fonts.ready;
    });
    await page.locator("header.site-bar").scrollIntoViewIfNeeded();

    const primaryNavigation = page.locator('nav[aria-label="Primary"]');
    await expect(primaryNavigation).toHaveCount(1);
    await expect(primaryNavigation).toBeVisible();
    await expect(page.locator("main")).toHaveCount(1);
    await expect(page.getByRole("main")).toHaveCount(1);
    await expect(page.getByRole("main")).toBeVisible();

    if (routeDefinition.path === "/") {
      // WEB-215 + Paul's C8 ruling (2026-11-01, "drop the old opening"): no opening region; the hero h1 is the one h1.
      const openingRegion = page.getByRole("region", { name: "Governed Logic Reasoning Systems" });
      await expect(openingRegion).toHaveCount(0);
      await expect(page.locator("h1")).toHaveCount(1);
      await expect(page.locator("main #explore h1.gl-hero-title")).toHaveCount(1);
      // WEB-205/WEB-231: one GET-form button on the homepage reaches /page-two/.
      const pageTwoForms = page.locator('main form.gl-go[method="get"][action="/page-two/"]');
      await expect(pageTwoForms).toHaveCount(1);
      await expect(pageTwoForms.locator('button[type="submit"]')).toHaveText("See what we are building");
      // C9/WEB-217 and WEB-218: Applications and the Truth Governs Mathematics card are held: visible, inert, unlinked.
      const held = page.locator('button.gl-hold[aria-disabled="true"]');
      await expect(held).toHaveCount(2);
      await expect(page.locator("form button.gl-hold")).toHaveCount(0);
      // WEB-223/WEB-214: /company/ and the library (Search) are one click from the header, and the brand name shows.
      const header = page.locator("header.site-bar");
      await expect(header.locator('form.gl-go[action="/company/"] > button')).toBeVisible();
      await expect(header.locator('form.gl-go[action="/library/"] > button')).toBeVisible();
      await expect(header.locator(".gl-brand-name")).toBeVisible();
      // D8 (WEB-214/WEB-226): "Reasoning Systems" and the CTA show at every width; below 390px the CTA is a
      // compact arrow button that keeps its accessible name.
      await expect(header.locator(".site-brand small")).toBeVisible();
      await expect(header.locator(".gl-bar-cta")).toBeVisible();
      await expect(header.locator(".gl-bar-cta")).toHaveAccessibleName("Explore the Research");
    }

    if (routeDefinition.path === "/page-two/") {
      // WEB-205/WEB-231: page two carries the preserved homepage main and no opening region.
      await expect(page.locator("#site")).toHaveCount(0);
      await expect(page.locator("main.home-content #explore")).toHaveCount(1);
    }

    const isMobile = testInfo.project.name.startsWith("mobile-");
    // WEB-228/C9: the homepage header lists its own items; every other route keeps the reviewed shell.
    const expectedNavigation = routeDefinition.path === "/" ? HOME_NAVIGATION : EXPECTED_NAVIGATION;
    if (isMobile) {
      // The disclosure is gone. The five doors stay visible, each at least 44px, with no horizontal overflow.
      await expect(page.locator('nav[aria-label="Primary"] summary')).toHaveCount(0);
      await expect(page.locator('nav[aria-label="Primary"] details')).toHaveCount(0);
      const navButtons = page.locator('nav[aria-label="Primary"] form.gl-go > button');
      await expect(navButtons).toHaveCount(expectedNavigation.length); // WEB-228/C9: six on the homepage
      for (const button of await navButtons.all()) {
        await button.scrollIntoViewIfNeeded();
        await expect(button).toBeVisible();
        const box = await button.boundingBox();
        expect(box.width).toBeGreaterThanOrEqual(44);
        expect(box.height).toBeGreaterThanOrEqual(44);
      }
    }
    const metrics = await page.evaluate(
      ({ expectedNavigation, mobile }) => {
        const visible = element => {
          const style = getComputedStyle(element);
          const rect = element.getBoundingClientRect();
          return style.display !== "none"
            && style.visibility !== "hidden"
            && Number(style.opacity) > 0
            && rect.width > 0
            && rect.height > 0;
        };
        const normalize = value => value.replace(/\s+/g, " ").trim();
        const navigation = document.querySelector('nav[aria-label="Primary"]');
        const bar = navigation.closest("header");
        const mainElements = Array.from(document.querySelectorAll("main"));
        const navigationRect = navigation.getBoundingClientRect();
        const barRect = bar ? bar.getBoundingClientRect() : navigationRect;
        const links = Array.from(navigation.querySelectorAll("form.gl-go > button"));
        const place = link => {
          if (!bar || bar.scrollWidth <= bar.clientWidth + 1) return;
          const before = link.getBoundingClientRect();
          const host = bar.getBoundingClientRect();
          if (before.left < host.left - 0.5 || before.right > host.right + 0.5) {
            bar.scrollLeft += before.left - host.left;
          }
        };
        const linkMetrics = links.map(link => {
          place(link);
          const rect = link.getBoundingClientRect();
          const host = bar ? bar.getBoundingClientRect() : navigationRect;
          const centerX = Math.max(0, Math.min(innerWidth - 1, rect.left + rect.width / 2));
          const centerY = Math.max(0, Math.min(innerHeight - 1, rect.top + rect.height / 2));
          const hit = document.elementFromPoint(centerX, centerY);
          return {
            href: link.closest("form")?.getAttribute("action") || "",
            label: normalize(link.textContent || ""),
            visible: visible(link),
            focusable: link.matches("button") && link.tabIndex >= 0,
            insideViewport:
              rect.left >= -0.5
              && rect.right <= innerWidth + 0.5
              && rect.top >= -0.5
              && rect.bottom <= innerHeight + 0.5,
            insideNavigation:
              rect.left >= host.left - 0.5
              && rect.right <= host.right + 0.5
              && rect.top >= host.top - 0.5
              && rect.bottom <= host.bottom + 0.5,
            centerHit: hit === link || link.contains(hit),
            height: rect.height,
            width: rect.width,
            top: rect.top,
            right: rect.right,
            bottom: rect.bottom,
            left: rect.left
          };
        });
        if (bar) bar.scrollLeft = 0;
        const rests = links.map(link => {
          const rect = link.getBoundingClientRect();
          return {left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom};
        });
        const overlaps = [];
        for (let first = 0; first < rests.length; first += 1) {
          for (let second = first + 1; second < rests.length; second += 1) {
            const a = rests[first];
            const b = rests[second];
            const width = Math.min(a.right, b.right) - Math.max(a.left, b.left);
            const height = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
            if (width > 0.5 && height > 0.5) {
              overlaps.push([first, second]);
            }
          }
        }
        return {
          documentOverflow:
            document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
          bodyOverflow: document.body.scrollWidth > document.body.clientWidth + 1,
          navigationInsideViewport:
            barRect.left >= -0.5
            && barRect.right <= innerWidth + 0.5
            && barRect.top >= -0.5
            && barRect.bottom <= innerHeight + 0.5,
          navigationContentWithinBounds:
            linkMetrics.every(link => link.insideNavigation),
          visibleMainCount: mainElements.filter(visible).length,
          mainWithinHorizontalViewport: mainElements.every(element => {
            const rect = element.getBoundingClientRect();
            return rect.left >= -0.5 && rect.right <= innerWidth + 0.5;
          }),
          links: linkMetrics,
          overlaps,
          labelsAndRoutesMatch:
            linkMetrics.length === expectedNavigation.length
            && linkMetrics.every((link, index) =>
              link.href === expectedNavigation[index].href
              && link.label === expectedNavigation[index].label
            ),
          mobileTargetsMeetMinimum:
            !mobile || linkMetrics.every(link => link.height >= 43.5)
        };
      },
      { expectedNavigation, mobile: isMobile }
    );

    const screenshotDirectory = path.resolve(
      "visual-qa",
      "screenshots",
      testInfo.project.name
    );
    await mkdir(screenshotDirectory, { recursive: true });
    const screenshotPath = path.join(screenshotDirectory, routeDefinition.slug + ".png");
    await page.addStyleTag({
      content:
        "*,*::before,*::after{animation-duration:0s!important;animation-delay:0s!important;"
        + "transition-duration:0s!important;caret-color:transparent!important}"
    });
    await page.screenshot({
      path: screenshotPath,
      fullPage: true,
      animations: "disabled",
      caret: "hide"
    });
    await testInfo.attach(routeDefinition.slug + "-" + testInfo.project.name, {
      path: screenshotPath,
      contentType: "image/png"
    });

    expect(metrics.documentOverflow, "document must not overflow horizontally").toBe(false);
    expect(metrics.bodyOverflow, "body must not overflow horizontally").toBe(false);
    expect(metrics.navigationInsideViewport, "primary navigation must fit the viewport").toBe(true);
    expect(
      metrics.navigationContentWithinBounds,
      "primary navigation links must remain inside the navigation container"
    ).toBe(true);
    expect(metrics.visibleMainCount, "exactly one main must be visible").toBe(1);
    expect(metrics.mainWithinHorizontalViewport, "main must fit the viewport width").toBe(true);
    expect(metrics.labelsAndRoutesMatch, "navigation labels and routes must match the reviewed shell").toBe(true);
    expect(metrics.overlaps, "navigation targets must not overlap").toEqual([]);
    expect(metrics.mobileTargetsMeetMinimum, "mobile navigation targets must be at least 44px tall").toBe(true);
    for (const [index, link] of metrics.links.entries()) {
      expect(link.visible, "navigation link " + index + " must be visible").toBe(true);
      expect(link.focusable, "navigation link " + index + " must be keyboard focusable").toBe(true);
      expect(link.insideViewport, "navigation link " + index + " must fit the viewport").toBe(true);
      expect(link.insideNavigation, "navigation link " + index + " must fit the navigation").toBe(true);
      expect(link.centerHit, "navigation link " + index + " must win its center hit test").toBe(true);
    }

    expect(blockedRequests, "the page must not request non-loopback resources").toEqual([]);
    expect(localRequestFailures, "loopback resources must load successfully").toEqual([]);
    expect(consoleErrors, "the page must not emit console errors").toEqual([]);
    expect(pageErrors, "the page must not emit uncaught errors").toEqual([]);

  });
}
