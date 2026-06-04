/* ============================================
   UTILS.JS — Vanilla JS Utility Library
   Converted from SupplyWise: apps/web/src/lib/utils.ts

   Original source:
     import { clsx } from "clsx"
     import { twMerge } from "tailwind-merge"
     export function cn(...inputs: ClassValue[]) {
       return twMerge(clsx(inputs))
     }

   This file provides:
     1.  cn()          — clsx + twMerge equivalent (core conversion)
     2.  clsx()        — conditional class joining
     3.  twMerge()     — Tailwind class deduplication (lightweight)
     4.  Companion helpers used across RealEstate pages
   ============================================ */

'use strict';

/* ─────────────────────────────────────────────────────────────────────────────
   1. clsx() — Conditional class joining
      Mirrors the npm `clsx` package behaviour exactly.
      Accepts: strings, arrays, objects {className: boolean}, falsy values.

   Examples:
     clsx('foo', null, 'bar')              → 'foo bar'
     clsx('a', { b: true, c: false })     → 'a b'
     clsx(['x', ['y', { z: true }]])      → 'x y z'
───────────────────────────────────────────────────────────────────────────── */
function clsx(...args) {
  const classes = [];

  function process(arg) {
    if (!arg) return;                            // null, undefined, false, 0, ''
    if (typeof arg === 'string' || typeof arg === 'number') {
      classes.push(String(arg));
    } else if (Array.isArray(arg)) {
      arg.forEach(process);
    } else if (typeof arg === 'object') {
      for (const key in arg) {
        if (Object.prototype.hasOwnProperty.call(arg, key) && arg[key]) {
          classes.push(key);
        }
      }
    }
  }

  args.forEach(process);
  return classes.join(' ');
}

