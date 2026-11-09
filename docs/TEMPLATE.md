# Springer template provenance

The manuscript uses the official Springer Nature journal authoring template, **version 3.1, December 2024**, downloaded on 2026-10-26.

- Publisher entry point: [LaTeX author support](https://www.springernature.com/gp/authors/campaigns/latex-author-support).
- Download endpoint: <https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/18782940/data/v12>.
- Archive SHA-256: `812e76dcaa9c28dc1bff1fb6065d51729b67d4ea140552a05088317414a3ecae`.
- `sn-jnl.cls` SHA-256: `36d0c3273a59d48dc6a9c7b080dfa1ec50dc10229d8751568d1f2e490ffa5ecc`.
- `sn-mathphys-num.bst` SHA-256: `b3a7c7fbcc1e7f9619de634fcea2f5bb7a245818a5942bc576e40ea001633332`.

The class and selected bibliography style are copied without modification from the publisher archive. Their embedded copyright and license notices are retained. The downloaded archive and full extracted examples/manual are local intermediates under ignored `build/`.

The project manuscript uses `\documentclass[pdflatex,sn-mathphys-num]{sn-jnl}`, a single manuscript `.tex` file, standard fonts, and minimal additional packages. Figures are copied to the same folder for portable compilation. This draft makes no claim of journal acceptance or compliance with an unspecified venue's additional instructions.

## Reading-copy margins

At the user's request, `main.tex` sets the left, right, and bottom text margins to **25 mm**, keeps the top text margin at **26 mm**, and removes the 6 mm binding offset for this project reading copy. The class's default single-column text width is 31 pc (approximately 130.75 mm on 210 mm A4 paper); the reading copy uses 160 mm. The default text block left about 77 mm below the body text; the draft now uses a 246 mm text height. The footer sits 10 mm below the text block, leaving approximately 15 mm to the paper edge. Float placement and the final page can still leave some unfilled space.

This is an explicit draft-layout override, not a claim that a particular journal permits altered submission margins. Replace `\compactdrafttrue` with `\compactdraftfalse` in `main.tex` to restore the unmodified publisher geometry before applying the chosen venue's requirements. The class and bibliography style themselves remain unmodified.

If the chosen venue is a Springer conference using LNCS, switch to its official `llncs` proceedings template after the venue is confirmed. Do not describe `sn-jnl` as LNCS.
