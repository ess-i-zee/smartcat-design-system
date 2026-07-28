export const meta = {
  name: 'review-preview-redesign',
  description: 'Adversarially-verified multi-dimension review of the redesigned page-level components preview',
  phases: [
    { title: 'Review', detail: 'parallel dimension reviews of preview-page-level-components.html' },
    { title: 'Verify', detail: '3-skeptic adversarial refute pass on each finding' },
  ],
}

const REPO = 'C:/Users/isizo/Dropbox/Marketing/01 Brand/00-claude-design-system'
const FILE = REPO + '/preview/preview-page-level-components.html'

const CONTEXT = `Repo: ${REPO} (Smartcat website design system, static HTML/CSS/JS, no build step, no framework).
File under review: ${FILE}.
This file was just redesigned: the "controls" (properties) panel for all 14 page-level component preview sections was converted from custom .dsp-chip button groups + grouped .dsp-field labels into the design system's real .select component (via a new shared bindSelect() JS helper), rows were flattened (no group headers), toggle "on" color was changed from --background-interaction-selectedbrand to --background-interaction-selectedstrong, section spacing was increased (--spacing-8 gaps replacing --spacing-3), and a JS syncPanelHeights() pass was added so the code panel matches the properties panel's height (224px floor, no growth from code content). .dsp-props-code was switched from align-items:stretch to align-items:flex-start specifically to break a circular flex-height bug that was found and fixed during implementation (a long code snippet was inflating both panels).
Read CLAUDE.md in the repo root first for the design system's rules (tokens-only CSS, component tiers, Figma property mapping, etc.) before judging compliance.
Read components/atomic/select/select.css and components/atomic/select/select.js for the canonical Select component behavior being reused.`

const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          file: { type: 'string' },
          line: { type: 'number' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          description: { type: 'string' },
          repro: { type: 'string' },
        },
        required: ['title', 'file', 'description'],
      },
    },
  },
  required: ['findings'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean' },
    reasoning: { type: 'string' },
  },
  required: ['refuted', 'reasoning'],
}

const DIMENSIONS = [
  {
    key: 'tokens-css',
    prompt: `${CONTEXT}

Review dimension: Design-system CSS/token compliance. Check every CSS rule changed or added in the "Component playground" style block (.dsp-controls, .dsp-code, .dsp-toggle, .dsp-toggle__label, .dsp-switch, .dsp-props-code, .dsp-section__head, .dsp-preview) against CLAUDE.md's rules: tokens-only CSS (no raw px/colors, except where this file's pre-existing "dsp-" chrome convention already used raw px, e.g. .dsp-nav width), semantic-over-primitive tokens, dark theme via [data-theme="dark"]. Flag any raw value that should be a token, any token misuse, or any rule violation. Report findings with file/line/severity/description.`,
  },
  {
    key: 'js-correctness',
    prompt: `${CONTEXT}

Review dimension: JS correctness. Read the shared <script> block's bindSelect(), wireChips(), wireViewport(), and syncPanelHeights() functions plus their ~28+14 call sites. Check for: event listener leaks or duplicate bindings, outside-click handling edge cases, whether open/select/close works correctly for every one of the 14 sections' selects, whether syncPanelHeights correctly handles window resize crossing the 880px breakpoint, and whether removing the old 10-line-collapse code left any dangling references (in CSS, JS, or markup) to classes/functions that no longer exist (e.g. .dsp-code__expand, .dsp-code__fade, is-collapsible, is-expanded, dsp-code-bg). Report findings with file/line/severity/description.`,
  },
  {
    key: 'a11y',
    prompt: `${CONTEXT}

Review dimension: Accessibility. The old .dsp-chip groups were real <button> elements (natively keyboard-focusable, clickable via Enter/Space). The new .select rows are plain <div class="select"> elements per components/atomic/select/select.html's reference markup. Check whether these preview-page controls are keyboard operable (tab order, Enter/Space to open, Escape to close, arrow-key navigation within the dropdown) by reading select.js/select.css for any keyboard handling, and check the actual markup in preview/preview-page-level-components.html for missing ARIA attributes (role, aria-expanded, aria-haspopup) a real combobox would need. Report findings with file/line/severity/description — note this is an internal preview/tooling page, not production marketing content, when judging severity.`,
  },
  {
    key: 'responsive',
    prompt: `${CONTEXT}

Review dimension: Responsive/breakpoint behavior. Check the @media (max-width: 880px) stacking rule for .dsp-props-code, how .dsp-controls' fixed "flex: 0 0 420px" width behaves as viewport width shrinks toward 880px (does the code panel get squeezed to near-zero before the stacking breakpoint kicks in?), and whether the select's fixed 200px width (.dsp-toggle .select) could overflow or wrap awkwardly at narrow widths just above 880px. Report findings with file/line/severity/description.`,
  },
  {
    key: 'figma-fidelity',
    prompt: `${CONTEXT}

Review dimension: fidelity to 6 specific corrections the user gave after the first implementation pass:
(1) toggle "on" track color must be --background-interaction-selectedstrong, not --background-interaction-selectedbrand;
(2) row gap between properties is 18px;
(3) row label is 14px / regular weight / --content-static-primary color;
(4) enum pickers use the Select component's "Complete" state (value shown, no placeholder, no clear button);
(5) section gaps (heading→preview, preview→controls+code) are --spacing-8 (40px);
(6) properties panel hugs its content with a 224px floor, code panel matches it exactly and never grows taller from code length alone.
Verify each of these 6 points is actually implemented correctly across ALL 14 sections, not just hero-block — spot check at least 4 other sections' markup (e.g. cards, faq, numbers, cta) for consistency, since all sections should share the same CSS classes. Report any section/point that doesn't hold, with file/line/severity/description.`,
  },
]

const results = await pipeline(
  DIMENSIONS,
  d => agent(d.prompt, { label: `review:${d.key}`, phase: 'Review', schema: FINDINGS_SCHEMA }),
  (review, dim) => parallel((review?.findings || []).map(f => () =>
    parallel([1, 2, 3].map(() => () =>
      agent(
        `A reviewer (dimension: ${dim.key}) flagged this issue in the Smartcat design system repo (${REPO}):

Title: ${f.title}
File: ${f.file}${f.line ? ':' + f.line : ''}
Description: ${f.description}
${f.repro ? 'Repro: ' + f.repro : ''}

Your job: try to REFUTE this finding. Read the actual file/line yourself and check whether the claim holds up against the real code. Default to refuted=true if you are uncertain or cannot independently verify the specific claim.`,
        { label: `verify:${dim.key}`, phase: 'Verify', schema: VERDICT_SCHEMA }
      )
    )).then(verdicts => {
      const survivors = verdicts.filter(Boolean).filter(v => !v.refuted).length
      return { ...f, dimension: dim.key, confirmed: survivors >= 2 }
    })
  ))
)

const allFindings = results.flat().filter(Boolean)
const confirmed = allFindings.filter(f => f.confirmed)
log(`${confirmed.length} confirmed / ${allFindings.length} total findings across ${DIMENSIONS.length} dimensions`)
return { confirmed, totalFindings: allFindings.length, refutedCount: allFindings.length - confirmed.length }
