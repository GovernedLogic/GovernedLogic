(function () {
  "use strict";
  const root = document.documentElement;
  root.classList.add("gl-intro-loading");
  window.__glIntroFallbackTimer = window.setTimeout(function () {
    if (!root.classList.contains("gl-intro-ready")) {
      root.classList.remove("gl-intro-loading");
      root.classList.add("gl-intro-failed");
    }
  }, 3000);
})();