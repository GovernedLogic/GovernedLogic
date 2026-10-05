/* Native, deterministic material environment for the Governed Logic opening. */
(() => {
  'use strict';
  const TAU = Math.PI * 2;
  const random = n => {
    const value = Math.sin(n * 127.13 + 91.719) * 43758.5453;
    return value - Math.floor(value);
  };

  window.GLMaterialEnvironment = function renderEnvironment(ctx, options) {
    const { width, height, cx, base, scale } = options;
    const s = Math.max(.01, scale);
    const horizon = base + 152 * s;
    const focal = 760 * s;
    const cameraHeight = 1.28;
    const centerDepth = 14.5;
    const reflectionY = horizon + focal * cameraHeight / centerDepth;

    function radial(x, y, radius, stops) {
      if (radius <= 0) return;
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
      stops.forEach(([offset, color]) => gradient.addColorStop(offset, color));
      ctx.fillStyle = gradient;
      ctx.fillRect(x - radius, y - radius, radius * 2, radius * 2);
    }

    function ellipseLight(x, y, rx, ry, stops) {
      ctx.save();
      ctx.translate(x, y);
      ctx.scale(1, ry / rx);
      radial(0, 0, rx, stops);
      ctx.restore();
    }

    function project(x, z) {
      if (z < .9) return null;
      return { x: cx + focal * x / z, y: horizon + focal * cameraHeight / z };
    }

    function pathWorld(points, color, lineWidth, yOffset = 0) {
      ctx.beginPath();
      let started = false;
      points.forEach(([x, z]) => {
        const point = project(x, z);
        if (!point || point.y > height + 120 * s) {
          started = false;
          return;
        }
        if (!started) ctx.moveTo(point.x, point.y + yOffset);
        else ctx.lineTo(point.x, point.y + yOffset);
        started = true;
      });
      ctx.strokeStyle = color;
      ctx.lineWidth = Math.max(.28, lineWidth);
      ctx.stroke();
    }

    function ring(radius, start, end, color, lineWidth, offset = 0) {
      const steps = Math.max(18, Math.ceil((end - start) * 105));
      const points = [];
      for (let i = 0; i <= steps; i++) {
        const angle = start + (end - start) * i / steps;
        points.push([Math.cos(angle) * radius, centerDepth + Math.sin(angle) * radius]);
      }
      pathWorld(points, color, lineWidth, offset);
    }

    ctx.save();
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = '#000204';
    ctx.fillRect(0, 0, width, height);

    // A dark overhead environment is reflected by the title and polished floor.
    const atmosphere = ctx.createRadialGradient(cx, base - 420 * s, 0, cx, base - 335 * s, 820 * s);
    atmosphere.addColorStop(0, '#182a37');
    atmosphere.addColorStop(.32, '#0b151e');
    atmosphere.addColorStop(.7, '#020609');
    atmosphere.addColorStop(1, '#000102');
    ctx.fillStyle = atmosphere;
    ctx.fillRect(0, 0, width, height);
    ellipseLight(cx, base - 440 * s, 470 * s, 190 * s, [
      [0, '#536b7720'], [.3, '#344e5f12'], [1, '#00000000']
    ]);

    // Fine recessed traces form marginal circuitry, rather than a foreground grid.
    for (const side of [-1, 1]) {
      const boundary = side < 0 ? 0 : width;
      const direction = -side;
      for (let row = 0; row < 58; row++) {
        const seed = row + (side < 0 ? 111 : 877);
        const y = base + (-402 + row * 8.2 + random(seed) * 3) * s;
        const reach = (112 + random(seed + 6) * 265) * s;
        const start = -random(seed + 2) * 50 * s;
        const a = reach * (.23 + random(seed + 4) * .12);
        const b = a + (12 + random(seed + 8) * 30) * s;
        const c = reach * (.66 + random(seed + 12) * .13);
        const rise = (row % 3 === 0 ? -1 : 1) * (10 + random(seed + 10) * 13) * s;
        const points = [
          [start, y], [a, y], [b, y + rise],
          [c, y + rise], [c + Math.abs(rise) * .6, y + rise * 1.6],
          [reach, y + rise * 1.6]
        ];
        const opacity = .07 + random(seed + 16) * .16;
        function trace(color, lineWidth, offset) {
          ctx.beginPath();
          points.forEach(([x, py], index) => {
            const screenX = boundary + direction * x;
            if (!index) ctx.moveTo(screenX, py + offset);
            else ctx.lineTo(screenX, py + offset);
          });
          ctx.strokeStyle = color;
          ctx.lineWidth = Math.max(.32, lineWidth);
          ctx.stroke();
        }
        trace('#00080be0', 2.1 * s, .8 * s);
        trace(`rgba(31,100,133,${opacity})`, .68 * s, 0);
        if (row % 7 === 1) trace('#4fa8c828', .48 * s, -.7 * s);
        const terminalX = boundary + direction * reach;
        const terminalY = points[points.length - 1][1];
        ctx.beginPath();
        ctx.arc(terminalX, terminalY, (1.5 + random(seed + 33)) * s, 0, TAU);
        ctx.strokeStyle = `rgba(70,167,207,${opacity + .06})`;
        ctx.lineWidth = Math.max(.35, .6 * s);
        ctx.stroke();
        if (row % 13 === 3) {
          radial(terminalX, terminalY, 12 * s, [
            [0, '#e5faffab'], [.03, '#a1e6ff80'], [.15, '#239ad72b'], [1, '#0069aa00']
          ]);
        }
        // Tiny solder lands repeat as hardware features, not random particles.
        if (row % 3 === 0) {
          for (let pad = 0; pad < 7; pad++) {
            const px = boundary + direction * (25 + pad * 12 + random(seed + 25) * 45) * s;
            ctx.fillStyle = '#071921';
            ctx.fillRect(px, y - 3.4 * s, 3.5 * s, 1.1 * s);
            ctx.fillStyle = '#22648135';
            ctx.fillRect(px, y - 3.4 * s, 3.5 * s, .45 * s);
          }
        }
      }
    }

    ctx.save();
    ctx.beginPath();
    ctx.rect(0, horizon - 22 * s, width, Math.max(1, height - horizon + 22 * s));
    ctx.clip();
    // The plane has a continuous dark material beneath its etchings.
    const floor = ctx.createLinearGradient(0, horizon - 22 * s, 0, height);
    floor.addColorStop(0, '#030b1100');
    floor.addColorStop(.08, '#0a1922eb');
    floor.addColorStop(.31, '#051019');
    floor.addColorStop(1, '#000203');
    ctx.fillStyle = floor;
    ctx.fillRect(0, horizon - 22 * s, width, height);
    ellipseLight(cx, horizon + 35 * s, 1010 * s, 91 * s, [
      [0, '#3d86ac62'], [.25, '#236f9340'], [.6, '#11446122'], [1, '#00000000']
    ]);
    ellipseLight(cx, reflectionY, 650 * s, 57 * s, [
      [0, '#8abbce58'], [.15, '#5a9cbb40'], [.52, '#32769822'], [1, '#00000000']
    ]);
    // The broad reflected light exposes the surface on the camera side as well.
    ellipseLight(cx + 12 * s, reflectionY + 92 * s, 158 * s, 230 * s, [
      [0, '#367ba732'], [.18, '#23689326'], [.6, '#13456713'], [1, '#00000000']
    ]);

    // Circular machining is located in world space and foreshortened by the camera.
    for (let index = 0; index < 25; index++) {
      const radius = .44 + Math.pow(index, 1.27) * .37;
      const strength = .078 + random(index + 427) * .1;
      ring(radius, 0, TAU, '#00040875', 1.45 * s, .72 * s);
      ring(radius, 0, TAU, `rgba(107,165,188,${strength})`, .7 * s);
      const start = .2 + random(index + 519) * 1.45;
      ring(radius, start, start + .23 + random(index + 522) * .63,
        `rgba(158,220,243,${.15 + random(index + 534) * .23})`, .79 * s);
      if (index % 2 === 0) {
        const nearArc = TAU * (.58 + random(index + 538) * .3);
        ring(radius, nearArc, nearArc + .19 + random(index + 541) * .36,
          '#91d6f073', .83 * s);
      }
      if (index % 3 === 0) {
        ring(radius, Math.PI + .22, Math.PI + .8, '#52b5d939', .6 * s);
        ring(radius + .035, .48, .95, '#02070cc9', 1.35 * s);
      }
    }

    // Irregular routed paths sit on the same surface as the rings.
    for (let index = 0; index < 106; index++) {
      const z = 2.15 + random(index + 710) * 31;
      const x = (random(index + 731) - .5) * 46;
      const step = .08 + random(index + 748) * .7;
      const run = .23 + random(index + 774) * 2.9;
      const turn = random(index + 795) > .5 ? 1 : -1;
      const points = [[x, z + run], [x, z + step], [x + turn * step, z], [x + turn * (step + run * .25), z]];
      pathWorld(points, '#000002b8', 1.9 * s, .65 * s);
      const strength = .075 + random(index + 816) * .13;
      pathWorld(points, `rgba(76,153,184,${strength})`, .75 * s);
      if (index % 13 === 2) {
        pathWorld(points.slice(1), '#8ed9ed83', .91 * s, -.35 * s);
      }
      if (index % 7 === 0) {
        const pad = project(x, z + run);
        if (pad && pad.y < height) {
          const size = Math.max(.4, Math.min(2.8 * s, focal * .014 / z));
          ctx.fillStyle = '#75b2c754';
          ctx.fillRect(pad.x - size, pad.y, size * 2.4, Math.max(.35, size * .32));
        }
      }
    }

    // Sparse grazing reflections expose polishing marks without visual noise.
    for (let index = 0; index < 94; index++) {
      const z = 2 + random(index + 935) * 27;
      const x = (random(index + 957) - .5) * 29;
      const length = .08 + random(index + 973) * .83;
      pathWorld([[x, z], [x + length, z + length * .017]],
        `rgba(103,165,190,${.018 + random(index + 986) * .027})`, .42 * s);
    }

    // This tapered reflection is aligned with the identity's central light.
    ctx.globalCompositeOperation = 'screen';
    ellipseLight(cx, reflectionY + 29 * s, 72 * s, 214 * s, [
      [0, '#7bc9ef65'], [.17, '#409ec542'], [.58, '#256d9e22'], [1, '#00131b00']
    ]);
    ellipseLight(cx, reflectionY, 285 * s, 20 * s, [
      [0, '#e1f5ffad'], [.07, '#b4e7f77a'], [.26, '#74cce74a'], [1, '#00548500']
    ]);
    ellipseLight(cx, reflectionY, 53 * s, 57 * s, [
      [0, '#f2fcffcb'], [.035, '#e7fbfff0'], [.12, '#b7f0ff8f'], [.38, '#60b5df43'], [1, '#00629b00']
    ]);
    // The streak has small breaks from the surface instead of a laser line.
    for (let index = 0; index < 28; index++) {
      const t = index / 28;
      const y = reflectionY - 18 * s + (t * t * 266) * s;
      const segment = (2.7 + t * 6.5) * s;
      const offset = (random(index + 1127) - .5) * (1.6 + t * 6) * s;
      const alpha = (.34 - t * .25) * (.45 + random(index + 1140) * .55);
      const grad = ctx.createLinearGradient(cx - 7 * s, 0, cx + 7 * s, 0);
      grad.addColorStop(0, '#429cd200');
      grad.addColorStop(.43, `rgba(96,183,220,${alpha * .3})`);
      grad.addColorStop(.5, `rgba(210,242,251,${alpha})`);
      grad.addColorStop(.57, `rgba(96,183,220,${alpha * .3})`);
      grad.addColorStop(1, '#429cd200');
      ctx.fillStyle = grad;
      ctx.fillRect(cx - 7 * s + offset, y, 14 * s, segment);
    }
    ctx.restore();

    // The material falls away into black at the edges, leaving clear composition.
    const vignette = ctx.createRadialGradient(cx, base + 30 * s, 240 * s, cx, base, Math.max(width * .65, height * .84));
    vignette.addColorStop(0, '#00000000');
    vignette.addColorStop(.57, '#00000000');
    vignette.addColorStop(1, '#000000a3');
    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, width, height);
    ctx.restore();
  };
})();
