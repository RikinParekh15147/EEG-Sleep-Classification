import importlib.util
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

HOST=Path(__file__).resolve().parents[1]/'bridge/host.py'
spec=importlib.util.spec_from_file_location('sleep_bridge_host',HOST)
host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)

class PtyAuthentication(unittest.TestCase):
    def test_drive_prompt_uses_controlling_tty_and_auth_code_is_not_echoed(self):
        with tempfile.TemporaryDirectory(prefix='sleep-bridge-') as folder:
            cli=Path(folder)/'fake-colab'
            cli.write_text('#!'+sys.executable+'\nimport sys\nprint("https://accounts.google.com/test",flush=True)\nprint("Press Enter after you have granted access... ",end="",flush=True)\nwith open("/dev/tty") as tty:tty.readline()\nprint("\\nSLEEP_JSON:{\\"ok\\":true}",flush=True)\n')
            cli.chmod(0o700)
            events=[];original_send=host.send;original_config=host.CONFIG_DIR
            host.send=events.append;host.CONFIG_DIR=Path(folder)/'state'
            result={}
            def command():
                try:result['output']=host.cli({'cliPath':str(cli)},['drivemount'],'auth-test',10)
                except Exception as error:result['error']=error
            thread=threading.Thread(target=command);thread.start()
            try:
                until=time.monotonic()+8
                while time.monotonic()<until and not any(e.get('event')=='auth-prompt' for e in events):time.sleep(.03)
                self.assertTrue(any(e.get('event')=='auth-prompt' for e in events),events)
                host.handle({'id':'reply','action':'auth-reply','params':{'requestId':'auth-test','value':'secret-test-code'}})
                thread.join(5);self.assertFalse(thread.is_alive());self.assertNotIn('error',result)
                self.assertEqual(host.marker(result['output']),{'ok':True})
                self.assertNotIn('secret-test-code',str(events));self.assertNotIn('secret-test-code',result['output'])
            finally:
                host.send=original_send;host.CONFIG_DIR=original_config
    def test_token_redaction(self):
        self.assertNotIn('abc123',host.clean('Bearer abc123'))
        self.assertNotIn('abc123',host.clean('refresh_token: abc123'))

if __name__=='__main__':unittest.main()
