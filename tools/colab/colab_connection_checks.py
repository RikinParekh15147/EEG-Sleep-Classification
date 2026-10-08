"""Read-only checks for a Colab runtime with Drive already mounted.

Execute only this script through the CLI after `colab drivemount`, or paste
its contents into a NEW cell in the existing notebook. No training is run.
"""

def _eeg_colab_connection_check():
    import importlib.metadata
    import os
    import platform
    import shutil
    import subprocess
    from pathlib import Path

    print("Runtime:", platform.platform())
    print("Python:", platform.python_version())
    print("Colab environment:", Path('/content').is_dir())
    for package in ('numpy', 'pandas', 'torch', 'tensorflow', 'mne'):
        try:
            print(package + ':', importlib.metadata.version(package))
        except importlib.metadata.PackageNotFoundError:
            print(package + ': not installed')
    if shutil.which('nvidia-smi'):
        gpu = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
            capture_output=True, text=True, timeout=20,
        )
        print('GPU:', (gpu.stdout or gpu.stderr).strip())
    else:
        print('GPU: nvidia-smi unavailable')

    drive_root = Path('/content/drive/MyDrive')
    if not drive_root.is_dir():
        raise RuntimeError('Drive is not mounted. Run the new mount cell or colab drivemount first.')
    with os.scandir(drive_root) as entries:
        next(entries, None)
    print('Drive directory access: PASS')

    dataset_setting = os.environ.get('EEG_DATASET_PATH', '').strip()
    if not dataset_setting:
        print('Dataset check: NOT TESTED; set EEG_DATASET_PATH to the exact mounted folder path.')
        return
    dataset = Path(dataset_setting)
    if not dataset.is_dir():
        raise FileNotFoundError('Dataset folder does not exist: ' + str(dataset))
    sample = None
    for root, folders, files in os.walk(dataset):
        folders.sort()
        if files:
            sample = Path(root) / sorted(files)[0]
            break
    if sample is None:
        raise RuntimeError('Dataset folder contains no files.')
    with sample.open('rb') as handle:
        count = len(handle.read(64))
    print('Dataset sample read: PASS; read', count, 'bytes from', sample.name)


try:
    _eeg_colab_connection_check()
finally:
    del _eeg_colab_connection_check
