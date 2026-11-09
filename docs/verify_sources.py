"""Verify manuscript evidence from retained files; Python standard library only."""
import csv
import hashlib
import json
import math
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parent
SOURCE = DOCS.parent / 'refinement_artifacts' / 'verified'


def load_json(name):
    return json.loads((SOURCE / name).read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    final = load_json('final_results.json')
    with (SOURCE / 'test_epoch_predictions.csv').open(newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    require(len(rows) == final['raw_metrics']['test_epochs'] == 3109, 'Test epoch count mismatch')
    require({row['subject_id'] for row in rows} == set(final['split']['test_subjects']), 'Test IDs mismatch')
    changes = dict(unchanged=0, corrected=0, degraded=0, wrong_to_wrong=0, changed=0)
    metrics = {}
    manuscript = (DOCS / 'main.tex').read_text(encoding='utf-8')
    for method, column in [('raw', 'raw_prediction'), ('refined', 'refined_prediction')]:
        cm = [[0] * 5 for _ in range(5)]
        for row in rows:
            cm[int(row['true_label'])][int(row[column])] += 1
        accuracy = sum(cm[k][k] for k in range(5)) / len(rows)
        f1 = []
        for k in range(5):
            support = sum(cm[k])
            predicted = sum(cm[j][k] for j in range(5))
            f1.append(2 * cm[k][k] / (support + predicted) if support + predicted else 0)
        macro_f1 = sum(f1) / 5
        expected = final[method + '_metrics']
        for key, value in [('accuracy', accuracy), ('macro_f1', macro_f1)]:
            require(math.isclose(value, expected[key], abs_tol=1e-12), f'{method} {key} mismatch')
            require(f'{value * 100:.2f}' in manuscript, f'Missing manuscript {method} {key}')
        for value in f1:
            require(f'{value * 100:.2f}' in manuscript, 'Missing per-stage F1 in manuscript')
        metrics[method] = {'accuracy': accuracy, 'macro_f1': macro_f1, 'class_f1': f1}
    for row in rows:
        truth, raw, refined = (int(row[k]) for k in ['true_label', 'raw_prediction', 'refined_prediction'])
        if raw == refined:
            changes['unchanged'] += 1
        else:
            changes['changed'] += 1
            category = 'corrected' if refined == truth else 'degraded' if raw == truth else 'wrong_to_wrong'
            changes[category] += 1
        require(raw in (1, 2) or raw == refined, 'Refiner changed a bypassed prediction')
        require(raw == refined or refined in (1, 2), 'Refiner emitted an invalid target')
    require(changes == final['changes'], 'Prediction-change counts mismatch')
    require(changes['corrected'] - changes['degraded'] == 121, 'Net gain mismatch')
    figures = {}
    for name in ['raw_confusion_matrix.png', 'refined_confusion_matrix.png', 'hypnogram_SN009.png']:
        digest = hashlib.sha256((DOCS / name).read_bytes()).hexdigest()
        require(digest == hashlib.sha256((SOURCE / name).read_bytes()).hexdigest(), f'Figure differs: {name}')
        figures[name] = digest
    bibliography = (DOCS / 'references.bib').read_text(encoding='utf-8')
    keys = set(re.findall(r'@\w+\{([^,]+),', bibliography))
    citations = {key.strip() for group in re.findall(r'\\cite\{([^}]+)\}', manuscript) for key in group.split(',')}
    require(citations <= keys, f'Missing bibliography entries: {citations - keys}')
    for asset in re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}', manuscript):
        require((DOCS / asset).is_file(), f'Missing figure: {asset}')
    report = {'run_id': final['run_id'], 'test_epochs': len(rows), 'metrics': metrics,
              'changes': changes, 'figure_sha256': figures, 'citation_keys': sorted(citations),
              'scope': 'Retained evidence consistency; no model execution or clinical validation', 'status': 'passed'}
    (DOCS / 'build').mkdir(exist_ok=True)
    (DOCS / 'build' / 'artifact_validation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS: 3,109 predictions, metrics, routing, change counts, figure copies, and citation keys.')


if __name__ == '__main__':
    main()
