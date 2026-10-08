import json,subprocess,sys,importlib.metadata as md
try:
    version=md.version('mne')
except md.PackageNotFoundError:
    subprocess.run([sys.executable,'-m','pip','install','mne==1.13.2'],check=True)
    version=md.version('mne')
import mne
print('SLEEP_JSON:'+json.dumps({'mne':version,'imported':mne.__version__}))
