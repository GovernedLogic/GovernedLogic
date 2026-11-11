(function () {
  var body = document.body;
  if (!body) return;
  var isHome = body.classList.contains("gl-home-page");
  var isPrinciple = body.classList.contains("gl-type-principle");
  if (!isHome && !isPrinciple) return;

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var root = document.documentElement;
  var lookX = 0;
  var lookY = 0;
  var targetX = 0;
  var targetY = 0;
  var raf = 0;
  var hidden = document.hidden;

  function splitSentences(text) {
    var parts = text.split(/(?<=\.) (?=[A-Z])/);
    if (parts.join(" ") !== text) return null;
    return parts;
  }

  function wrapSentences(el) {
    if (!el || el.children.length) return;
    var text = el.textContent;
    if (!text || text.length <= 160) return;
    if (text.trim() === "A law can describe. A mind can mean. A will can obligate.") return;
    var parts = splitSentences(text);
    if (!parts || parts.length < 2) return;
    el.textContent = "";
    parts.forEach(function (part, i) {
      var span = document.createElement("span");
      span.className = "gl-r32-sent";
      span.textContent = part;
      el.appendChild(span);
      if (i < parts.length - 1) el.appendChild(document.createTextNode(" "));
    });
  }

  function addSight() {
    if (document.querySelector(".gl-r32-sight")) return;
    var sight = document.createElement("div");
    sight.className = "gl-r32-sight";
    sight.setAttribute("aria-hidden", "true");
    var fill = document.createElement("i");
    sight.appendChild(fill);
    body.insertBefore(sight, body.firstChild);
  }

  function setupHome() {
    var problem = document.querySelector("#the-problem");
    if (!problem || problem.querySelector(".gl-r32-screen")) return;
    var original = problem.textContent;
    var parts = splitSentences(original);
    if (!parts || parts.length !== 5) return;

    var screenA = document.createElement("span");
    screenA.className = "gl-r32-screen gl-r32-screen-a";
    var look = document.createElement("span");
    look.className = "gl-r32-look gl-r32-reveal gl-r32-in";
    look.textContent = parts[0] + " ";
    screenA.appendChild(look);

    var screenB = document.createElement("span");
    screenB.className = "gl-r32-screen gl-r32-screen-b";
    parts.slice(1).forEach(function (part, i) {
      var span = document.createElement("span");
      span.className = "gl-r32-sent gl-r32-reveal";
      span.textContent = part;
      screenB.appendChild(span);
      if (i < parts.length - 2) screenB.appendChild(document.createTextNode(" "));
    });

    if (screenA.textContent + screenB.textContent !== original) return;

    problem.textContent = "";
    problem.appendChild(screenA);
    problem.appendChild(screenB);

    var copy = document.querySelector(".gl-hero-copy");
    var title = document.querySelector("h1.gl-hero-title");
    var actions = document.querySelector("#explore .gl-actions");
    var claim = document.querySelector("#the-seed > .gl-core-copy:first-of-type p");
    var arch = null;
    document.querySelectorAll("#the-seed .gl-core-copy p").forEach(function (p) {
      if (p.textContent.trim() === "Governed Logic is a substrate-agnostic reasoning architecture.") arch = p;
    });
    if (!copy || !title || !actions) return;

    var screenC = document.createElement("div");
    screenC.className = "gl-r32-screen gl-r32-screen-c";
    if (claim) {
      claim.classList.add("gl-r32-claim", "gl-r32-reveal");
      screenC.appendChild(claim);
    }
    title.classList.add("gl-r32-reveal");
    screenC.appendChild(title);
    if (arch) {
      arch.classList.add("gl-r32-arch", "gl-r32-reveal");
      screenC.appendChild(arch);
    }
    actions.classList.add("gl-r32-reveal");
    screenC.appendChild(actions);
    copy.appendChild(screenC);

    document.querySelectorAll("#the-seed > .gl-core-copy").forEach(function (block) {
      if (!block.textContent.trim()) block.setAttribute("hidden", "");
    });
  }

  function setupPrinciples() {
    var heading = document.querySelector("main.principle-main h1");
    if (heading) body.setAttribute("data-principle", heading.textContent.trim().toLowerCase());

    var triad = "A law can describe. A mind can mean. A will can obligate.";
    document.querySelectorAll(".principle-passage p").forEach(function (p) {
      if (p.textContent.trim() === triad) {
        p.classList.add("gl-r32-triad");
        return;
      }
      wrapSentences(p);
    });

    var name = (heading && heading.textContent.trim()) || "";
    var first = document.querySelector(".principle-passage");
    if (first && name === "Meaning") {
      first.querySelectorAll(".gl-r32-sent").forEach(function (span) {
        if (span.textContent.trim() === "When meaning drifts, reasoning drifts.") {
          span.classList.add("gl-r32-weight");
        }
      });
    }
    if (first && name === "Obligation") {
      first.querySelectorAll(".gl-r32-sent").forEach(function (span) {
        if (/^If\s/.test(span.textContent.trim())) span.classList.add("gl-r32-if");
      });
    }

    document.querySelectorAll("main.principle-main h1, .principle-passage p, .principle-passage h2, .principle-passage .gl-r32-sent").forEach(function (el) {
      el.classList.add("gl-r32-reveal");
    });
    document.querySelectorAll("main.principle-main h1, .principle-passage:first-of-type .gl-r32-reveal").forEach(function (el) {
      el.classList.add("gl-r32-in");
    });
  }

  function setLook(x, y) {
    targetX = Math.max(-1, Math.min(1, x));
    targetY = Math.max(-1, Math.min(1, y));
    if (!raf && !reduced && !hidden) raf = requestAnimationFrame(tick);
  }

  function tick() {
    raf = 0;
    if (hidden || reduced) return;
    lookX += (targetX - lookX) * 0.12;
    lookY += (targetY - lookY) * 0.12;
    root.style.setProperty("--look-x", lookX.toFixed(3));
    root.style.setProperty("--look-y", lookY.toFixed(3));
    if (Math.abs(targetX - lookX) > 0.002 || Math.abs(targetY - lookY) > 0.002) {
      raf = requestAnimationFrame(tick);
    }
  }

  function onPointer(e) {
    var w = window.innerWidth || 1;
    var h = window.innerHeight || 1;
    setLook((e.clientX / w) * 2 - 1, (e.clientY / h) * 2 - 1);
  }

  function onOrient(e) {
    if (e.gamma == null || e.beta == null) return;
    setLook(e.gamma / 40, (e.beta - 90) / 40);
  }

  function progress() {
    var max = document.documentElement.scrollHeight - window.innerHeight;
    var p = max > 0 ? window.scrollY / max : 0;
    root.style.setProperty("--progress", Math.max(0, Math.min(1, p)).toFixed(4));
  }

  function reveal() {
    var nodes = document.querySelectorAll(".gl-r32-reveal");
    if (reduced || !("IntersectionObserver" in window)) {
      nodes.forEach(function (el) { el.classList.add("gl-r32-in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) entry.target.classList.add("gl-r32-in");
      });
    }, { threshold: 0.18, rootMargin: "0px 0px -8% 0px" });
    nodes.forEach(function (el) { io.observe(el); });
  }

  addSight();
  if (isHome) setupHome();
  if (isPrinciple) setupPrinciples();
  reveal();
  progress();
  window.addEventListener("scroll", progress, { passive: true });

  if (!reduced) {
    window.addEventListener("pointermove", onPointer, { passive: true });
    if (window.DeviceOrientationEvent && !(("ontouchstart" in window) && window.DeviceOrientationEvent.requestPermission)) {
      window.addEventListener("deviceorientation", onOrient, { passive: true });
    }
  }

  document.addEventListener("visibilitychange", function () {
    hidden = document.hidden;
    if (hidden) {
      if (raf) cancelAnimationFrame(raf);
      raf = 0;
    } else if (!reduced) {
      raf = requestAnimationFrame(tick);
    }
  });
})();
