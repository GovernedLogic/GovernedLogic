(function () {
  "use strict";

  const root = document.documentElement;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  root.classList.add("depth-js");

  const portal = document.querySelector("[data-depth-portal]");
  if (portal) {
    let step = Number(portal.dataset.step || 0);
    portal.addEventListener("click", function () {
      step = (step + 1) % 3;
      portal.dataset.step = String(step);
      const current = step === 0 ? "representation" : step === 1 ? "referent" : "ground";
      const next = step === 0 ? "referent" : step === 1 ? "ground" : "representation";
      portal.setAttribute("aria-label", "Current layer: " + current + ". Activate to move to " + next + ".");
    });
  }

  const doors = Array.from(document.querySelectorAll(".primary-doors > a"));
  doors.forEach(function (door) {
    door.addEventListener("pointerdown", function () { door.classList.add("is-pressed"); }, { passive: true });
    ["pointerup","pointercancel","pointerleave"].forEach(function (type) {
      door.addEventListener(type, function () { door.classList.remove("is-pressed"); }, { passive: true });
    });
  });

  if (!reduceMotion.matches && window.matchMedia("(pointer:fine)").matches) {
    doors.forEach(function (door) {
      door.addEventListener("pointermove", function (event) {
        const rect = door.getBoundingClientRect();
        const x = Math.max(0, Math.min(1, (event.clientX - rect.left) / Math.max(1, rect.width)));
        const y = Math.max(0, Math.min(1, (event.clientY - rect.top) / Math.max(1, rect.height)));
        door.style.setProperty("--door-x", (x * 100).toFixed(1) + "%");
        door.style.setProperty("--door-y", (y * 100).toFixed(1) + "%");
        door.style.setProperty("--door-ry", ((x - 0.5) * 5.5).toFixed(2) + "deg");
        door.style.setProperty("--door-rx", ((0.5 - y) * 4.2).toFixed(2) + "deg");
      }, { passive: true });
      door.addEventListener("pointerleave", function () {
        door.style.setProperty("--door-rx", "0deg");
        door.style.setProperty("--door-ry", "0deg");
      }, { passive: true });
    });
  }

  const reveals = Array.from(document.querySelectorAll("[data-reveal]"));
  if (reduceMotion.matches || typeof IntersectionObserver !== "function") {
    reveals.forEach(function (node) { node.classList.add("is-visible"); });
    return;
  }

  const observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.14, rootMargin: "0px 0px -8% 0px" });

  reveals.forEach(function (node) { observer.observe(node); });
})();