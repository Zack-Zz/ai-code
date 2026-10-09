"""Real subprocess publication races; no native agent or Bridge task is started."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/bridge_client.py"
WRITER = r'''
import importlib.util,json,sys,time
from pathlib import Path
script,root,target,binding=sys.argv[1:]
spec=importlib.util.spec_from_file_location('consumer',script)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
root=Path(root)
create=module.tempfile.NamedTemporaryFile
def hold_publication(*args,**kwargs):
    stream=create(*args,**kwargs)
    (root/('entered-'+binding)).touch()
    end=time.monotonic()+5
    while not (root/'release').exists():
        if time.monotonic()>end:
            stream.close();raise OSError('Test release was not received')
        time.sleep(.01)
    return stream
module.tempfile.NamedTemporaryFile=hold_publication
try:
    module.BridgeClient._write_receipt(target,{'apiVersion':module.API_VERSION,
        'requestId':'request-'+binding,'callerRef':'origin','engine':'codex',
        'projectId':'sample','taskId':'task-'+binding,'sessionId':None,
        'scopeReference':'human:receipt-race'})
    print(json.dumps({'binding':binding,'result':'written'}))
except module.ClientError as error:
    print(json.dumps({'binding':binding,'result':'rejected','code':error.code,
        'executionDisposition':error.execution_disposition}))
'''


@unittest.skipUnless(os.name == "posix", "Native Bridge execution currently requires POSIX")
class ReceiptConcurrencyTests(unittest.TestCase):
    def test_process_exit_releases_the_mutex_without_deleting_its_lock_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt = root / "receipt.json"
            process = subprocess.Popen([sys.executable, "-B", "-c", WRITER,
                                        str(SCRIPT), str(root), str(receipt), "A"],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                self.wait_until(lambda: (root / "entered-A").exists())
                process.kill()
                process.communicate(timeout=8)
                (root / "release").touch()
                retry = subprocess.run([sys.executable, "-B", "-c", WRITER,
                                        str(SCRIPT), str(root), str(receipt), "B"],
                                       capture_output=True, text=True, timeout=8)
                self.assertEqual(0, retry.returncode, retry.stderr)
                self.assertEqual("written", json.loads(retry.stdout)["result"])
                self.assertEqual("task-B", json.loads(receipt.read_text())["taskId"])
            finally:
                if process.poll() is None:
                    process.kill()
                process.communicate(timeout=8)

    def test_two_processes_never_silently_replace_different_task_bindings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt = root / "receipt.json"
            processes = []
            try:
                first = subprocess.Popen([sys.executable, "-B", "-c", WRITER,
                                          str(SCRIPT), str(root), str(receipt), "A"],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                processes.append(first)
                self.wait_until(lambda: (root / "entered-A").exists())
                second = subprocess.Popen([sys.executable, "-B", "-c", WRITER,
                                           str(SCRIPT), str(root), str(receipt), "B"],
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                processes.append(second)
                self.wait_until(lambda: (root / "entered-B").exists() or second.poll() is not None)
                (root / "release").touch()
                results = []
                for process in processes:
                    stdout, stderr = process.communicate(timeout=8)
                    self.assertEqual(0, process.returncode, stderr)
                    results.append(json.loads(stdout))
                self.assertEqual(["rejected", "written"], sorted(item["result"] for item in results),
                                 "a conflicting receipt must not overwrite a successful task binding")
                self.assertEqual("task-A", json.loads(receipt.read_text())["taskId"])
                rejected = next(item for item in results if item["result"] == "rejected")
                self.assertEqual("RECEIPT_WRITE_FAILED", rejected["code"])
                self.assertEqual("unknown", rejected["executionDisposition"])
            finally:
                (root / "release").touch()
                for process in processes:
                    if process.poll() is None:
                        process.kill()
                    process.communicate(timeout=8)

    def wait_until(self, predicate):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(.01)
        self.fail("Subprocess did not reach the bounded test publication point")


if __name__ == "__main__":
    unittest.main()
