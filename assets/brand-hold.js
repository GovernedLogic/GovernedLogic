(function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  function hold() {
    document.documentElement.classList.toggle("gl-hold-motion", document.hidden || reduce.matches);
  }
  document.addEventListener("visibilitychange", hold);
  if (reduce.addEventListener) reduce.addEventListener("change", hold);
  hold();
})();
