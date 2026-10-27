---
name: vue-component-analyzer
description: Analyze Vue 3 components in client/src for performance problems, duplicated or reusable logic, violations of this project's conventions (client/CLAUDE.md), and accessibility gaps, then report prioritized findings with file:line and a suggested fix. Report-only — never edits code. Use when asked to analyze, audit, or suggest optimizations for a .vue file, a view, or the whole frontend.
---

# Vue Component Analyzer

Produce a prioritized, evidence-backed report on one or more Vue 3 components. **Do not modify any files**; the output is a report the user can act on (or hand to the vue-expert subagent).

## 1. Scope

- If the user names files or views, report findings only for those. Child components they render (e.g. a view's modals) are out of scope unless the user asks; mention them in one line if they look problematic.
- Otherwise analyze `client/src/views/*.vue` and `client/src/components/*.vue`. For more than ~5 files, fan out: one Explore subagent per group of files, each returning findings in the format below, then merge and de-duplicate. Skip the fan-out if you are already running as a subagent, lack the Agent tool, or were told not to spawn agents — analyze sequentially instead.
- Reading vs searching: read the in-scope files in full; you may `grep` the whole of `client/src` to confirm duplication or find an existing helper (section 4).
- Read `client/CLAUDE.md` and the root `CLAUDE.md` first. Where they give generic examples that conflict with section 3 (e.g. `toLocaleString('en-US', { currency: 'USD' })` for money, `console.log` for debugging), **section 3 wins** — it reflects how this app actually works (i18n with USD→JPY conversion, no debug logging in shipped code).
- Skim `client/src/App.vue` (global styles), `client/src/api.js`, `client/src/composables/` and `client/src/utils/` so you can recognise when a component re-implements something that already exists.

## 2. Performance

Flag only issues with a real cost:

- Work in the template or in methods called from the template that should be a `computed` (sorting, filtering, aggregation, `Math.max(...list)` per row, lookups into other arrays by index).
- Nested loops over the same data (O(n²)), e.g. `find`/`filter` inside `v-for` over a large list — suggest a `Map` built in a computed.
- `watch` that triggers duplicate API calls (watching several refs that change together, missing debounce on slider/search input, missing stale-response guard when requests can overlap).
- Sequential `await`s of independent requests — suggest `Promise.all`.
- Large lists rendered without need, `v-if` vs `v-show` misuse on frequently toggled UI, `deep: true` watchers on big objects.
- Timers/listeners added in `onMounted` without cleanup in `onBeforeUnmount`.

## 3. Project conventions (client/CLAUDE.md)

Each is a finding when violated:

- Composition API with `setup()` returning bindings (no Options API `data`/`methods`/`mounted`, no mixing).
- `v-for` keys are stable ids (`sku`, `id`, `month`), never `index`.
- All user-visible text goes through `t()` from `useI18n`; new keys exist in **both** `locales/en.js` and `locales/ja.js`.
- Money uses `formatCurrency`/`formatCurrencyWithDecimals` from `utils/currency.js` with the current currency — not `'$' + value`, not raw `toLocaleString()` on USD values in a JPY locale.
- HTTP goes through `api.js`, not `axios`/`fetch` directly with hard-coded URLs.
- Loading/error pattern: `loading` + `error` refs, `error.value = null` at the start of each load, `try/catch/finally`, template shows loading → error → content.
- Views that show order/inventory data react to the global filter bar via `useFilters()` + `watch`.
- Dates validated before `.getMonth()` etc.; month/date labels formatted with the active locale.
- No `console.log` left in shipped code (`console.error` in catch blocks is fine).
- No emojis in UI text; styling reuses global classes from `App.vue` (`card`, `stat-card`, `badge`, `table-container`) rather than scoped copies.

## 4. Reuse and duplication

- Logic repeated across components (date formatting, status-to-class maps, currency symbol handling, filter-param building) → suggest moving it to `composables/` or `utils/`, naming the existing helper if one already exists.
- Components over ~300 lines of template or with several unrelated responsibilities → suggest a split and name the pieces.
- Scoped CSS that duplicates global classes, or selectors that are defined but never used.

## 5. Accessibility

- Form controls without an associated `<label>` / `aria-label`; icon-only buttons without an accessible name.
- Clickable `div`/`tr`/`span` with `@click` but no `role`, `tabindex`, or keyboard handler — suggest a `<button>` or add keyboard support.
- Modals: no `role="dialog"`/`aria-modal`, no focus moved into the dialog on open, no Escape-to-close, focus not restored on close.
- Status conveyed by colour alone (badges without text), insufficient contrast against the slate palette.

## 6. Verify before reporting

For every candidate finding, re-read the exact lines and confirm it is real in the current file. Drop anything speculative, stylistic-only, or already handled elsewhere (e.g. a "missing error reset" that actually happens in a called helper). Prefer fewer, high-confidence findings over a long list.

- **Check data assumptions against real data.** Hard-coded scales, thresholds or axis labels (e.g. a chart max of `25000`) can only be judged against actual values — look up the ranges in `server/data/*.json` (or call the API on `http://localhost:8001` if it is running) and quote them in the finding.
- **Possibly intentional behaviour** (e.g. a page that deliberately ignores some filters): report it as Low with "confirm intent" instead of calling it a bug, unless the UI clearly implies otherwise.

## 7. Report format

Write the report in the language the user is using (identifiers, paths and code stay as-is). When the same problem appears in several places or files, use **one row** listing every location rather than repeating it.

Start with a one-line summary (files analyzed, number of findings per severity). Then a table per severity, most severe first:

| # | Category | Location | Problem | Suggested fix |
|---|----------|----------|---------|---------------|
| 1 | Performance | `client/src/views/Reports.vue:88` | `getBarHeight` recomputes `Math.max` over all months for every bar (O(n²)) | Compute `maxRevenue` once in a `computed` and reuse it |

Severities:
- **High** — user-visible bug or significant slowdown (wrong data, broken i18n, duplicate requests, memory leak).
- **Medium** — convention violation or maintainability problem likely to cause bugs.
- **Low** — cleanup and polish (dead CSS, minor duplication, small a11y gaps).

Accessibility severity: if the **only** way to reach a feature is mouse-only (e.g. a modal that opens solely from a clickable `div`), that is Medium, not Low.

Finish with "Quick wins" (up to 3 fixes with the best effort/impact ratio). Remind the user that fixes to `.vue` files should be delegated to the `vue-expert` subagent per the root CLAUDE.md.
