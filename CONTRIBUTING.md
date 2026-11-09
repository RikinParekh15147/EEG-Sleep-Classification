# Contributing to EEG Sleep Classification

Thank you for your interest in this project. We are two undergraduate students with a mentor, and we welcome help of any size: bug reports, documentation fixes, tests, or new ideas.

## Ways to contribute

- **Report a bug or unclear result** by opening an issue. Include what you ran, what you expected, and what happened.
- **Improve documentation**, such as setup steps, explanations of the pipeline, or typos.
- **Add or improve tests** for the refinement logic, architecture metrics, or reference-profile calculations.
- **Validate on other data.** Results on other datasets (for example Sleep-EDF) are especially valuable.
- **Work on the roadmap.** See [ROADMAP.md](ROADMAP.md) for planned work.

Look for issues labelled `good first issue` if you are new.

## Getting set up

- **Sleep Studio (GUI):** requires Node.js 22.12.0 or newer. From the repo root run `cd gui`, `npm install`, then `npm start`. Details are in `gui/README.md`.
- **Reproducing the experiment:** follow the "Reproduce the current experiment" section of the README. It needs Colab, Drive, and the HMC data supplied by you.

## Before opening a pull request

1. Open an issue first for large changes so we can agree on the approach.
2. Keep each pull request focused on one change.
3. From `gui/`, run `npm run build` and `npm test`, and run the Python tests with `python -m unittest discover -s tests -p "test_*.py"`.
4. If you change any model, feature, or metric, say which numbers change and why. Do not edit reported results by hand; regenerate them with `refinement_artifacts/reproduce.py`.
5. Never commit credentials, local app state, or raw dataset files.

## Research integrity rules

This project reports limitations openly, and we ask contributors to do the same.

- Keep the training-only rule: the N1/N2 refiner is fitted on training data only, and test routing uses predicted labels only.
- Keep recording-level splits disjoint across train, validation, and test.
- Describe reference profiles as descriptive, not diagnostic.
- State clearly whether a claim is implemented and evaluated, or only proposed.

## Data and licensing

Code is released under the license in `LICENSE`. The HMC Sleep Staging Database belongs to PhysioNet and keeps its own terms. Please follow them and do not upload raw recordings to this repository.

## Conduct

Be kind, assume good intent, and give feedback on the work, not the person. Harassment of any kind is not tolerated.

## Questions

Open an issue with the `question` label and we will do our best to reply.