/* ─────────────────────────────────────────────────────────────────────────────
   2. twMerge() — Lightweight Tailwind class deduplication
      Mirrors the core behaviour of the npm `tailwind-merge` package.
      When two classes target the same CSS property (e.g. px-2 and px-4),
      the LAST one wins — just like the real twMerge.

   Supports deduplication for the most common Tailwind utility groups:
     layout, spacing, sizing, typography, colors, borders, flex/grid,
     effects, transitions, and arbitrary values.

   Examples:
     twMerge('px-2 px-4')          → 'px-4'
     twMerge('text-red-500 text-blue-500') → 'text-blue-500'
     twMerge('font-bold font-normal')      → 'font-normal'
───────────────────────────────────────────────────────────────────────────── */
function twMerge(...classLists) {
  // Flatten all arguments into a single space-separated class string
  const allClasses = classLists
    .flatMap(c => (typeof c === 'string' ? c.split(/\s+/) : []))
    .filter(Boolean);

  // Map of "group key" → "last winning class"
  const grouped = new Map();
  const unGrouped = [];

  // Determine a group key for a class. Returns null if class is not in a known group.
  function getGroupKey(cls) {
    // Handle responsive / state prefixes (e.g. "hover:", "md:", "dark:")
    const prefixMatch = cls.match(/^([a-z]+(?:\[[^\]]+\])?:)+/);
    const prefix = prefixMatch ? prefixMatch[0] : '';
    const base = cls.slice(prefix.length);

    // Negative modifier
    const neg = base.startsWith('-') ? '-' : '';
    const bare = neg ? base.slice(1) : base;

    // Groups: each entry is [regex, groupName]
    const groups = [
      // Spacing — padding
      [/^p-/, 'p'], [/^px-/, 'px'], [/^py-/, 'py'],
      [/^pt-/, 'pt'], [/^pr-/, 'pr'], [/^pb-/, 'pb'], [/^pl-/, 'pl'],
      [/^ps-/, 'ps'], [/^pe-/, 'pe'],
      // Spacing — margin
      [/^m-/, 'm'], [/^mx-/, 'mx'], [/^my-/, 'my'],
      [/^mt-/, 'mt'], [/^mr-/, 'mr'], [/^mb-/, 'mb'], [/^ml-/, 'ml'],
      [/^ms-/, 'ms'], [/^me-/, 'me'],
      // Sizing
      [/^w-/, 'w'], [/^min-w-/, 'min-w'], [/^max-w-/, 'max-w'],
      [/^h-/, 'h'], [/^min-h-/, 'min-h'], [/^max-h-/, 'max-h'],
      [/^size-/, 'size'],
      // Typography
      [/^text-(?:xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|8xl|9xl|\[)/, 'text-size'],
      [/^text-(?!xs|sm|base|lg|xl|\d)/, 'text-color'],
      [/^font-(?:thin|extralight|light|normal|medium|semibold|bold|extrabold|black)$/, 'font-weight'],
      [/^font-(?:sans|serif|mono)$/, 'font-family'],
      [/^leading-/, 'leading'],
      [/^tracking-/, 'tracking'],
      [/^line-clamp-/, 'line-clamp'],
      // Colors — background
      [/^bg-/, 'bg'],
      // Colors — border
      [/^border-(?!t-|r-|b-|l-|x-|y-|s-|e-|opacity)([a-z])/, 'border-color'],
      // Border width
      [/^border-(?:t|r|b|l|x|y|s|e)?$|^border-\d/, 'border-width'],
      [/^border(?:-(?:t|r|b|l|x|y|s|e))?-\d/, 'border-width'],
      // Border radius
      [/^rounded(?:-(?:none|sm|md|lg|xl|2xl|3xl|full|\[))?$/, 'rounded'],
      [/^rounded-[trlbse]/, 'rounded-side'],
      // Border style
      [/^border-(?:solid|dashed|dotted|double|hidden|none)$/, 'border-style'],
      // Flex
      [/^flex-(?:row|col|row-reverse|col-reverse)$/, 'flex-direction'],
      [/^flex-(?:wrap|nowrap|wrap-reverse)$/, 'flex-wrap'],
      [/^flex-(?:\d|auto|initial|none|\[)/, 'flex'],
      [/^grow(?:-\d)?$/, 'grow'], [/^shrink(?:-\d)?$/, 'shrink'],
      [/^basis-/, 'basis'],
      [/^justify-/, 'justify'],
      [/^items-/, 'items'],
      [/^self-/, 'self'],
      [/^content-/, 'content'],
      [/^gap-/, 'gap'], [/^gap-x-/, 'gap-x'], [/^gap-y-/, 'gap-y'],
      // Grid
      [/^grid-cols-/, 'grid-cols'], [/^grid-rows-/, 'grid-rows'],
      [/^col-span-/, 'col-span'], [/^row-span-/, 'row-span'],
      // Display
      [/^(?:block|inline-block|inline|flex|inline-flex|grid|inline-grid|hidden|table|contents)$/, 'display'],
      // Position
      [/^(?:static|fixed|absolute|relative|sticky)$/, 'position'],
      [/^(?:top|right|bottom|left|inset(?:-x|-y)?)-/, 'inset'],
      // Z-index
      [/^z-/, 'z'],
      // Overflow
      [/^overflow(?:-x|-y)?-/, 'overflow'],
      // Opacity
      [/^opacity-/, 'opacity'],
      // Shadow
      [/^shadow(?:-(?:sm|md|lg|xl|2xl|inner|none|\[))?$/, 'shadow'],
      // Ring
      [/^ring(?:-(?:\d|offset|color|opacity|\[))?/, 'ring'],
      // Transition / Animation
      [/^transition(?:-(?:none|all|colors|opacity|shadow|transform|\[))?$/, 'transition'],
      [/^duration-/, 'duration'],
      [/^ease-/, 'ease'],
      [/^delay-/, 'delay'],
      [/^animate-/, 'animate'],
      // Transform
      [/^scale-/, 'scale'], [/^rotate-/, 'rotate'],
      [/^translate-x-/, 'translate-x'], [/^translate-y-/, 'translate-y'],
      [/^skew-x-/, 'skew-x'], [/^skew-y-/, 'skew-y'],
      // Cursor
      [/^cursor-/, 'cursor'],
      // Pointer events
      [/^pointer-events-/, 'pointer-events'],
      // User select
      [/^select-/, 'select'],
      // Object fit / position
      [/^object-(?:contain|cover|fill|none|scale-down)$/, 'object-fit'],
      [/^object-(?:bottom|center|left|right|top)$/, 'object-position'],
      // Aspect ratio
      [/^aspect-/, 'aspect'],
      // Columns
      [/^columns-/, 'columns'],
    ];

    for (const [regex, group] of groups) {
      if (regex.test(bare)) {
        return prefix + neg + group; // unique key per prefix+group
      }
    }
    return null; // not in a known group → keep as-is
  }

  for (const cls of allClasses) {
    const key = getGroupKey(cls);
    if (key !== null) {
      grouped.set(key, cls); // last one wins
    } else {
      // Deduplicate exact duplicates in ungrouped set
      if (!unGrouped.includes(cls)) unGrouped.push(cls);
    }
  }

  return [...grouped.values(), ...unGrouped].join(' ');
}

/* ─────────────────────────────────────────────────────────────────────────────
   3. cn() — The core conversion from SupplyWise utils.ts
      Combines clsx() (conditional joining) + twMerge() (deduplication).
      Drop-in equivalent of:
        import { cn } from "@/lib/utils"

   Examples:
     cn('px-2', 'px-4')                        → 'px-4'
     cn('btn', isActive && 'btn-active')        → 'btn btn-active'
     cn('text-red-500', { 'text-blue-500': true }) → 'text-blue-500'
     cn('flex gap-2', props.className)          → merged result
───────────────────────────────────────────────────────────────────────────── */
function cn(...inputs) {
  return twMerge(clsx(...inputs));
}

/* ─────────────────────────────────────────────────────────────────────────────
   4. Companion Utility Helpers
      These complement cn() and fill gaps in the RealEstate codebase.
───────────────────────────────────────────────────────────────────────────── */

/**
 * formatCurrency(price)
 * Formats a number as Indian Rupees with lakh/crore suffix.
 * Mirrors the existing formatCurrency() in script.js but available here
 * as a standalone import-style utility.
 *
 * @param {number} price
 * @returns {string}  e.g. "₹45.5L", "₹1.2Cr", "₹95,000"
 */
function formatCurrency(price) {
  if (!price && price !== 0) return '₹0';
  const n = parseFloat(price);
  if (n >= 1e7)  return `₹${(n / 1e7).toFixed(2).replace(/\.?0+$/, '')}Cr`;
  if (n >= 1e5)  return `₹${(n / 1e5).toFixed(1).replace(/\.?0+$/, '')}L`;
  return `₹${n.toLocaleString('en-IN')}`;
}

/**
 * slugify(str)
 * Converts a string to a URL-safe lowercase slug.
 *
 * @param {string} str
 * @returns {string}  e.g. "My Villa 2BHK" → "my-villa-2bhk"
 */
function slugify(str) {
  return String(str)
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

/**
 * truncate(str, maxLen, suffix)
 * Truncates a string to maxLen characters, appending suffix if trimmed.
 *
 * @param {string} str
 * @param {number} maxLen  default 80
 * @param {string} suffix  default '…'
 * @returns {string}
 */
function truncate(str, maxLen = 80, suffix = '…') {
  if (!str) return '';
  const s = String(str);
  return s.length <= maxLen ? s : s.slice(0, maxLen - suffix.length) + suffix;
}

/**
 * debounce(fn, wait)
 * Returns a debounced version of fn that fires after `wait` ms of silence.
 * Useful for search inputs, resize handlers etc.
 *
 * @param {Function} fn
 * @param {number}   wait  ms, default 300
 * @returns {Function}
 */
function debounce(fn, wait = 300) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), wait);
  };
}

/**
 * pick(obj, keys)
 * Returns a new object containing only the specified keys.
 *
 * @param {Object}   obj
 * @param {string[]} keys
 * @returns {Object}
 */
function pick(obj, keys) {
  const result = {};
  for (const k of keys) {
    if (Object.prototype.hasOwnProperty.call(obj, k)) result[k] = obj[k];
  }
  return result;
}

/**
 * omit(obj, keys)
 * Returns a new object with the specified keys removed.
 *
 * @param {Object}   obj
 * @param {string[]} keys
 * @returns {Object}
 */
function omit(obj, keys) {
  const result = { ...obj };
  for (const k of keys) delete result[k];
  return result;
}

/**
 * isNullish(value)
 * Returns true if value is null or undefined (not 0, '', false).
 * Mirrors TypeScript's nullish-coalescing guard.
 *
 * @param {*} value
 * @returns {boolean}
 */
function isNullish(value) {
  return value === null || value === undefined;
}

/**
 * copyToClipboard(text)
 * Copies text to the clipboard. Returns a Promise<boolean>.
 * Gracefully falls back to execCommand for older browsers.
 *
 * @param {string} text
 * @returns {Promise<boolean>}
 */
async function copyToClipboard(text) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
    // Fallback
    const el = document.createElement('textarea');
    el.value = text;
    el.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0';
    document.body.appendChild(el);
    el.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(el);
    return ok;
  } catch {
    return false;
  }
}

