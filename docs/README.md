# Project manuscript

The initial LaTeX documentation uses the official **Springer Nature journal article template, version 3.1 (December 2024)** with the `sn-mathphys-num` numbered reference style. No target journal or conference has been selected. This is the journal template, rather than the separate Springer LNCS proceedings template.

Start with [main.tex](main.tex); the compiled reading copy is [main.pdf](main.pdf).

The reading copy uses **25 mm left/right/bottom text margins** and a **26 mm top text margin**. Set `\compactdraftfalse` in `main.tex` to restore Springer's default margins for venue-specific submission preparation; see [template notes](TEMPLATE.md#reading-copy-margins).

The draft includes the abstract, introduction, related work, data/splits, preprocessing, retained classifier, spectral refinement equations, recording measurements, reference profiles, verified results, software/reproduction workflow, limitations, planned extensions, and declarations. It uses existing evidence from **HMC-N1N2-20261007**. It does not rerun training or combine the older 3,773-epoch Soft-Viterbi experiment with the current 3,109-epoch experiment.

## Files

| File | Purpose |
| --- | --- |
| `main.tex` | Single-file manuscript, following the publisher's source organization |
| `references.bib` | Dataset, platform, and related-work citations |
| `sn-jnl.cls` | Unmodified publisher class |
| `sn-mathphys-num.bst` | Unmodified publisher bibliography style |
| `raw_confusion_matrix.png` | Copy of the verified baseline confusion matrix |
| `refined_confusion_matrix.png` | Copy of the verified refined confusion matrix |
| `hypnogram_SN009.png` | Copy of the verified example hypnogram |
| `build.ps1` | Windows build: pdfLaTeX, BibTeX, two pdfLaTeX passes |
| `verify_sources.py` | Check retained predictions, metrics, source figure copies, and citation keys |
| `SOURCES.md` | Claim-to-artifact map and evidence boundaries |
| `TEMPLATE.md` | Publisher download provenance and style notes |
| `ORIGINALITY.md` | Editorial attribution review and similarity-check limitations |
| `build/` | Ignored template download, validation output, and rendered review pages |

## Build locally

Install MiKTeX or TeX Live with pdfLaTeX and BibTeX. From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File docs/build.ps1
```

The script stops on a failed compiler pass and writes `docs/main.pdf`. MiKTeX may need permission to install missing standard LaTeX packages on first use. Auxiliary compiler files are ignored by Git.

The source verification uses only Python's standard library and does not need the checkpoint, raw data, or Colab:

```powershell
python docs/verify_sources.py
```

This recomputes classification metrics and prediction-change counts from the existing test CSV and checks them against the saved JSON and manuscript tables. It does not validate the original training run or clinical utility.

## Build in Overleaf

Upload the files in this folder's top level, including the class, bibliography style, bibliography, and three PNG figures. Exclude the ignored `build/` directory. Select `main.tex` as the main document and pdfLaTeX as the compiler. Keeping publication sources and figures together also avoids repository-relative paths in the manuscript.

## Next editorial work

- Confirm the target venue and its required bibliography style and article structure.
- Confirm author order, corresponding author, contact details, and whether the mentor should be a coauthor. Current team members follow the README order; the mentor is acknowledged pending review.
- Complete contribution, funding, competing-interest, ethics, and archival code-availability statements from author-supplied information.
- Expand the literature review with verified sources appropriate to the selected venue.
- Add recording-level uncertainty estimates and derived-measurement error analysis only when those analyses exist; do not infer them from aggregate epoch metrics.
- Preserve qualifications about the four-recording test cohort, partial SN001, unverified continuity, and descriptive clinical-cohort reference profiles.

Existing proposals, audits, and extracted slide text in `docs/` are preserved.
