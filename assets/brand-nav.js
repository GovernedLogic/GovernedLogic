(function () {
  var toggle = document.querySelector("#gl-home-bar .gl-nav-toggle");
  var nav = document.getElementById("gl-primary-nav");
  if (!toggle || !nav) return;

  function open() {
    return toggle.getAttribute("aria-expanded") === "true";
  }

  function items() {
    return [toggle].concat([].slice.call(nav.querySelectorAll("a")));
  }

  function setOpen(next) {
    toggle.setAttribute("aria-expanded", next ? "true" : "false");
    document.body.classList.toggle("gl-nav-open", next);
    if (next) {
      var first = nav.querySelector("a");
      if (first) first.focus();
    } else if (document.activeElement && nav.contains(document.activeElement)) {
      toggle.focus();
    }
  }

  toggle.addEventListener("click", function () {
    setOpen(!open());
  });

  document.addEventListener("keydown", function (e) {
    if (!open()) return;
    if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
      return;
    }
    if (e.key !== "Tab") return;
    var list = items();
    var i = list.indexOf(document.activeElement);
    if (e.shiftKey) {
      if (i <= 0) {
        e.preventDefault();
        list[list.length - 1].focus();
      }
    } else if (i < 0 || i === list.length - 1) {
      e.preventDefault();
      list[0].focus();
    }
  });

  nav.addEventListener("click", function (e) {
    if (e.target.closest("a")) setOpen(false);
  });
})();

/* Exactly one primary-nav item is current. Fragment links and the header CTA are not. */
(function () {
  function pathOf(href) {
    try {
      var url = new URL(href, location.origin);
      var path = url.pathname;
      if (path.length > 1 && path.endsWith("/")) path = path.slice(0, -1);
      return { url: url, path: path };
    } catch (e) {
      return null;
    }
  }

  function settle() {
    var here = location.pathname;
    if (here.length > 1 && here.endsWith("/")) here = here.slice(0, -1);
    document.querySelectorAll(".gl-go > a[href]").forEach(function (link) {
      var parsed = pathOf(link.getAttribute("href") || "");
      var inNav = !!link.closest('nav[aria-label="Primary"]');
      var match = parsed
        && inNav
        && parsed.url.hash.length <= 1
        && parsed.url.origin === location.origin
        && parsed.path === here;
      if (match) link.setAttribute("aria-current", "page");
      else if (link.getAttribute("aria-current") === "page") link.removeAttribute("aria-current");
    });
  }

  // Deferred scripts run at readyState "interactive", before DOMContentLoaded.
  // The header script marks links on that event, so this correction has to run after it.
  if (document.readyState === "complete") settle();
  else document.addEventListener("DOMContentLoaded", settle);
})();

/* Pause decorative motion, including the footer seed, while the tab is hidden. */
(function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  function hold() {
    document.documentElement.classList.toggle("gl-hold-motion", document.hidden || reduce.matches);
  }
  document.addEventListener("visibilitychange", hold);
  if (reduce.addEventListener) reduce.addEventListener("change", hold);
  hold();
})();
