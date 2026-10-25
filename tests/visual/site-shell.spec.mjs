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
  { path: "/faq/", slug: "faq" }
];
const EXPECTED_NAVIGATION = [
  { href: "/concepts/governed-logic/", label: "Governed Logic" },
  { href: "/concepts/ultimate-grounding/", label: "Ultimate Grounding" },
  { href: "/concepts/governed-intelligence/", label: "Governed Intelligence" },
  { href: "/company/", label: "Company" },
  { href: "/research/", label: "Research" }
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
      const openingRegion = page.getByRole("region", { name: "Governed Logic Reasoning Systems" });
      await expect(openingRegion).toHaveCount(1);
      await expect(openingRegion).toBeVisible();
    }

    const isMobile = testInfo.project.name.startsWith("mobile-");
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
        const mainElements = Array.from(document.querySelectorAll("main"));
        const navigationRect = navigation.getBoundingClientRect();
        const links = Array.from(navigation.querySelectorAll(":scope > a"));
        const linkMetrics = links.map(link => {
          const rect = link.getBoundingClientRect();
          const centerX = Math.max(0, Math.min(innerWidth - 1, rect.left + rect.width / 2));
          const centerY = Math.max(0, Math.min(innerHeight - 1, rect.top + rect.height / 2));
          const hit = document.elementFromPoint(centerX, centerY);
          return {
            href: link.getAttribute("href"),
            label: normalize(link.textContent || ""),
            visible: visible(link),
            focusable: link.matches("a[href]") && link.tabIndex >= 0,
            insideViewport:
              rect.left >= -0.5
              && rect.right <= innerWidth + 0.5
              && rect.top >= -0.5
              && rect.bottom <= innerHeight + 0.5,
            insideNavigation:
              rect.left >= navigationRect.left - 0.5
              && rect.right <= navigationRect.right + 0.5
              && rect.top >= navigationRect.top - 0.5
              && rect.bottom <= navigationRect.bottom + 0.5,
            centerHit: hit === link || link.contains(hit),
            height: rect.height,
            top: rect.top,
            right: rect.right,
            bottom: rect.bottom,
            left: rect.left
          };
        });
        const overlaps = [];
        for (let first = 0; first < linkMetrics.length; first += 1) {
          for (let second = first + 1; second < linkMetrics.length; second += 1) {
            const a = linkMetrics[first];
            const b = linkMetrics[second];
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
            navigationRect.left >= -0.5
            && navigationRect.right <= innerWidth + 0.5
            && navigationRect.top >= -0.5
            && navigationRect.bottom <= innerHeight + 0.5,
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
      { expectedNavigation: EXPECTED_NAVIGATION, mobile: isMobile }
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
