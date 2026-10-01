(() => {
  "use strict";

  const stage = document.getElementById("book-hero-stage");
  if (!stage) return;

  function setOpen(open) {
    stage.classList.toggle("is-open", open);
    stage.setAttribute("aria-pressed", String(open));
  }

  function toggle() {
    setOpen(!stage.classList.contains("is-open"));
  }

  stage.addEventListener("click", toggle);
  stage.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggle();
    }
  });

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduce) {
    window.setTimeout(() => setOpen(true), 1150);
  } else {
    setOpen(true);
  }
})();