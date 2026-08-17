# RIV-UI-0023 — Dynamic Mermaid architecture rendering

Use this checkpoint when the first architecture view renders but subsequent
view selections show raw Mermaid source or stale SVG.

Each selection must render into a fresh container or use Mermaid's explicit
render API and replace the prior SVG. Generated view discovery comes from the
architecture projection; the UI must not assume a fixed view count. Raw `.mmd`
source is a Details surface only.

Recovery verification: select every discovered view repeatedly, confirm a
diagram rather than source text is visible, and retain a source fallback when
the pinned Mermaid runtime is unavailable.
