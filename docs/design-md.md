# DESIGN.md (optional, repos with a UI)

[DESIGN.md](https://github.com/google-labs-code/design.md) (Google Labs, Apache 2.0) describes a
visual identity for coding agents: design tokens in YAML front matter (colors, typography,
rounded, spacing, components) and the reasons for them in Markdown sections.

- A repo with a UI may keep `DESIGN.md` at its root. Repos without a UI do not need one.
- Where it exists, the `design-md` step of the `checks` job in `adlc.yml` runs
  `npx --yes @google/design.md@0.4.0 lint DESIGN.md`. The lint fails on errors (for example a
  token reference that does not resolve) and reports warnings such as text/background pairs
  below WCAG AA contrast (4.5:1). A failed lint shows a warning and never blocks a merge.
- The format is at version `alpha` and its authors expect changes, so the CLI version is pinned.
  Raise the pin in its own PR.
- Changes to `DESIGN.md` can be compared with `npx @google/design.md@0.4.0 diff OLD NEW`.
- Add `T2 DESIGN.md` (or higher) to `.adlc/tiers` if design changes need review.
