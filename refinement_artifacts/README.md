# Current N1/N2 refinement artifacts

Use `verified/` for the current model parameters, complete feature/reference tables, epoch predictions, profiles and plots. See `refinement_completion_audit.md` for results and validation, and `completion_manifest.json` for deliverable hashes.

`originals/` preserves the pre-update notebook, three decks, two original PDFs and documentation. `validation/` contains the first-party presentation validation receipts. `renders/` contains native PowerPoint slide previews, and `pdf_renders/` contains the PDF verification previews.

The small CSV/JSON tables directly in this folder were extracted from saved notebook displays for comparison. Some display tables contain `...` and are truncated. They are source evidence, not the complete current matrices. The complete CSV/JSON matrices are in `verified/`.

`reproduce.py` independently rebuilds the current experiment in Colab. `prepare_verified.py` checks the downloaded outputs against the notebook and desktop implementation. `build_decks.mjs` builds the three root presentations, `render_presentations.ps1` renders/exports them, and `finalize_audit.py` refreshes the text summaries and completion manifest. The reproduction only reads the original checkpoint and NPZ inputs. It saves an isolated output and a recovery bundle in the experiment's Drive folder.

Temporary ZIP downloads are excluded from Git. `reproduction_first.zip` belongs to an initial diagnostic run that omitted the notebook's second inference normalization. Its metrics and fitted classifier are not valid for the current experiment. `reproduction_verified.zip` contains the exact corrected reproduction; `plots_verified.zip` adds its verified plots.
