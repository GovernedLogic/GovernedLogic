/* Presentation only. Page labels come from the document; discovery from the generated corpus. */
(() => {
  'use strict';
  if (!window.HTMLDialogElement || !HTMLDialogElement.prototype.showModal) return;
  if (document.getElementById('gl-explore-dialog')) return;

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const normalize = value => String(value || '').replace(/\s+/g, ' ').trim();
  const sectionTargets = [...document.querySelectorAll('header[id], main[id], main > section[id], main > article > section[id]')];
  // Some older documents anchor their heading rather than its section wrapper.
  document.querySelectorAll('main h1[id], main h2[id]').forEach(heading => {
    const covered = sectionTargets.some(target => (target.matches('section,header') && target.contains(heading)) || target.querySelector(':scope > h1, :scope > h2, :scope > article > h1') === heading);
    if (!covered) sectionTargets.push(heading);
  });
  sectionTargets.sort((a, b) => a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1);
  const sections = sectionTargets
    .map(target => {
      const heading = target.matches('h1,h2') ? target : target.querySelector(':scope > h1, :scope > h2, :scope > article > h1');
      return heading ? { target, heading, title: normalize(heading.textContent), url: '#' + encodeURIComponent(target.id), type: 'section' } : null;
    }).filter(Boolean);
  const origin = document.getElementById('origin');
  const root = document.createElement('div');
  root.className = 'gl-navigation';
  root.dataset.hand = 'right';
  root.setAttribute('data-gl-navigation', '');
  root.innerHTML = `
    <button id="gl-explore-trigger" class="gl-explore-trigger" type="button" aria-haspopup="dialog" aria-controls="gl-explore-dialog" aria-expanded="false">
      <span class="gl-compass" aria-hidden="true"><i></i></span><span>Explore</span><span class="gl-trigger-key" aria-hidden="true">⌘ / Ctrl K</span>
    </button>
    <dialog id="gl-explore-dialog" class="gl-explore-dialog" aria-labelledby="gl-explore-title" aria-describedby="gl-explore-description">
      <div class="gl-explore-surface">
        <div class="gl-explore-heading"><span class="gl-eyebrow">Governed Logic</span><h2 id="gl-explore-title">Explore</h2><p id="gl-explore-description">Your place in the page. A way into the library.</p></div>
        <div class="gl-location"><span class="gl-location-dot" aria-hidden="true"></span><span class="gl-current-location"></span></div>
        <div id="gl-nav-panel" class="gl-nav-panel" role="tabpanel" aria-labelledby="gl-page-tab"><ol class="gl-nav-results"></ol><p class="gl-empty" hidden></p></div>
        <div class="gl-controls">
          <p class="gl-nav-status" role="status" aria-live="polite" aria-atomic="true"></p>
          <label for="gl-nav-search" class="gl-search-label">Find a section on this page</label><div class="gl-search-wrap"><span aria-hidden="true">⌕</span><input id="gl-nav-search" type="search" autocomplete="off" spellcheck="false" placeholder="Find on this page"><button class="gl-clear-search" type="button" aria-label="Clear search" hidden>×</button></div>
          <div class="gl-tabs" role="tablist" aria-label="Explore destinations"><button id="gl-page-tab" type="button" role="tab" aria-selected="true" aria-controls="gl-nav-panel">Page</button><button id="gl-library-tab" type="button" role="tab" aria-selected="false" aria-controls="gl-nav-panel" tabindex="-1">Library</button></div>
          <div class="gl-section-tools"><div class="gl-scrub" role="slider" tabindex="0" aria-label="Preview page sections" aria-describedby="gl-scrub-help"><span class="gl-scrub-line" aria-hidden="true"></span><span class="gl-scrub-point" aria-hidden="true"></span></div><p id="gl-scrub-help">Slide to preview. Release to visit. Arrow keys, then Enter.</p></div>
          <div class="gl-reach-row"><a class="gl-previous" aria-label="Previous section"><span aria-hidden="true">←</span></a><a class="gl-next" aria-label="Next section"><span aria-hidden="true">→</span></a><button class="gl-hand-switch" type="button" aria-label="Switch controls to the left side">Right hand</button><button class="gl-close" type="button" aria-label="Close navigation">Close <span aria-hidden="true">×</span></button></div>
          <div class="gl-explore-footer"><a href="/library/">Open full library ↗</a><button class="gl-motion" type="button" aria-pressed="false">Device motion: off</button></div>
          <p class="gl-motion-status gl-sr-only" role="status" aria-live="polite"></p>
        </div>
      </div>
    </dialog>`;
  document.body.append(root);

  const find = selector => root.querySelector(selector);
  const trigger = find('#gl-explore-trigger');
  const dialog = find('#gl-explore-dialog');
  const surface = find('.gl-explore-surface');
  const results = find('.gl-nav-results');
  const empty = find('.gl-empty');
  const search = find('#gl-nav-search');
  const searchLabel = find('label[for="gl-nav-search"]');
  const clear = find('.gl-clear-search');
  const pageTab = find('#gl-page-tab');
  const libraryTab = find('#gl-library-tab');
  const panel = find('#gl-nav-panel');
  const status = find('.gl-nav-status');
  const locationLabel = find('.gl-current-location');
  const previous = find('.gl-previous');
  const next = find('.gl-next');
  const sectionTools = find('.gl-section-tools');
  const scrub = find('.gl-scrub');
  const handSwitch = find('.gl-hand-switch');
  const motionButton = find('.gl-motion');
  const motionStatus = find('.gl-motion-status');
  let mode = 'page', current = -1, preview = -1, catalog = null, catalogRequest = null;
  let opener = trigger, restoreFocus = true, pendingScroll = 0, searchTimer = 0, pointer = null;
  let motionActive = false, motionWanted = false, motionFrame = 0, motionOrigin = null;
  let motionX = 0, motionY = 0, motionRequest = 0, motionSensorTimer = 0;

  function setHand(side) {
    root.dataset.hand = side === 'left' ? 'left' : 'right';
    const left = root.dataset.hand === 'left';
    handSwitch.textContent = left ? 'Left hand' : 'Right hand';
    handSwitch.setAttribute('aria-label', `Switch controls to the ${left ? 'right' : 'left'} side`);
  }
  try { setHand(localStorage.getItem('gl-navigation-hand')); } catch { setHand('right'); }
  handSwitch.addEventListener('click', () => {
    setHand(root.dataset.hand === 'left' ? 'right' : 'left');
    try { localStorage.setItem('gl-navigation-hand', root.dataset.hand); } catch { /* Session preference still works. */ }
  });

  function localUrl(value) {
    try {
      const url = new URL(value, location.href);
      if (!['https:', 'http:'].includes(url.protocol)) return null;
      if (url.origin !== location.origin && url.hostname !== 'governedlogic.com' && url.hostname !== 'www.governedlogic.com') return null;
      return url.pathname + url.search + url.hash;
    } catch { return null; }
  }
  function termsFor(value) { return normalize(value).toLocaleLowerCase().split(' ').filter(Boolean); }
  function matches(record, terms) {
    const title = record.title.toLocaleLowerCase();
    const body = (record.title + ' ' + (record.text || '')).toLocaleLowerCase();
    return terms.every(term => body.includes(term)) ? terms.reduce((score, term) => score + (title.includes(term) ? 10 : 1), 0) : -1;
  }
  function render() {
    const terms = termsFor(search.value);
    clear.hidden = !search.value;
    const source = mode === 'page' ? sections : catalog || [];
    const visible = source.map((record, index) => ({ record, index, score: matches(record, terms) })).filter(item => item.score >= 0);
    if (mode === 'library' && terms.length) visible.sort((a, b) => b.score - a.score || a.index - b.index);
    results.replaceChildren();
    const fragment = document.createDocumentFragment();
    visible.slice(0, 60).forEach(({ record, index }) => {
      const li = document.createElement('li');
      const link = document.createElement('a');
      link.href = record.url;
      const number = document.createElement('span');
      number.className = 'gl-result-number';
      number.setAttribute('aria-hidden', 'true');
      number.textContent = mode === 'page' ? String(index + 1).padStart(2, '0') : '↗';
      const copy = document.createElement('span');
      copy.className = 'gl-result-copy';
      const title = document.createElement('span');
      title.textContent = record.title;
      copy.append(title);
      if (mode === 'library' && record.type) {
        const type = document.createElement('small');
        type.textContent = record.type;
        copy.append(type);
      }
      if (mode === 'page') {
        link.dataset.section = String(index);
        if (index === current) link.setAttribute('aria-current', 'location');
      }
      link.append(number, copy);
      li.append(link);
      fragment.append(li);
    });
    results.append(fragment);
    const loading = mode === 'library' && catalog === null;
    empty.hidden = !!visible.length || loading;
    empty.textContent = terms.length ? 'No matching destinations. Try another word or open the full library.' : 'No addressable sections on this page. Explore the library.';
    status.textContent = loading ? 'Loading library…' : `${visible.length} ${visible.length === 1 ? 'destination' : 'destinations'}${visible.length > 60 ? ' · first 60 shown; refine your search' : ''}`;
  }
  async function loadCatalog() {
    if (catalog) return;
    if (!catalogRequest) catalogRequest = fetch('/publication/search-index.json', { credentials: 'same-origin' })
      .then(response => { if (!response.ok) throw new Error('Index unavailable'); return response.json(); })
      .then(data => {
        const records = Array.isArray(data) ? data : data.records;
        if (!Array.isArray(records)) throw new Error('Index invalid');
        catalog = records.map(record => ({ title: normalize(record.title), url: localUrl(record.url), type: normalize(record.type), text: typeof record.text === 'string' ? record.text : '' }))
          .filter(record => record.title && record.url);
      });
    try {
      await catalogRequest;
      if (dialog.open && mode === 'library') render();
    } catch {
      catalogRequest = null;
      if (dialog.open && mode === 'library') {
        status.textContent = 'Library search is unavailable. Use the full library link below.';
        empty.hidden = false;
        empty.textContent = 'The full library remains available without search.';
      }
    }
  }
  function setMode(value) {
    mode = value;
    const page = mode === 'page';
    pageTab.setAttribute('aria-selected', String(page));
    libraryTab.setAttribute('aria-selected', String(!page));
    pageTab.tabIndex = page ? 0 : -1;
    libraryTab.tabIndex = page ? -1 : 0;
    panel.setAttribute('aria-labelledby', page ? pageTab.id : libraryTab.id);
    search.placeholder = page ? 'Find on this page' : 'Search the canonical library';
    searchLabel.textContent = page ? 'Find a section on this page' : 'Search the canonical library';
    sectionTools.hidden = !page || sections.length < 2;
    render();
    if (!page) loadCatalog();
  }
  pageTab.addEventListener('click', () => setMode('page'));
  libraryTab.addEventListener('click', () => setMode('library'));
  find('.gl-tabs').addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const page = event.key === 'Home' || (event.key !== 'End' && mode !== 'page');
    setMode(page ? 'page' : 'library');
    (page ? pageTab : libraryTab).focus();
  });
  search.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(render, 100);
  });
  clear.addEventListener('click', () => { search.value = ''; render(); search.focus(); });

  function setStep(link, index, label) {
    const record = sections[index];
    if (record) {
      link.href = record.url;
      link.removeAttribute('aria-disabled');
      link.setAttribute('aria-label', `${label}: ${record.title}`);
    } else {
      link.removeAttribute('href');
      link.setAttribute('aria-disabled', 'true');
      link.setAttribute('aria-label', label);
    }
  }
  function showPreview(index) {
    preview = Math.max(0, Math.min(sections.length - 1, index));
    const record = sections[preview];
    if (!record) return;
    scrub.setAttribute('aria-valuenow', String(preview + 1));
    scrub.setAttribute('aria-valuetext', record.title);
    scrub.style.setProperty('--position', sections.length > 1 ? String(preview / (sections.length - 1)) : '0');
    locationLabel.textContent = (preview === current ? '' : 'Preview · ') + record.title;
  }
  function updatePosition() {
    pendingScroll = 0;
    const inOrigin = !!origin && origin.getBoundingClientRect().bottom > innerHeight * .35;
    root.classList.toggle('gl-at-origin', inOrigin);
    let index = -1;
    sections.forEach((record, i) => { if (record.target.getBoundingClientRect().top <= innerHeight * .3) index = i; });
    if (index < 0 && !inOrigin && sections.length) index = 0;
    const changed = index !== current;
    current = index;
    setStep(previous, current - 1, 'Previous section');
    setStep(next, current + 1, 'Next section');
    if (!pointer) {
      showPreview(Math.max(0, current));
      if (current < 0) locationLabel.textContent = origin?.getAttribute('aria-label') || 'On this page';
    }
    if (changed) results.querySelectorAll('[data-section]').forEach(link => {
      if (+link.dataset.section === current) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }
  function queuePosition() { if (!pendingScroll) pendingScroll = requestAnimationFrame(updatePosition); }
  addEventListener('scroll', queuePosition, { passive: true });
  addEventListener('resize', queuePosition, { passive: true });
  addEventListener('hashchange', queuePosition);
  scrub.setAttribute('aria-valuemin', '1');
  scrub.setAttribute('aria-valuemax', String(Math.max(1, sections.length)));
  scrub.setAttribute('aria-orientation', 'horizontal');

  function focusTarget(target) {
    if (!target) return;
    const temporary = !target.hasAttribute('tabindex');
    if (temporary) target.tabIndex = -1;
    target.focus({ preventScroll: true });
    if (temporary) target.addEventListener('blur', () => target.removeAttribute('tabindex'), { once: true });
  }
  function close(restore = true) {
    restoreFocus = restore;
    dialog.close();
  }
  function visit(index) {
    const record = sections[index];
    if (!record) return;
    close(false);
    location.hash = record.url.slice(1);
    requestAnimationFrame(() => focusTarget(record.heading));
  }
  dialog.addEventListener('click', event => {
    const link = event.target.closest('a');
    if (link?.getAttribute('aria-disabled') === 'true') { event.preventDefault(); return; }
    if (link && !event.ctrlKey && !event.metaKey && !event.altKey && !event.shiftKey && event.button === 0) {
      const url = new URL(link.href);
      let target = null;
      if (url.pathname === location.pathname && url.hash) {
        try { target = document.getElementById(decodeURIComponent(url.hash.slice(1))); } catch { /* Native fragment navigation remains available. */ }
      }
      close(false);
      if (target) requestAnimationFrame(() => focusTarget(target.querySelector('h1,h2') || target));
      return;
    }
    if (event.target === dialog) {
      const bounds = dialog.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) close();
    }
  });
  function positionFromPointer(event) {
    const bounds = scrub.getBoundingClientRect();
    return Math.round(Math.max(0, Math.min(1, (event.clientX - bounds.left - 12) / Math.max(1, bounds.width - 24))) * (sections.length - 1));
  }
  scrub.addEventListener('pointerdown', event => {
    if (event.button !== 0 || !event.isPrimary) return;
    pointer = { id: event.pointerId };
    scrub.setPointerCapture(event.pointerId);
    scrub.classList.add('gl-scrubbing');
    showPreview(positionFromPointer(event));
  });
  scrub.addEventListener('pointermove', event => {
    if (pointer?.id === event.pointerId) showPreview(positionFromPointer(event));
  });
  function cancelScrub() {
    pointer = null;
    scrub.classList.remove('gl-scrubbing');
    updatePosition();
  }
  scrub.addEventListener('pointercancel', cancelScrub);
  scrub.addEventListener('lostpointercapture', () => { if (pointer) cancelScrub(); });
  scrub.addEventListener('pointerup', event => {
    if (pointer?.id !== event.pointerId) return;
    const index = preview;
    pointer = null;
    scrub.classList.remove('gl-scrubbing');
    visit(index);
  });
  scrub.addEventListener('keydown', event => {
    let index = preview;
    if (event.key === 'ArrowRight' || event.key === 'ArrowUp') index++;
    else if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') index--;
    else if (event.key === 'Home') index = 0;
    else if (event.key === 'End') index = sections.length - 1;
    else if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); visit(preview); return; }
    else return;
    event.preventDefault();
    showPreview(index);
  });

  function stopMotion() {
    removeEventListener('deviceorientation', orient);
    motionActive = false;
    motionOrigin = null;
    clearTimeout(motionSensorTimer);
    cancelAnimationFrame(motionFrame);
    motionFrame = 0;
    surface.style.removeProperty('--tilt-x');
    surface.style.removeProperty('--tilt-y');
    motionButton.setAttribute('aria-pressed', 'false');
    motionButton.textContent = 'Device motion: off';
  }
  function orient(event) {
    if (!dialog.open || document.hidden || reduced.matches || !Number.isFinite(event.beta) || !Number.isFinite(event.gamma)) return;
    if (!motionOrigin) {
      motionOrigin = { beta: event.beta, gamma: event.gamma };
      clearTimeout(motionSensorTimer);
      motionButton.textContent = 'Device motion: on';
    }
    motionX = Math.max(-1.5, Math.min(1.5, (event.beta - motionOrigin.beta) * -.06));
    motionY = Math.max(-1.5, Math.min(1.5, (event.gamma - motionOrigin.gamma) * .06));
    if (!motionFrame) motionFrame = requestAnimationFrame(() => {
      motionFrame = 0;
      surface.style.setProperty('--tilt-x', motionX + 'deg');
      surface.style.setProperty('--tilt-y', motionY + 'deg');
    });
  }
  function startMotion() {
    if (reduced.matches || !dialog.open || document.hidden) return;
    motionActive = true;
    addEventListener('deviceorientation', orient, { passive: true });
    motionButton.setAttribute('aria-pressed', 'true');
    motionButton.textContent = 'Device motion: waiting';
    motionSensorTimer = setTimeout(() => {
      if (!motionOrigin && dialog.open) {
        motionWanted = false;
        stopMotion();
        motionButton.textContent = 'Device motion: unavailable';
        motionStatus.textContent = 'No motion data is available on this device. Navigation works without it.';
      }
    }, 2200);
  }
  motionButton.addEventListener('click', async () => {
    const request = ++motionRequest;
    if (motionWanted || motionActive) { motionWanted = false; stopMotion(); return; }
    if (reduced.matches) { motionStatus.textContent = 'Device motion is off because reduced motion is enabled.'; return; }
    if (!window.isSecureContext || typeof window.DeviceOrientationEvent === 'undefined') {
      motionStatus.textContent = 'Device motion is unavailable here. All navigation works by touch, mouse, or keyboard.';
      motionButton.textContent = 'Device motion: unavailable';
      return;
    }
    try {
      const permission = typeof DeviceOrientationEvent.requestPermission === 'function' ? await DeviceOrientationEvent.requestPermission() : 'granted';
      if (request !== motionRequest || !dialog.open) return;
      if (permission !== 'granted') { motionStatus.textContent = 'Motion permission was not granted. Navigation is unchanged.'; return; }
      motionWanted = true;
      startMotion();
      motionStatus.textContent = 'Optional panel depth enabled. Move your device gently; movement never selects a destination.';
    } catch { motionStatus.textContent = 'Device motion could not be enabled. Navigation is unchanged.'; }
  });
  reduced.addEventListener('change', () => { if (reduced.matches) { motionWanted = false; ++motionRequest; stopMotion(); } });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stopMotion();
    else if (motionWanted && dialog.open) startMotion();
  });
  function open(searchLibrary = false) {
    if (!dialog.open) {
      opener = document.activeElement instanceof HTMLElement ? document.activeElement : trigger;
      restoreFocus = true;
      dialog.showModal();
      document.documentElement.classList.add('gl-navigation-open');
      trigger.setAttribute('aria-expanded', 'true');
      updatePosition();
    }
    if (searchLibrary) setMode('library'); else setMode(mode);
    if (searchLibrary || matchMedia('(pointer:fine)').matches) search.focus({ preventScroll: true });
    else (mode === 'page' ? pageTab : libraryTab).focus({ preventScroll: true });
  }
  trigger.addEventListener('click', () => open());
  find('.gl-close').addEventListener('click', () => close());
  dialog.addEventListener('cancel', cancelScrub);
  dialog.addEventListener('close', () => {
    ++motionRequest;
    motionWanted = false;
    stopMotion();
    cancelScrub();
    document.documentElement.classList.remove('gl-navigation-open');
    trigger.setAttribute('aria-expanded', 'false');
    if (restoreFocus && opener?.isConnected) opener.focus({ preventScroll: true });
    restoreFocus = true;
  });
  document.addEventListener('keydown', event => {
    const editable = event.target instanceof Element && event.target.closest('input,textarea,select,[contenteditable]:not([contenteditable="false"])');
    if ((event.ctrlKey || event.metaKey) && !event.altKey && event.key.toLocaleLowerCase() === 'k' && !editable) {
      event.preventDefault();
      open(true);
    }
  });
  updatePosition();
  setMode('page');
  document.documentElement.classList.add('gl-nav-ready');
})();