/**
 * getQueryParam(key)
 * Reads a URL query parameter value by key.
 *
 * @param {string} key
 * @returns {string|null}
 */
function getQueryParam(key) {
  return new URLSearchParams(window.location.search).get(key);
}

/**
 * cx(base, variants, props)
 * Variant-aware class builder — a lightweight CVA (class-variance-authority)
 * equivalent. Useful for building component-level class APIs.
 *
 * @param {string}   base       Base classes always applied
 * @param {Object}   variants   Map of variant name → { value → classes }
 * @param {Object}   props      Selected variant values
 * @returns {string}
 *
 * Example:
 *   const btnClass = cx(
 *     'btn',
 *     { size: { sm: 'btn-sm', lg: 'btn-lg' }, intent: { danger: 'btn-danger' } },
 *     { size: 'sm', intent: 'danger' }
 *   );
 *   // → 'btn btn-sm btn-danger'
 */
function cx(base, variants = {}, props = {}) {
  const parts = [base];
  for (const [key, map] of Object.entries(variants)) {
    const chosen = props[key];
    if (chosen && map[chosen]) parts.push(map[chosen]);
  }
  return cn(...parts);
}

/* ─────────────────────────────────────────────────────────────────────────────
   Exports — attach everything to window so any page can use them
   (No ES module system needed — works with plain <script src="utils.js">)
───────────────────────────────────────────────────────────────────────────── */
Object.assign(window, {
  // Core (from SupplyWise utils.ts)
  cn,
  clsx,
  twMerge,

  // Companion helpers
  formatCurrency: window.formatCurrency || formatCurrency, // don't override script.js if already defined
  slugify,
  truncate,
  debounce,
  pick,
  omit,
  isNullish,
  copyToClipboard,
  getQueryParam,
  cx,
});
