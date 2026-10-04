from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime"))
import providers
import harnesses
from grok_cli_worker import stop_owned_leader
from store import Store


class GrokTests(unittest.TestCase):
    def test_cli_catalog_does_not_count_login_text_as_a_model(self):
        result = subprocess.CompletedProcess([], 0, "You are logged in with grok.com.\nAvailable models:\n * grok-4.7 (default)\n - grok-4.6\n", "")
        with patch("providers.subprocess.run", return_value=result):
            self.assertEqual(providers.grok_catalog(), ["grok-4.7", "grok-4.6"])

    def test_failed_catalog_is_not_a_verified_provider(self):
        with patch("providers.subprocess.run", return_value=subprocess.CompletedProcess([], 1, "", "login required")):
            with self.assertRaises(RuntimeError):
                providers.grok_catalog()

    def test_model_identity_rejects_undocumented_alias_and_extra_model(self):
        self.assertTrue(providers.model_matches("grok", "grok-4.7", {"models": ["grok-4.7-build"]}))
        self.assertFalse(providers.model_matches("grok", "grok-4.7", {"models": ["grok-4.6"]}))
        self.assertFalse(providers.model_matches("grok", "grok-4.7", {"models": ["grok-4.7-build", "grok-4.6"]}))
        self.assertFalse(providers.model_matches("grok", "invented", {"models": []}))

    def test_max_turns_and_errors_do_not_establish_completion(self):
        for data in [{"text": "PASS", "stopReason": "max_turns"}, {"type": "error", "message": "login required"}]:
            self.assertFalse(providers.parse_output("grok", json.dumps(data))["completed"])

    def test_native_session_and_actual_backend_are_retained(self):
        result = providers.parse_output("grok", json.dumps({"text": "proof", "stopReason": "end_turn", "sessionId": "native-uuid", "modelUsage": {"grok-4.7-build": {}}}))
        self.assertEqual(result["session"], "native-uuid")
        self.assertEqual(result["models"], ["grok-4.7-build"])
        self.assertTrue(result["completed"])

    def test_unverified_writer_is_rejected(self):
        with self.assertRaises(ValueError):
            providers.command({"provider": "grok", "model": "unverified-writer", "effort": "xhigh"}, "edit", False)

    def test_ignored_reasoning_effort_is_not_counted_as_supported(self):
        self.assertFalse(providers.effort_applied("grok", "WARN model does not support reasoning effort; ignoring"))
        self.assertTrue(providers.effort_applied("grok", ""))

    def test_reused_leader_pid_is_never_signalled(self):
        with patch("grok_cli_worker.process_identity", return_value="different process"), patch("grok_cli_worker.os.kill") as kill:
            stop_owned_leader(1234, "owned identity")
            kill.assert_not_called()

    def test_missing_owner_cannot_signal_a_process_group(self):
        with patch("grok_cli_worker.os.kill") as kill:
            stop_owned_leader(0, "owned identity")
            stop_owned_leader(None, None)
            kill.assert_not_called()

    def test_rejected_effort_is_not_persisted(self):
        result = subprocess.CompletedProcess([], 1, '{"type":"error","message":"unsupported max"}', "unsupported max")
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder))
            store.put("config", "execution", {"host": "local", "mode": "local-cli", "enabled_cli": ["grok"], "machine": harnesses.fingerprint()})
            with patch("providers.grok_catalog", return_value=["grok-4.7"]), patch("providers.capture", return_value=result):
                with self.assertRaises(RuntimeError):
                    providers.probe(store, "grok", "grok-4.7", "max")
            self.assertEqual(store.list("model"), [])

    def test_successful_probe_exposes_transport_backend_and_effort(self):
        data = {"text": "PSTACK_MODEL_PROBE", "stopReason": "end_turn", "sessionId": "native", "modelUsage": {"grok-4.7-build": {}}}
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder))
            store.put("config", "execution", {"host": "local", "mode": "local-cli", "enabled_cli": ["grok"], "machine": harnesses.fingerprint()})
            with patch("providers.grok_catalog", return_value=["grok-4.7"]), patch("providers.capture", return_value=subprocess.CompletedProcess([], 0, json.dumps(data), "")):
                model = providers.probe(store, "grok", "grok-4.7", "xhigh")
            self.assertEqual(model["family"], "xai")
            self.assertEqual(model["efforts"], ["xhigh"])
            self.assertEqual(model["reported_models"], ["grok-4.7-build"])

    def test_probe_deadline_cancels_owned_child_group(self):
        with tempfile.TemporaryDirectory() as folder:
            argv = [sys.executable, '-c', 'import subprocess,sys,time; child=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"]);open("child.pid","w").write(str(child.pid));time.sleep(60)']
            with self.assertRaisesRegex(RuntimeError, 'deadline exhausted'):
                providers.capture(argv, folder, os.environ.copy(), timeout=.5)
            child = int((Path(folder) / 'child.pid').read_text())
            status = subprocess.run(['ps', '-p', str(child), '-o', 'stat='], capture_output=True, text=True).stdout.strip()
            self.assertTrue(not status or status.startswith('Z'), status)


if __name__ == "__main__":
    unittest.main()
