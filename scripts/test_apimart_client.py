import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import apimart_client


def fingerprint(prompt, size="1:1", resolution="1k", n=1, image_urls=None, official_fallback=False):
    payload = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "n": n,
        "size": size,
        "resolution": resolution,
        "image_urls": image_urls or [],
        "official_fallback": official_fallback,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ApimartClientIdempotencyTest(unittest.TestCase):
    def make_config(self, root: Path, prompt="same prompt", filename="card.png", n=1) -> Path:
        output_dir = root / "out"
        config_path = root / "config.json"
        config_path.write_text(json.dumps({
            "series_title": "test",
            "output_dir": str(output_dir),
            "size": "1:1",
            "resolution": "1k",
            "cards": [{"title": "card", "prompt": prompt, "filename": filename, "n": n}],
        }, ensure_ascii=False))
        return config_path

    def test_reuses_existing_nonfailed_task_instead_of_resubmitting(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = self.make_config(root)
            output_dir = root / "out"
            output_dir.mkdir()
            (output_dir / ".apimart-tasks.json").write_text(json.dumps({
                "version": 1,
                "tasks": [{
                    "fingerprint": fingerprint("same prompt"),
                    "task_id": "task_existing",
                    "status": "processing",
                    "filename": "card.png",
                }],
            }))

            def fake_save(task_data, out_dir):
                generated = Path(out_dir) / "task_existing_1.png"
                generated.write_bytes(b"image")
                return [str(generated)]

            with patch.object(apimart_client, "submit_generate", side_effect=AssertionError("resubmitted")), \
                 patch.object(apimart_client, "poll_task", return_value={"data": {"id": "task_existing", "status": "completed", "result": {"images": []}}}) as poll, \
                 patch.object(apimart_client, "save_results", side_effect=fake_save):
                apimart_client.generate_series(str(config_path))

            poll.assert_called_once_with("task_existing", on_status=unittest.mock.ANY)
            self.assertEqual((output_dir / "card.png").read_bytes(), b"image")

    def test_resubmits_only_when_cached_task_failed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = self.make_config(root)
            output_dir = root / "out"
            output_dir.mkdir()
            (output_dir / ".apimart-tasks.json").write_text(json.dumps({
                "version": 1,
                "tasks": [{
                    "fingerprint": fingerprint("same prompt"),
                    "task_id": "task_failed",
                    "status": "failed",
                    "filename": "card.png",
                }],
            }))

            def fake_submit(*args, **kwargs):
                return {"data": {"task_id": "task_new"}}

            def fake_save(task_data, out_dir):
                generated = Path(out_dir) / "task_new_1.png"
                generated.write_bytes(b"new image")
                return [str(generated)]

            with patch.object(apimart_client, "submit_generate", side_effect=fake_submit) as submit, \
                 patch.object(apimart_client, "poll_task", return_value={"data": {"id": "task_new", "status": "completed", "result": {"images": []}}}), \
                 patch.object(apimart_client, "save_results", side_effect=fake_save):
                apimart_client.generate_series(str(config_path))

            submit.assert_called_once()
            self.assertEqual((output_dir / "card.png").read_bytes(), b"new image")

    def test_existing_output_file_skips_api_calls(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = self.make_config(root)
            output_dir = root / "out"
            output_dir.mkdir()
            (output_dir / "card.png").write_bytes(b"done")

            with patch.object(apimart_client, "submit_generate", side_effect=AssertionError("submitted")), \
                 patch.object(apimart_client, "poll_task", side_effect=AssertionError("polled")):
                apimart_client.generate_series(str(config_path))

            self.assertEqual((output_dir / "card.png").read_bytes(), b"done")

    def test_timeout_rerun_reuses_recorded_task_id(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = self.make_config(root)
            output_dir = root / "out"

            with patch.object(apimart_client, "submit_generate", return_value={"data": {"task_id": "task_timeout"}}), \
                 patch.object(apimart_client, "poll_task", side_effect=SystemExit("timeout")):
                with self.assertRaises(SystemExit):
                    apimart_client.generate_series(str(config_path))

            manifest = json.loads((output_dir / ".apimart-tasks.json").read_text())
            self.assertEqual(manifest["tasks"][0]["task_id"], "task_timeout")

            def fake_save(task_data, out_dir):
                generated = Path(out_dir) / "task_timeout_1.png"
                generated.write_bytes(b"image")
                return [str(generated)]

            with patch.object(apimart_client, "submit_generate", side_effect=AssertionError("resubmitted")), \
                 patch.object(apimart_client, "poll_task", return_value={"data": {"id": "task_timeout", "status": "completed", "result": {"images": []}}}), \
                 patch.object(apimart_client, "save_results", side_effect=fake_save):
                apimart_client.generate_series(str(config_path))

            self.assertEqual((output_dir / "card.png").read_bytes(), b"image")

    def test_failed_during_poll_marks_manifest_failed_then_allows_resubmit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = self.make_config(root)
            output_dir = root / "out"
            output_dir.mkdir()
            (output_dir / ".apimart-tasks.json").write_text(json.dumps({
                "version": 1,
                "tasks": [{
                    "fingerprint": fingerprint("same prompt"),
                    "task_id": "task_existing",
                    "status": "processing",
                    "filename": "card.png",
                }],
            }))

            with patch.object(apimart_client, "_api", return_value={"data": {"id": "task_existing", "status": "failed", "error": {"message": "bad prompt"}}}):
                with self.assertRaises(SystemExit):
                    apimart_client.generate_series(str(config_path))

            manifest = json.loads((output_dir / ".apimart-tasks.json").read_text())
            self.assertEqual(manifest["tasks"][0]["status"], "failed")

            def fake_save(task_data, out_dir):
                generated = Path(out_dir) / "task_new_1.png"
                generated.write_bytes(b"new image")
                return [str(generated)]

            with patch.object(apimart_client, "submit_generate", return_value={"data": {"task_id": "task_new"}}) as submit, \
                 patch.object(apimart_client, "poll_task", return_value={"data": {"id": "task_new", "status": "completed", "result": {"images": []}}}), \
                 patch.object(apimart_client, "save_results", side_effect=fake_save):
                apimart_client.generate_series(str(config_path))

            submit.assert_called_once()
            self.assertEqual((output_dir / "card.png").read_bytes(), b"new image")

    def test_corrupt_manifest_fails_safe_without_submit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = self.make_config(root)
            output_dir = root / "out"
            output_dir.mkdir()
            (output_dir / ".apimart-tasks.json").write_text("{broken")

            with patch.object(apimart_client, "submit_generate", side_effect=AssertionError("submitted")):
                with self.assertRaises(SystemExit):
                    apimart_client.generate_series(str(config_path))

    def test_manifest_entry_without_task_id_fails_safe_without_submit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = self.make_config(root)
            output_dir = root / "out"
            output_dir.mkdir()
            (output_dir / ".apimart-tasks.json").write_text(json.dumps({
                "version": 1,
                "tasks": [{
                    "fingerprint": fingerprint("same prompt"),
                    "status": "processing",
                    "filename": "card.png",
                }],
            }))

            with patch.object(apimart_client, "submit_generate", side_effect=AssertionError("submitted")):
                with self.assertRaises(SystemExit):
                    apimart_client.generate_series(str(config_path))

    def test_n_greater_than_one_tracks_all_saved_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = self.make_config(root, n=2)
            output_dir = root / "out"

            def fake_save(task_data, out_dir):
                first = Path(out_dir) / "task_new_1.png"
                second = Path(out_dir) / "task_new_2.png"
                first.write_bytes(b"first")
                second.write_bytes(b"second")
                return [str(first), str(second)]

            with patch.object(apimart_client, "submit_generate", return_value={"data": {"task_id": "task_new"}}), \
                 patch.object(apimart_client, "poll_task", return_value={"data": {"id": "task_new", "status": "completed", "result": {"images": []}}}), \
                 patch.object(apimart_client, "save_results", side_effect=fake_save):
                apimart_client.generate_series(str(config_path))

            manifest = json.loads((output_dir / ".apimart-tasks.json").read_text())
            self.assertEqual(manifest["tasks"][0]["saved_paths"], [
                str(output_dir / "card.png"),
                str(output_dir / "task_new_2.png"),
            ])


if __name__ == "__main__":
    unittest.main()
