/* ============================================
   TOOLTIP SYSTEM — Vanilla JS
   Converted from SupplyWise tooltip.tsx (Base UI / Radix)

   Usage:
     Add  data-tooltip="Your text here"  to any element.
     Optionally add  data-tooltip-side="top|bottom|left|right"  (default: top)
     Call  initTooltips()  after the DOM is ready.
   ============================================ */

(function () {
  'use strict';

  // ── Shared tooltip DOM element ──────────────────────────────────────────────
  let box = null;
  let arrow = null;
  let hideTimer = null;
  let showTimer = null;
  const DELAY_SHOW = 120;   // ms before showing  (matches SupplyWise delay=0 but slight UX grace)
  const DELAY_HIDE = 80;    // ms before hiding
  const OFFSET = 8;         // px gap between trigger and tooltip box (≈ sideOffset: 4 in SupplyWise)

  function createTooltipDOM() {
    if (box) return;

    // Inject keyframes + base styles once
    if (!document.getElementById('re-tooltip-styles')) {
      const style = document.createElement('style');
      style.id = 're-tooltip-styles';
      style.textContent = `
        /* ── Tooltip box ── */
        #re-tooltip-box {
          position: fixed;
          z-index: 10000;
          pointer-events: none;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          max-width: 240px;
          padding: 5px 10px;
          border-radius: 6px;
          font-size: 0.72rem;
          font-weight: 500;
          line-height: 1.4;
          letter-spacing: 0.01em;
          white-space: nowrap;
          background: var(--text, #e8e8e8);
          color: var(--bg, #0d0d0d);
          box-shadow: 0 4px 16px rgba(0,0,0,0.35);
          opacity: 0;
          transform: scale(0.92) translateY(4px);
          transition:
            opacity 0.15s ease,
            transform 0.15s cubic-bezier(0.175, 0.885, 0.32, 1.275);
          will-change: opacity, transform;
        }
        #re-tooltip-box.tt-visible {
          opacity: 1;
          transform: scale(1) translateY(0);
        }
        #re-tooltip-box.tt-side-bottom {
          transform: scale(0.92) translateY(-4px);
        }
        #re-tooltip-box.tt-side-bottom.tt-visible {
          transform: scale(1) translateY(0);
        }
        #re-tooltip-box.tt-side-left {
          transform: scale(0.92) translateX(4px);
        }
        #re-tooltip-box.tt-side-left.tt-visible {
          transform: scale(1) translateX(0);
        }
        #re-tooltip-box.tt-side-right {
          transform: scale(0.92) translateX(-4px);
        }
        #re-tooltip-box.tt-side-right.tt-visible {
          transform: scale(1) translateX(0);
        }

        /* ── Arrow ── */
        #re-tooltip-arrow {
          position: fixed;
          z-index: 10001;
          pointer-events: none;
          width: 9px;
          height: 9px;
          background: var(--text, #e8e8e8);
          border-radius: 2px;
          transform: rotate(45deg);
          opacity: 0;
          transition: opacity 0.15s ease;
        }
        #re-tooltip-arrow.tt-visible {
          opacity: 1;
        }

        /* ── Light-mode ── */
        [data-theme="light"] #re-tooltip-box {
          background: var(--text, #212529);
          color: var(--text-inv, #ffffff);
        }
        [data-theme="light"] #re-tooltip-arrow {
          background: var(--text, #212529);
        }
      `;
      document.head.appendChild(style);
    }

    box = document.createElement('div');
    box.id = 're-tooltip-box';
    box.setAttribute('role', 'tooltip');
    box.setAttribute('aria-live', 'polite');
    document.body.appendChild(box);

    arrow = document.createElement('div');
    arrow.id = 're-tooltip-arrow';
    document.body.appendChild(arrow);
  }

  // ── Positioning logic ───────────────────────────────────────────────────────
  function positionTooltip(trigger, side) {
    const tr = trigger.getBoundingClientRect();
    const bw = box.offsetWidth;
    const bh = box.offsetHeight;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const arrowSize = 9;
    let x, y, ax, ay, resolvedSide = side;

    // Auto-flip if preferred side doesn't fit
    if (side === 'top' && tr.top < bh + OFFSET + arrowSize) resolvedSide = 'bottom';
    else if (side === 'bottom' && tr.bottom + bh + OFFSET + arrowSize > vh) resolvedSide = 'top';
    else if (side === 'left' && tr.left < bw + OFFSET + arrowSize) resolvedSide = 'right';
    else if (side === 'right' && tr.right + bw + OFFSET + arrowSize > vw) resolvedSide = 'left';

    if (resolvedSide === 'top') {
      x = tr.left + tr.width / 2 - bw / 2;
      y = tr.top - bh - OFFSET - arrowSize / 2;
      ax = tr.left + tr.width / 2 - arrowSize / 2;
      ay = tr.top - OFFSET - arrowSize / 2;
    } else if (resolvedSide === 'bottom') {
      x = tr.left + tr.width / 2 - bw / 2;
      y = tr.bottom + OFFSET + arrowSize / 2;
      ax = tr.left + tr.width / 2 - arrowSize / 2;
      ay = tr.bottom + OFFSET - arrowSize / 2;
    } else if (resolvedSide === 'left') {
      x = tr.left - bw - OFFSET - arrowSize / 2;
      y = tr.top + tr.height / 2 - bh / 2;
      ax = tr.left - OFFSET - arrowSize / 2;
      ay = tr.top + tr.height / 2 - arrowSize / 2;
    } else { // right
      x = tr.right + OFFSET + arrowSize / 2;
      y = tr.top + tr.height / 2 - bh / 2;
      ax = tr.right + OFFSET - arrowSize / 2;
      ay = tr.top + tr.height / 2 - arrowSize / 2;
    }

    // Clamp to viewport edges (8px margin)
    x = Math.max(8, Math.min(x, vw - bw - 8));
    y = Math.max(8, Math.min(y, vh - bh - 8));

    box.style.left = x + 'px';
    box.style.top  = y + 'px';
    arrow.style.left = ax + 'px';
    arrow.style.top  = ay + 'px';

    // Remove old side classes, add new one
    box.className = box.className.replace(/tt-side-\w+/g, '').trim();
    box.classList.add('tt-side-' + resolvedSide);
  }

  // ── Show / Hide ─────────────────────────────────────────────────────────────
  function showTooltip(trigger) {
    clearTimeout(hideTimer);
    showTimer = setTimeout(() => {
      const text = trigger.dataset.tooltip;
      if (!text) return;
      const side = trigger.dataset.tooltipSide || 'top';

      box.textContent = text;
      // Force reflow so position calc uses correct size
      box.style.opacity = '0';
      box.style.display = 'inline-flex';

      positionTooltip(trigger, side);

      // Trigger animation
      requestAnimationFrame(() => {
        box.classList.add('tt-visible');
        arrow.classList.add('tt-visible');
      });
    }, DELAY_SHOW);
  }

  function hideTooltip() {
    clearTimeout(showTimer);
    hideTimer = setTimeout(() => {
      if (box) {
        box.classList.remove('tt-visible');
        arrow.classList.remove('tt-visible');
      }
    }, DELAY_HIDE);
  }

  // ── Bind events ─────────────────────────────────────────────────────────────
  function bindTrigger(el) {
    if (el._tooltipBound) return;
    el._tooltipBound = true;
    el.addEventListener('mouseenter', () => showTooltip(el));
    el.addEventListener('mouseleave', hideTooltip);
    el.addEventListener('focus',      () => showTooltip(el));
    el.addEventListener('blur',       hideTooltip);
    // Accessibility
    if (!el.hasAttribute('aria-label')) {
      el.setAttribute('aria-label', el.dataset.tooltip);
    }
  }

  // ── Public API ───────────────────────────────────────────────────────────────

  /**
   * initTooltips()
   * Scans the DOM for all [data-tooltip] elements and binds hover/focus events.
   * Safe to call multiple times (won't double-bind).
   */
  window.initTooltips = function () {
    createTooltipDOM();
    document.querySelectorAll('[data-tooltip]').forEach(bindTrigger);
  };

  /**
   * tooltipObserver()
   * Sets up a MutationObserver so dynamically-added elements (e.g., table rows)
   * also get tooltips automatically.
   */
  window.tooltipObserver = function () {
    initTooltips(); // initial scan
    const obs = new MutationObserver(() => {
      document.querySelectorAll('[data-tooltip]:not([_tooltipBound])').forEach(bindTrigger);
    });
    obs.observe(document.body, { childList: true, subtree: true });
  };

})();
