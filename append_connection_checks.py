"""Append diagnostic cells, preserving every original cell and its outputs."""
import ast
import copy
import hashlib
import json
from pathlib import Path

path = Path('Original_Prev_MP_HMC_FINAL_edit.ipynb')
backup = path.with_suffix('.before_connection_checks.ipynb')
original_bytes = path.read_bytes()
original = json.loads(original_bytes)
notebook = copy.deepcopy(original)
marker = 'eeg-colab-drive-checks-v1'
if any(c.get('metadata', {}).get('connection_checks') == marker for c in notebook['cells']):
    raise SystemExit('Checks already appended; no changes made.')

mount = """def _eeg_connection_mount_check():
    from google.colab import drive
    from pathlib import Path
    drive.mount('/content/drive', force_remount=False)
    if not Path('/content/drive/MyDrive').is_dir():
        raise RuntimeError('Drive mount did not expose MyDrive.')
    print('Drive mount: PASS')

try:
    _eeg_connection_mount_check()
finally:
    del _eeg_connection_mount_check
"""
runtime = """def _eeg_connection_runtime_check():
    import platform
    import shutil
    import subprocess
    from importlib.metadata import version, PackageNotFoundError
    print('Python:', platform.python_version())
    print('Runtime:', platform.platform())
    for package in ('numpy', 'pandas', 'mne', 'pyedflib', 'scikit-learn', 'tensorflow', 'torch'):
        try:
            print(package + ':', version(package))
        except PackageNotFoundError:
            print(package + ': not installed')
    if shutil.which('nvidia-smi'):
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
            capture_output=True, text=True, timeout=20)
        print('GPU:', (result.stdout or result.stderr).strip())
    else:
        print('GPU: nvidia-smi unavailable; CPU checks can still run.')

try:
    _eeg_connection_runtime_check()
finally:
    del _eeg_connection_runtime_check
"""
dataset = """def _eeg_connection_dataset_check():
    from pathlib import Path
    roots = (
        Path('/content/drive/MyDrive/Sleep_Health_Profiling/processed/HMC_preprocessed'),
        Path('/content/drive/MyDrive/HMC_preprocessed'),
        Path('/content/drive/MyDrive/Sleep_Health_Profiling/Data/HMC'),
        Path('/content/drive/MyDrive/MAJOR PROJECT HMC/haaglanden-medisch-centrum-sleep-staging-database-1.1/recordings'),
    )
    reads = 0
    for folder in roots:
        try:
            if not folder.is_dir():
                print('NOT FOUND:', folder)
                continue
            sample = None
            # Probe direct dataset files without loading arrays or traversing Drive.
            for candidate in folder.iterdir():
                if candidate.suffix.lower() in ('.npz', '.npy', '.edf') and candidate.is_file():
                    sample = candidate
                    break
            if sample is None:
                print('Folder accessible; no direct .npz/.npy/.edf files:', folder)
                continue
            with sample.open('rb') as handle:
                size = len(handle.read(64))
            if not size:
                print('EMPTY sample:', sample)
                continue
            reads += 1
            print('Dataset read: PASS;', size, 'bytes;', sample)
        except OSError as error:
            print('Dataset read: FAIL;', folder, ';', type(error).__name__, str(error))
    if not reads:
        raise RuntimeError('No dataset sample could be read from the paths used in this notebook.')
    print('Connection checks passed for', reads, 'dataset location(s).')

try:
    _eeg_connection_dataset_check()
finally:
    del _eeg_connection_dataset_check
"""
note = """## Drive and runtime connection checks (new cells only)

These cells were appended locally and have NOT been executed in Colab.
Run only the three new code cells below, in order. Do not use Run all.
They mount Drive without forcing a remount, report installed packages/GPU,
and read up to 64 bytes of one dataset file per location already used above.
They do not run training, install packages, or write to Drive.
Google may ask you to authorize Drive access when the mount cell runs.
"""
notebook['cells'].append({'cell_type': 'markdown', 'metadata': {'connection_checks': marker},
                           'source': note.splitlines(keepends=True)})
for label, source in (('mount', mount), ('runtime', runtime), ('dataset', dataset)):
    ast.parse(source)
    notebook['cells'].append({'cell_type': 'code', 'metadata': {'connection_checks': marker},
                               'execution_count': None, 'outputs': [],
                               'source': source.splitlines(keepends=True)})
assert notebook['cells'][:len(original['cells'])] == original['cells']
assert notebook['metadata'] == original['metadata']
with backup.open('xb') as handle:
    handle.write(original_bytes)
path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
verified = json.loads(path.read_text(encoding='utf-8'))
assert verified['cells'][:len(original['cells'])] == original['cells']
assert {k:v for k,v in verified.items() if k != 'cells'} == {k:v for k,v in original.items() if k != 'cells'}
assert backup.read_bytes() == original_bytes
print('Original cells preserved:', len(original['cells']))
print('Original cells with outputs preserved:', sum(bool(c.get('outputs')) for c in original['cells']))
print('Appended: 1 markdown cell and 3 unexecuted code cells')
print('Backup SHA256:', hashlib.sha256(original_bytes).hexdigest())
print('Remote Drive/runtime/dataset checks: NOT EXECUTED')
