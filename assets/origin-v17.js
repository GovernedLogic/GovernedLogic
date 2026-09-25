(function () {
  "use strict";

  const root = document.documentElement;
  const fallbackWasShown = root.classList.contains("gl-intro-failed");
  const experience = document.querySelector(".origin-experience");
  const stage = experience && experience.querySelector(".origin-stage");
  const canvas = experience && experience.querySelector("#origin-canvas");
  const centerMark = experience && experience.querySelector("#origin-center, .origin-center");
  const architecture = experience && experience.querySelector("#origin-architecture");
  const hero = document.querySelector("#architecture");

  function markFailed() {
    if (window.__glIntroFallbackTimer) window.clearTimeout(window.__glIntroFallbackTimer);
    root.classList.remove("gl-intro-loading", "gl-intro-ready");
    root.classList.add("gl-intro-failed");
  }

  if (!experience || !stage || !canvas || !centerMark || !architecture || !hero) {
    markFailed();
    return;
  }

  let context = null;
  try {
    context = canvas.getContext("2d", { alpha: true, desynchronized: true });
  } catch (error) {
    markFailed();
    return;
  }
  if (!context) {
    markFailed();
    return;
  }

  const principleElements = Array.from(
    experience.querySelectorAll(".origin-principle[data-principle]")
  );
  const tokenElements = Array.from(
    experience.querySelectorAll(".origin-token[data-token]")
  );
  const chainElements = Array.from(architecture.querySelectorAll("li"));
  const chainLabelElements = chainElements.map(function (element) {
    return element.querySelector("span") || element;
  });
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  const TAU = Math.PI * 2;
  const AUTOPLAY_SECONDS = 13.5;
  const MOBILE_BREAKPOINT = 720;

  /*
   * Every item is authored. There is no random particle generator here.
   * The starting radius, depth, rotation and final position give each real
   * DOM token a deliberate path through the semantic field.
   */
  const TOKEN_LAYOUT = {
    reality:        { a0: -2.84, a1: -2.62, r0: 1.10, r1: 0.72, z0: 0.20, z1: 0.84, turns: 0.78, mobile: true },
    representation: { a0:  0.32, a1:  0.26, r0: 1.18, r1: 0.78, z0: 0.14, z1: 0.65, turns: 1.06, mobile: true },
    premise:        { a0: -1.70, a1: -1.32, r0: 0.96, r1: 0.66, z0: 0.42, z1: 0.76, turns: 0.70, mobile: true },
    referent:       { a0:  2.90, a1:  2.68, r0: 1.08, r1: 0.81, z0: 0.26, z1: 0.56, turns: 0.92, mobile: true },
    inference:      { a0: -0.66, a1: -0.58, r0: 1.02, r1: 0.64, z0: 0.52, z1: 0.92, turns: 0.84, mobile: true },
    conclusion:     { a0:  1.04, a1:  0.92, r0: 1.24, r1: 0.76, z0: 0.10, z1: 0.70, turns: 1.12, mobile: false, desktop: false },
    coherence:      { a0:  2.10, a1:  2.20, r0: 1.14, r1: 0.69, z0: 0.34, z1: 0.82, turns: 0.74, mobile: false, desktop: false },
    correspondence: { a0: -2.22, a1: -2.06, r0: 1.26, r1: 0.85, z0: 0.08, z1: 0.50, turns: 1.00, mobile: false, desktop: false },
    sufficiency:    { a0:  0.04, a1: -0.02, r0: 0.94, r1: 0.58, z0: 0.62, z1: 0.88, turns: 0.68, mobile: false, desktop: false },
    consequence:   { a0:  1.68, a1:  1.56, r0: 1.20, r1: 0.80, z0: 0.18, z1: 0.62, turns: 0.94, mobile: false, desktop: false },
    claim:          { a0: -1.12, a1: -0.98, r0: 1.30, r1: 0.87, z0: 0.06, z1: 0.46, turns: 1.16, mobile: false, desktop: false },
    evidence:       { a0:  2.50, a1:  2.38, r0: 1.00, r1: 0.62, z0: 0.48, z1: 0.94, turns: 0.80, mobile: false, desktop: false }
  };

  const PRINCIPLE_ANGLES = {
    being: -Math.PI / 2,
    truth: -Math.PI / 6,
    logic: Math.PI / 6,
    meaning: Math.PI / 2,
    intelligibility: (5 * Math.PI) / 6,
    obligation: (7 * Math.PI) / 6
  };

  /*
   * This is the relationship ledger for the visible lines. Each edge has a
   * semantic reason; none exists merely to make the scene look busier.
   */
  const RELATIONSHIPS = [
    ["being", "fixed_center"],
    ["truth", "fixed_center"],
    ["logic", "fixed_center"],
    ["meaning", "fixed_center"],
    ["intelligibility", "fixed_center"],
    ["obligation", "fixed_center"],
    ["representation", "referent"],
    ["premise", "truth"],
    ["conclusion", "reality"],
    ["inference", "logic"],
    ["correspondence", "truth"],
    ["sufficiency", "ground"]
  ];

  let width = 1;
  let height = 1;
  let dpr = 1;
  let progress = 0;
  let targetProgress = 0;
  let autoplay = true;
  let frameRequest = 0;
  let lastFrameTime = 0;
  let inView = true;
  let documentVisible = !document.hidden;
  let firstRender = true;
  let lastScrollProgress = 0;
  let isMobile = window.innerWidth <= MOBILE_BREAKPOINT;
  let layoutRefreshRequest = 0;

  const pointer = { x: 0, y: 0, targetX: 0, targetY: 0 };
  const tokenPositions = new Map();
  const principlePositions = new Map();
  const chainPositions = new Map();
  const layout = {
    stageLeft: 0,
    stageTop: 0,
    stageRenderedWidth: 1,
    stageRenderedHeight: 1,
    experienceTop: 0,
    experienceHeight: 1,
    stageHeight: 1,
    scrollDistance: 1,
    chainPoints: []
  };

  function clamp(value, minimum, maximum) {
    return Math.max(minimum, Math.min(maximum, value));
  }

  function mix(from, to, amount) {
    return from + (to - from) * amount;
  }

  function smoothstep(from, to, value) {
    const amount = clamp((value - from) / Math.max(0.00001, to - from), 0, 1);
    return amount * amount * (3 - 2 * amount);
  }

  function easeOutCubic(value) {
    return 1 - Math.pow(1 - clamp(value, 0, 1), 3);
  }

  function measureLayout() {
    const stageBounds = stage.getBoundingClientRect();
    const experienceBounds = experience.getBoundingClientRect();
    const stageScale = Number.parseFloat(
      experience.style.getPropertyValue("--origin-stage-scale") || "1"
    ) || 1;
    width = Math.max(1, Math.round(stage.clientWidth));
    height = Math.max(1, Math.round(stage.clientHeight));
    layout.stageLeft = stageBounds.left;
    layout.stageTop = stageBounds.top;
    layout.stageRenderedWidth = Math.max(1, stageBounds.width);
    layout.stageRenderedHeight = Math.max(1, stageBounds.height);
    layout.experienceTop = window.scrollY + experienceBounds.top;
    layout.experienceHeight = Math.max(1, experienceBounds.height);
    layout.stageHeight = height;
    layout.scrollDistance = Math.max(1, layout.experienceHeight - layout.stageHeight);
    layout.chainPoints = [];
    chainPositions.clear();
    chainLabelElements.forEach(function (element) {
      const bounds = element.getBoundingClientRect();
      const point = {
        x: (bounds.left - stageBounds.left + bounds.width / 2) / stageScale,
        y: (bounds.top - stageBounds.top + bounds.height / 2) / stageScale
      };
      layout.chainPoints.push(point);
      chainPositions.set(element.textContent.trim().toLowerCase(), point);
    });
  }

  function resizeCanvas() {
    measureLayout();
    isMobile = width <= MOBILE_BREAKPOINT;
    const dprCap = isMobile ? 1.35 : 1.75;
    dpr = Math.min(window.devicePixelRatio || 1, dprCap);
    canvas.width = Math.max(1, Math.round(width * dpr));
    canvas.height = Math.max(1, Math.round(height * dpr));
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    context.setTransform(dpr, 0, 0, dpr, 0, 0);
    updateHandoff(getScrollProgress());
    render(progress);
  }

  function scheduleLayoutRefresh() {
    if (layoutRefreshRequest) return;
    layoutRefreshRequest = window.requestAnimationFrame(function () {
      layoutRefreshRequest = 0;
      resizeCanvas();
    });
  }

  function getScrollProgress() {
    return clamp((window.scrollY - layout.experienceTop) / layout.scrollDistance, 0, 1);
  }

  function updateHandoff(scrollProgress) {
    const handoff = smoothstep(0.64, 1, scrollProgress);
    experience.style.setProperty("--origin-stage-opacity", mix(1, 0.16, handoff).toFixed(4));
    experience.style.setProperty("--origin-stage-scale", mix(1, 0.985, handoff).toFixed(4));
    hero.style.setProperty("--origin-hero-opacity", mix(0.12, 1, handoff).toFixed(4));
    hero.style.setProperty("--origin-hero-shift", mix(38, 0, handoff).toFixed(2) + "px");
  }

  function wake() {
    if (frameRequest || !inView || !documentVisible || reduceMotion.matches) return;
    lastFrameTime = 0;
    frameRequest = window.requestAnimationFrame(frame);
  }

  function frame(now) {
    frameRequest = 0;
    if (!inView || !documentVisible || reduceMotion.matches) return;

    const delta = lastFrameTime ? Math.min(0.05, (now - lastFrameTime) / 1000) : 0;
    lastFrameTime = now;

    if (autoplay) {
      progress = clamp(progress + delta / AUTOPLAY_SECONDS, 0, 1);
      targetProgress = progress;
      if (progress >= 1) {
        autoplay = false;
      }
    } else {
      const response = 1 - Math.exp(-delta * 9.5);
      progress += (targetProgress - progress) * response;
      if (Math.abs(targetProgress - progress) < 0.00025) progress = targetProgress;
    }

    const pointerResponse = 1 - Math.exp(-delta * 7);
    pointer.x += (pointer.targetX - pointer.x) * pointerResponse;
    pointer.y += (pointer.targetY - pointer.y) * pointerResponse;

    render(progress);

    const progressMoving = autoplay || Math.abs(targetProgress - progress) >= 0.00025;
    const pointerMoving =
      Math.abs(pointer.targetX - pointer.x) >= 0.001 ||
      Math.abs(pointer.targetY - pointer.y) >= 0.001;
    if (progressMoving || pointerMoving) frameRequest = window.requestAnimationFrame(frame);
  }

  function updateCenter(value) {
    const arrive = smoothstep(0.12, 0.34, value);
    const settle = smoothstep(0.78, 1, value);
    const scale = mix(0.42, 1, easeOutCubic(arrive)) * mix(1, 0.86, settle);
    centerMark.style.opacity = String(mix(0, 0.96, arrive) * mix(1, 0.7, settle));
    centerMark.style.transform = "translate(-50%, -50%) scale(" + scale.toFixed(4) + ")";
  }

  function updateTokens(value) {
    tokenPositions.clear();
    const baseRadius = Math.min(width, height) * 0.47;
    const centerX = width / 2;
    const centerY = height / 2;
    const fieldShiftX = pointer.x * (isMobile ? 3 : 11);
    const fieldShiftY = pointer.y * (isMobile ? 2 : 7);

    tokenElements.forEach(function (element, index) {
      const key = String(element.dataset.token || "").toLowerCase();
      const layout = TOKEN_LAYOUT[key];
      if (!layout || (isMobile && !layout.mobile) || (!isMobile && layout.desktop === false)) {
        element.style.opacity = "0";
        tokenPositions.set(key, { x: centerX, y: centerY, opacity: 0, visible: false });
        return;
      }

      const delay = index * 0.012;
      const movement = easeOutCubic(smoothstep(0.035 + delay, 0.62 + delay * 0.25, value));
      const reveal = smoothstep(0.035 + delay, 0.19 + delay, value);
      /* Vocabulary completes its pass before the principle ring arrives.
       * The phases stay sparse, legible and semantically distinct. */
      const quiet = smoothstep(0.18, 0.3, value);
      const angle = layout.a0 + movement * (layout.a1 - layout.a0 + layout.turns * TAU);
      const radius = baseRadius * mix(layout.r0, layout.r1, movement);
      const depth = clamp(
        mix(layout.z0, layout.z1, movement) + Math.sin(angle * 1.7 + index) * 0.035,
        0,
        1
      );
      const perspective = mix(0.72, 1.08, depth);
      const x =
        centerX + Math.cos(angle) * radius * perspective + fieldShiftX * mix(0.28, 1, depth);
      const y =
        centerY + Math.sin(angle) * radius * perspective * 0.72 + fieldShiftY * mix(0.28, 1, depth);
      const scale = mix(0.68, 1.12, depth) * mix(1, 0.92, quiet);
      const exit = 1 - quiet;
      const opacity = reveal * mix(0.28, 0.78, depth) * exit;
      const z = Math.round(mix(-90, 110, depth));

      element.style.opacity = opacity.toFixed(4);
      element.style.filter = "blur(" + mix(0.75, 0, depth).toFixed(2) + "px)";
      element.style.transform =
        "translate(-50%, -50%) translate3d(" +
        (x - centerX).toFixed(2) +
        "px," +
        (y - centerY).toFixed(2) +
        "px," +
        z +
        "px) scale(" +
        scale.toFixed(4) +
        ")";
      tokenPositions.set(key, { x: x, y: y, opacity: opacity, visible: opacity > 0.01 });
    });
  }

  function updatePrinciples(value) {
    principlePositions.clear();
    const centerX = width / 2;
    const centerY = height / 2;
    const ringRadius = Math.min(width, height) * (isMobile ? 0.29 : 0.265);
    const settle = smoothstep(0.69, 0.9, value);

    principleElements.forEach(function (element, index) {
      const key = String(element.dataset.principle || "").toLowerCase();
      const targetAngle = PRINCIPLE_ANGLES[key];
      if (typeof targetAngle !== "number") {
        element.style.opacity = "0";
        return;
      }

      /* Consecutive semantic phases: sparse vocabulary, then principles,
       * then the reasoning chain. */
      const revealStart = 0.3 + index * 0.025;
      const revealEnd = 0.44 + index * 0.025;
      const reveal = smoothstep(revealStart, revealEnd, value);
      const angle = targetAngle - (1 - reveal) * 0.46;
      const radius = ringRadius * mix(1.42, 1, easeOutCubic(reveal)) * mix(1, 0.78, settle);
      const depth = 0.52 + 0.32 * Math.cos(angle - 0.55);
      const x = centerX + Math.cos(angle) * radius + pointer.x * 3.5 * depth;
      const y = centerY + Math.sin(angle) * radius * 0.78 + pointer.y * 2.5 * depth;
      const finalQuiet = mix(1, 0.32, smoothstep(0.8, 1, value));
      const opacity = reveal * finalQuiet;
      const scale = mix(0.74, 1.03, depth) * mix(1, 0.94, settle);

      element.style.opacity = opacity.toFixed(4);
      element.style.filter = "blur(" + mix(0.45, 0, reveal).toFixed(2) + "px)";
      element.style.transform =
        "translate(-50%, -50%) translate3d(" +
        (x - centerX).toFixed(2) +
        "px," +
        (y - centerY).toFixed(2) +
        "px," +
        Math.round(mix(-20, 36, depth)) +
        "px) scale(" +
        scale.toFixed(4) +
        ")";
      principlePositions.set(key, { x: x, y: y, opacity: opacity, visible: opacity > 0.01 });
    });
  }

  function updateArchitecture(value) {
    const arrival = smoothstep(0.67, 0.79, value);
    architecture.style.opacity = arrival.toFixed(4);

    let pulsePosition = -1;
    if (value >= 0.71 && value < 0.87) {
      pulsePosition = smoothstep(0.71, 0.87, value);
    } else if (value >= 0.87 && value < 0.985) {
      pulsePosition = 1 - smoothstep(0.87, 0.985, value);
    }

    const activeIndex = pulsePosition < 0
      ? -1
      : Math.round(pulsePosition * Math.max(0, chainElements.length - 1));

    chainElements.forEach(function (element, index) {
      const label = chainLabelElements[index];
      const distance = activeIndex < 0 ? 99 : Math.abs(index - activeIndex);
      const emphasis = distance === 0 ? 1 : distance === 1 ? 0.42 : 0;
      element.style.opacity = String(arrival * mix(0.7, 1, emphasis));
      label.style.color = emphasis > 0.5 ? "#ffffff" : "#f5f2e8";
      label.style.textShadow = emphasis > 0
        ? "0 0 " + Math.round(8 + emphasis * 16) + "px rgba(171,128,255," +
          (0.25 + emphasis * 0.55).toFixed(2) + ")"
        : "none";
      label.style.transform = "scale(" + mix(1, 1.045, emphasis).toFixed(4) + ")";
    });
  }

  function drawPolygon(centerX, centerY, radius, sides, rotation) {
    for (let index = 0; index <= sides; index += 1) {
      const angle = rotation + (index / sides) * TAU;
      const x = centerX + Math.cos(angle) * radius;
      const y = centerY + Math.sin(angle) * radius * 0.72;
      if (index === 0) context.moveTo(x, y);
      else context.lineTo(x, y);
    }
  }

  function drawInfinityDepth(value) {
    const appear = smoothstep(0.26, 0.5, value);
    const quiet = 1 - 0.78 * smoothstep(0.74, 1, value);
    const alpha = appear * quiet;
    if (alpha <= 0.001) return;

    const centerX = width / 2;
    const centerY = height / 2;
    const base = Math.min(width, height) * (isMobile ? 0.31 : 0.34);
    const layers = isMobile ? 3 : 5;
    context.save();
    context.lineWidth = 0.65;
    for (let index = 0; index < layers; index += 1) {
      const depth = index / Math.max(1, layers - 1);
      const radius = base * mix(1, 0.28, depth);
      context.beginPath();
      drawPolygon(centerX, centerY, radius, 12, value * 0.42 + index * 0.055);
      context.strokeStyle = "rgba(126,179,224," + (alpha * mix(0.105, 0.035, depth)).toFixed(4) + ")";
      context.stroke();
    }
    context.restore();
  }

  function drawSeedOfLife(value) {
    const appear = smoothstep(0.34, 0.54, value);
    const quiet = 1 - 0.84 * smoothstep(0.72, 1, value);
    const alpha = appear * quiet;
    if (alpha <= 0.001) return;

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * (isMobile ? 0.072 : 0.083);
    context.save();
    context.lineWidth = 0.7;
    context.strokeStyle = "rgba(199,222,239," + (alpha * 0.16).toFixed(4) + ")";
    for (let index = 0; index < 7; index += 1) {
      const x = index === 0 ? centerX : centerX + Math.cos(((index - 1) / 6) * TAU) * radius;
      const y = index === 0 ? centerY : centerY + Math.sin(((index - 1) / 6) * TAU) * radius;
      context.beginPath();
      context.arc(x, y, radius, 0, TAU);
      context.stroke();
    }
    context.restore();
  }

  function drawTesseract(value) {
    const appear = smoothstep(0.43, 0.61, value);
    const quiet = 1 - 0.82 * smoothstep(0.76, 1, value);
    const alpha = appear * quiet;
    if (alpha <= 0.001) return;

    const centerX = width / 2;
    const centerY = height / 2;
    const outer = Math.min(width, height) * (isMobile ? 0.19 : 0.225);
    const inner = outer * 0.52;
    const rotation = Math.PI / 4 + value * 0.31;
    const offsetX = Math.cos(value * Math.PI) * outer * 0.09;
    const offsetY = Math.sin(value * Math.PI) * outer * 0.055;
    const outerPoints = [];
    const innerPoints = [];

    for (let index = 0; index < 4; index += 1) {
      const angle = rotation + index * (Math.PI / 2);
      outerPoints.push({
        x: centerX + Math.cos(angle) * outer,
        y: centerY + Math.sin(angle) * outer * 0.68
      });
      innerPoints.push({
        x: centerX + offsetX + Math.cos(angle + 0.1) * inner,
        y: centerY + offsetY + Math.sin(angle + 0.1) * inner * 0.68
      });
    }

    context.save();
    context.lineWidth = 0.8;
    context.strokeStyle = "rgba(149,125,241," + (alpha * 0.19).toFixed(4) + ")";
    context.beginPath();
    [outerPoints, innerPoints].forEach(function (points) {
      points.forEach(function (point, index) {
        if (index === 0) context.moveTo(point.x, point.y);
        else context.lineTo(point.x, point.y);
      });
      context.lineTo(points[0].x, points[0].y);
    });
    outerPoints.forEach(function (point, index) {
      context.moveTo(point.x, point.y);
      context.lineTo(innerPoints[index].x, innerPoints[index].y);
    });
    context.stroke();
    context.restore();
  }

  function getSemanticPosition(key) {
    if (key === "fixed_center") return { x: width / 2, y: height / 2, opacity: 1, visible: true };
    const fieldPosition = tokenPositions.get(key) || principlePositions.get(key);
    if (fieldPosition) return fieldPosition;
    const point = chainPositions.get(key);
    if (!point) return null;
    const opacity = Number.parseFloat(architecture.style.opacity || "0");
    return {
      x: point.x,
      y: point.y,
      opacity: opacity,
      visible: opacity > 0.01
    };
  }

  function drawRelationships(value) {
    const ambientAlpha =
      smoothstep(0.08, 0.16, value) * (1 - smoothstep(0.22, 0.3, value));
    const principleAlpha =
      smoothstep(0.34, 0.59, value) * mix(1, 0.24, smoothstep(0.78, 1, value));
    if (Math.max(ambientAlpha, principleAlpha) <= 0.001) return;

    context.save();
    context.lineWidth = 0.72;
    RELATIONSHIPS.forEach(function (relationship, index) {
      const masterAlpha = relationship[1] === "fixed_center"
        ? principleAlpha
        : ambientAlpha;
      if (masterAlpha <= 0.001) return;
      const from = getSemanticPosition(relationship[0]);
      const to = getSemanticPosition(relationship[1]);
      if (!from || !to || !from.visible || !to.visible) return;
      const localAlpha = masterAlpha * Math.min(from.opacity || 1, to.opacity || 1) * 0.34;
      if (localAlpha <= 0.002) return;

      const midpointX = (from.x + to.x) / 2 + (height * 0.018) * Math.sin(index * 1.7);
      const midpointY = (from.y + to.y) / 2 - (width * 0.012) * Math.cos(index * 1.3);
      const gradient = context.createLinearGradient(from.x, from.y, to.x, to.y);
      gradient.addColorStop(0, "rgba(109,177,232," + (localAlpha * 0.55).toFixed(4) + ")");
      gradient.addColorStop(0.55, "rgba(232,238,242," + localAlpha.toFixed(4) + ")");
      gradient.addColorStop(1, "rgba(151,111,242," + (localAlpha * 0.62).toFixed(4) + ")");
      context.strokeStyle = gradient;
      context.beginPath();
      context.moveTo(from.x, from.y);
      context.quadraticCurveTo(midpointX, midpointY, to.x, to.y);
      context.stroke();
    });

    tokenPositions.forEach(function (point) {
      if (!point.visible) return;
      context.fillStyle = "rgba(221,238,250," + (ambientAlpha * point.opacity * 0.5).toFixed(4) + ")";
      context.beginPath();
      context.arc(point.x, point.y, 1.2, 0, TAU);
      context.fill();
    });
    context.restore();
  }

  function chainPoints() {
    return layout.chainPoints;
  }

  function pointAlongPath(points, amount) {
    if (points.length === 0) return null;
    if (points.length === 1) return points[0];
    const lengths = [];
    let total = 0;
    for (let index = 1; index < points.length; index += 1) {
      const length = Math.hypot(
        points[index].x - points[index - 1].x,
        points[index].y - points[index - 1].y
      );
      lengths.push(length);
      total += length;
    }
    let remaining = clamp(amount, 0, 1) * total;
    for (let index = 0; index < lengths.length; index += 1) {
      if (remaining <= lengths[index] || index === lengths.length - 1) {
        const local = lengths[index] ? remaining / lengths[index] : 0;
        return {
          x: mix(points[index].x, points[index + 1].x, clamp(local, 0, 1)),
          y: mix(points[index].y, points[index + 1].y, clamp(local, 0, 1))
        };
      }
      remaining -= lengths[index];
    }
    return points[points.length - 1];
  }

  function drawArchitecturePath(value) {
    const arrival = smoothstep(0.68, 0.8, value);
    if (arrival <= 0.001 || chainElements.length < 2) return;
    const points = chainPoints();

    context.save();
    context.lineWidth = 0.75;
    context.strokeStyle = "rgba(143,113,237," + (arrival * 0.27).toFixed(4) + ")";
    context.beginPath();
    points.forEach(function (point, index) {
      if (index === 0) context.moveTo(point.x, point.y);
      else context.lineTo(point.x, point.y);
    });
    context.stroke();

    let pulseAmount = -1;
    let pulseOpacity = 1;
    if (value >= 0.71 && value < 0.87) {
      pulseAmount = smoothstep(0.71, 0.87, value);
    } else if (value >= 0.87 && value < 0.985) {
      pulseAmount = 1 - smoothstep(0.87, 0.985, value);
      pulseOpacity = 1 - 0.25 * smoothstep(0.94, 0.985, value);
    }

    if (pulseAmount >= 0) {
      const pulse = pointAlongPath(points, pulseAmount);
      if (pulse) {
        const glow = context.createRadialGradient(pulse.x, pulse.y, 0, pulse.x, pulse.y, 18);
        glow.addColorStop(0, "rgba(255,255,255," + (0.92 * pulseOpacity).toFixed(3) + ")");
        glow.addColorStop(0.24, "rgba(185,130,255," + (0.68 * pulseOpacity).toFixed(3) + ")");
        glow.addColorStop(1, "rgba(108,59,205,0)");
        context.fillStyle = glow;
        context.beginPath();
        context.arc(pulse.x, pulse.y, 18, 0, TAU);
        context.fill();
        context.fillStyle = "rgba(255,255,255," + pulseOpacity.toFixed(3) + ")";
        context.beginPath();
        context.arc(pulse.x, pulse.y, 1.7, 0, TAU);
        context.fill();
      }
    }
    context.restore();
  }

  function drawFixedCenter(value) {
    const appear = smoothstep(0.1, 0.34, value);
    if (appear <= 0.001) return;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = mix(6, Math.min(width, height) * 0.09, appear);
    const gradient = context.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius);
    gradient.addColorStop(0, "rgba(255,255,255," + (appear * 0.18).toFixed(4) + ")");
    gradient.addColorStop(0.18, "rgba(142,203,247," + (appear * 0.11).toFixed(4) + ")");
    gradient.addColorStop(1, "rgba(93,90,224,0)");
    context.save();
    context.fillStyle = gradient;
    context.beginPath();
    context.arc(centerX, centerY, radius, 0, TAU);
    context.fill();
    context.strokeStyle = "rgba(225,241,255," + (appear * 0.24).toFixed(4) + ")";
    context.lineWidth = 0.65;
    context.beginPath();
    context.arc(centerX, centerY, mix(3, 16, appear), 0, TAU);
    context.stroke();
    context.restore();
  }

  function render(value) {
    value = clamp(value, 0, 1);
    context.setTransform(dpr, 0, 0, dpr, 0, 0);
    context.clearRect(0, 0, width, height);

    updateCenter(value);
    updateTokens(value);
    updatePrinciples(value);
    updateArchitecture(value);

    drawInfinityDepth(value);
    drawSeedOfLife(value);
    drawTesseract(value);
    drawRelationships(value);
    drawArchitecturePath(value);
    drawFixedCenter(value);

    if (firstRender) {
      firstRender = false;
      if (window.__glIntroFallbackTimer) window.clearTimeout(window.__glIntroFallbackTimer);
      root.classList.remove("gl-intro", "gl-intro-loading", "gl-intro-failed");
      root.classList.add("gl-intro-ready");
    }
  }

  function onScroll() {
    const current = getScrollProgress();
    updateHandoff(current);
    const scrollDelta = current - lastScrollProgress;
    if (Math.abs(scrollDelta) > 0.0005) {
      autoplay = false;
      targetProgress = clamp(targetProgress + scrollDelta, 0, 1);
      lastScrollProgress = current;
      wake();
    }
  }

  function onPointerMove(event) {
    if (event.pointerType === "touch") return;
    pointer.targetX = clamp(
      ((event.clientX - layout.stageLeft) / layout.stageRenderedWidth) * 2 - 1,
      -1,
      1
    );
    pointer.targetY = clamp(
      ((event.clientY - layout.stageTop) / layout.stageRenderedHeight) * 2 - 1,
      -1,
      1
    );
    wake();
  }

  function onPointerLeave() {
    pointer.targetX = 0;
    pointer.targetY = 0;
    wake();
  }

  function onVisibilityChange() {
    documentVisible = !document.hidden;
    if (!documentVisible && frameRequest) {
      window.cancelAnimationFrame(frameRequest);
      frameRequest = 0;
    }
    if (documentVisible) wake();
  }

  function applyReducedMotion() {
    if (frameRequest) {
      window.cancelAnimationFrame(frameRequest);
      frameRequest = 0;
    }
    autoplay = false;
    progress = 1;
    targetProgress = 1;
    pointer.x = pointer.targetX = 0;
    pointer.y = pointer.targetY = 0;
    render(1);
  }

  stage.addEventListener("pointermove", onPointerMove, { passive: true });
  stage.addEventListener("pointerleave", onPointerLeave, { passive: true });
  window.addEventListener("scroll", onScroll, { passive: true });
  document.addEventListener("visibilitychange", onVisibilityChange);

  if (typeof ResizeObserver === "function") {
    const resizeObserver = new ResizeObserver(scheduleLayoutRefresh);
    resizeObserver.observe(stage);
  } else {
    window.addEventListener("resize", scheduleLayoutRefresh, { passive: true });
  }

  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", scheduleLayoutRefresh, { passive: true });
    window.visualViewport.addEventListener("scroll", scheduleLayoutRefresh, { passive: true });
  }

  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(scheduleLayoutRefresh);
  }

  if (typeof IntersectionObserver === "function") {
    const intersectionObserver = new IntersectionObserver(
      function (entries) {
        inView = Boolean(entries[0] && entries[0].isIntersecting);
        if (!inView && frameRequest) {
          window.cancelAnimationFrame(frameRequest);
          frameRequest = 0;
        }
        if (inView) wake();
      },
      { threshold: 0.01 }
    );
    intersectionObserver.observe(experience);
  }

  if (typeof reduceMotion.addEventListener === "function") {
    reduceMotion.addEventListener("change", function () {
      if (reduceMotion.matches) applyReducedMotion();
      else {
        progress = getScrollProgress();
        targetProgress = progress;
        autoplay = progress <= 0.001;
        wake();
      }
    });
  }

  if (fallbackWasShown) {
    autoplay = false;
    progress = 1;
    targetProgress = 1;
  }

  resizeCanvas();
  lastScrollProgress = getScrollProgress();
  updateHandoff(lastScrollProgress);
  if (reduceMotion.matches) {
    applyReducedMotion();
  } else if (lastScrollProgress > 0.001) {
    autoplay = false;
    progress = lastScrollProgress;
    targetProgress = progress;
    render(progress);
    wake();
  } else {
    wake();
  }

  Array.from(document.querySelectorAll('a[href="#architecture"]')).forEach(function (link) {
    link.addEventListener("click", function () {
      window.requestAnimationFrame(function () {
        try {
          hero.focus({ preventScroll: true });
        } catch (error) {
          hero.focus();
        }
      });
    });
  });
})();
