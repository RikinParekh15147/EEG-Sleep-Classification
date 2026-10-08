"""Create a separate test notebook; never modify the user's notebook."""
import ast
import json
from pathlib import Path

root = Path(__file__).resolve().parent
checks = (root / 'colab_connection_checks.py').read_text(encoding='utf-8')
mount = """def _eeg_mount_drive_check():
    from google.colab import drive
    drive.mount('/content/drive', force_remount=False)

try:
    _eeg_mount_drive_check()
finally:
    del _eeg_mount_drive_check
"""
for source in (mount, checks):
    ast.parse(source)
cells = [{
    'cell_type': 'markdown', 'metadata': {}, 'source': [
        '# Colab connection checks\n',
        'Prepared only; these cells have not been executed remotely.\n',
        'Copy the code cells to the end of your existing notebook and run only those new cells.\n',
        'The mount uses force_remount=False. The checks read at most 64 bytes of one dataset file.\n',
        'To test the dataset, set EEG_DATASET_PATH in a new cell, for example:\n',
        "`import os; os.environ['EEG_DATASET_PATH'] = '/content/drive/MyDrive/YOUR_DATASET_FOLDER'`\n",
    ],
}]
for index, source in enumerate((mount, checks)):
    cells.append({'cell_type': 'code', 'id': f'eeg-connection-check-{index}',
                  'metadata': {}, 'execution_count': None, 'outputs': [],
                  'source': source.splitlines(keepends=True)})
notebook = {'cells': cells, 'metadata': {
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python'},
}, 'nbformat': 4, 'nbformat_minor': 5}
target = root / 'colab_connection_checks.ipynb'
with target.open('x', encoding='utf-8') as handle:
    json.dump(notebook, handle, indent=2)
print('Created separate notebook:', target.name)
print('Verified Python syntax; remote checks are not executed.')
