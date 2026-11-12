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
