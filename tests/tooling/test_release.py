"""Release bundles are source-derived, isolated and honest about host acceptance."""

import json
import os
from pathlib import Path
import sys
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import zipfile
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tooling"))
from plugin_tools import io
from plugin_tools.registry import load_catalog
from plugin_tools.release import check_release, prepare_release, verify_release
from plugin_tools.rendering import file_hashes, package_files
from tests.tooling.test_registry import add_plugin, write_json

HOSTS = ["claude", "codex", "zcode"]


def png(size):
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))
    ihdr = struct.pack(">IIBBBBB", size, size, 1, 0, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + \
        chunk(b"IDAT", zlib.compress(b"\0" * ((size // 8 + 1) * size))) + chunk(b"IEND", b"")


def release_plugin(root):
    plugin = add_plugin(root, "ai-one", hosts=HOSTS, skills=["ask"])
    manifest = json.loads((plugin / "product.json").read_text())
    manifest["publisher"] = {"name": "Example", "url": "https://example.com"}
    manifest["display_name"] = "AI One"
    manifest["resources"].append({"source": "assets/icon.svg", "target": "assets/icon.svg", "include": []})
    write_json(plugin / "product.json", manifest)
    (plugin / "assets").mkdir()
    (plugin / "assets/icon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M0 0h64v64H0z"/></svg>')
    adapter = json.loads((plugin / "adapters/codex/plugin.json").read_text())
    adapter["extensions"] = {"com.openai": {"interface": {
        "displayName": "AI One", "shortDescription": "Useful AI skills", "longDescription": "Explain useful AI tasks.",
        "developerName": "Example", "category": "Developer Tools", "defaultPrompt": ["Use the ask skill."],
        "logo": "./assets/icon.svg", "composerIcon": "./assets/icon.svg"}}}
    write_json(plugin / "adapters/codex/plugin.json", adapter)
    release = plugin / "release"
    release.mkdir()
    for name, text in (("NOTES.md", "A useful first release."), ("README.md", "# AI One\nUse ask."),
                       ("README_CN.md", "# AI One\n使用 ask。")):
        (release / name).write_text(text)
    write_json(plugin / "release.json", {"schema_version": 1, "notes": "release/NOTES.md",
        "readmes": {"en": "release/README.md", "zh-CN": "release/README_CN.md"},
        "acceptance": {host: None for host in HOSTS}})
    write_json(root / "catalog.json", {"schema_version": 1, "plugins": [{"path": "plugins/ai-one"}]})
    return plugin


def refresh_record(bundle):
    """Attacker updates every self-reported checksum; source checks must still fail."""
    files = {path.relative_to(bundle).as_posix(): path.read_bytes()
             for path in bundle.rglob("*") if path.is_file() and path.name not in ("release.json", "SHA256SUMS")}
    (bundle / "SHA256SUMS").write_text("".join(f"{io.sha256(data)}  {relative}\n" for relative, data in sorted(files.items())))
    files["SHA256SUMS"] = (bundle / "SHA256SUMS").read_bytes()
    record = json.loads((bundle / "release.json").read_text())
    record["files"] = [[name, io.sha256(data)] for name, data in sorted(files.items())]
    record["content_hash"] = io.sha256(io.canonical_json(record["files"]))
    write_json(bundle / "release.json", record)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ai-release-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "repo"
        self.plugin = release_plugin(self.root)
        self.output = self.base / "release"

    def spec(self):
        return load_catalog(self.root)[0]

    def prepare(self, **options):
        result = prepare_release(self.root, self.spec(), self.output, **options)
        self.assertTrue(result["ok"], result)
        return result

    def test_draft_valid_metadata_reports_every_unverified_host(self):
        report = check_release(self.root, self.spec())
        self.assertTrue(report["ok"], report)
        self.assertFalse(report["publication_ready"])
        self.assertEqual(set(report["pending_acceptance"]), set(HOSTS))

    def test_prepare_three_host_downloads_and_submission_source_kits(self):
        self.prepare()
        for host, channel, native in (("claude", "claude", ".claude-plugin/plugin.json"),
                                     ("codex", "openai", "plugin.json"), ("zcode", "zcode", ".zcode-plugin/plugin.json")):
            self.assertTrue((self.output / f"downloads/ai-one-1.0.0-{host}.zip").is_file())
            kit = self.output / f"submissions/{channel}/plugins/ai-one"
            self.assertTrue((kit / native).is_file())
            self.assertTrue((kit / "README_CN.md").is_file())
            with zipfile.ZipFile(self.output / f"submissions/{channel}/ai-one-1.0.0.zip") as archive:
                names = archive.namelist()
                self.assertTrue(all(name.startswith("ai-one/") for name in names))
                self.assertNotIn("ai-one/artifact.json", names)
                self.assertIn("ai-one/skills/ask/SKILL.md", names)
        report = verify_release(self.root, self.spec(), self.output)
        self.assertTrue(report["ok"], report)
        second = self.base / "second"
        self.assertTrue(prepare_release(self.root, self.spec(), second)["ok"])
        bytes_at = lambda root: {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        self.assertEqual(bytes_at(self.output), bytes_at(second))

    def test_stable_cannot_use_missing_acceptance_or_absent_git_tag(self):
        report = check_release(self.root, self.spec(), mode="stable")
        self.assertFalse(report["ok"], report)
        self.assertFalse(report["publication_ready"])
        self.assertTrue(report["blockers"])
        result = prepare_release(self.root, self.spec(), self.output, mode="stable")
        self.assertFalse(result["ok"])
        self.assertFalse(self.output.exists())

    def test_source_metadata_rejects_missing_unsafe_and_oversized_icons(self):
        path = self.plugin / "assets/icon.svg"
        original = path.read_bytes()
        for payload in (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"/>',
                        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><script>alert(1)</script></svg>',
                        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><image href="https://example.com/external"/></svg>',
                        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><set attributeName="href" to="https://example.com/external"/></svg>',
                        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path style="fill:u\\72l(https://example.com/external)"/></svg>',
                        original + b" " * (5 * 1024 * 1024)):
            path.write_bytes(payload)
            report = check_release(self.root, self.spec())
            self.assertFalse(report["ok"], report)
            self.assertTrue(any("icon" in item.lower() or "svg" in item.lower() for item in report["blockers"]), report)
        path.write_bytes(original)
        config = json.loads((self.plugin / "adapters/codex/plugin.json").read_text())
        config["extensions"]["com.openai"]["interface"]["logo"] = "./assets/missing.svg"
        write_json(self.plugin / "adapters/codex/plugin.json", config)
        self.assertFalse(check_release(self.root, self.spec())["ok"])

    def test_svg_rejects_nonfinite_dimensions_and_allows_local_quoted_paint(self):
        icon = self.plugin / "assets/icon.svg"
        icon.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="inf" height="inf"/>')
        self.assertFalse(check_release(self.root, self.spec())["ok"])
        icon.write_text("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs><linearGradient id="paint"/></defs><path style="fill:url('#paint')"/></svg>""")
        self.assertTrue(check_release(self.root, self.spec())["ok"])

    def test_default_prompts_are_optional_scalar_or_at_most_three_unique_short_entries(self):
        path = self.plugin / "adapters/codex/plugin.json"
        adapter = json.loads(path.read_text())
        interface = adapter["extensions"]["com.openai"]["interface"]
        interface.pop("defaultPrompt")
        write_json(path, adapter)
        self.assertTrue(check_release(self.root, self.spec())["ok"])
        interface["defaultPrompt"] = "Use ask."
        write_json(path, adapter)
        self.assertTrue(check_release(self.root, self.spec())["ok"])
        for prompts in (["x" * 129], ["one", "two", "three", "four"], ["one", "one"], "x" * 129):
            interface["defaultPrompt"] = prompts
            write_json(path, adapter)
            self.assertFalse(check_release(self.root, self.spec())["ok"], prompts)

    def use_png(self, payload):
        product = json.loads((self.plugin / "product.json").read_text())
        product["resources"][-1] = {"source": "assets/icon.png", "target": "assets/icon.png", "include": []}
        write_json(self.plugin / "product.json", product)
        path = self.plugin / "adapters/codex/plugin.json"
        adapter = json.loads(path.read_text())
        interface = adapter["extensions"]["com.openai"]["interface"]
        interface.update(logo="./assets/icon.png", composerIcon="./assets/icon.png")
        write_json(path, adapter)
        icon = self.plugin / "assets/icon.png"
        icon.write_bytes(payload)
        return icon

    def test_png_icons_reject_more_than_4096_pixels(self):
        icon = self.use_png(png(8192))
        self.assertFalse(check_release(self.root, self.spec())["ok"])
        icon.write_bytes(png(64))
        self.assertTrue(check_release(self.root, self.spec())["ok"])

    def test_png_header_without_complete_chunks_is_rejected(self):
        self.use_png(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 64, 64))
        report = check_release(self.root, self.spec())
        self.assertFalse(report["ok"], report)
        self.assertTrue(any("PNG" in item for item in report["blockers"]), report)

    def test_png_invalid_crc_and_missing_image_data_are_rejected(self):
        valid = png(64)
        icon = self.use_png(valid)
        icon.write_bytes(valid[:29] + b"\0\0\0\0" + valid[33:])
        self.assertFalse(check_release(self.root, self.spec())["ok"])
        icon.write_bytes(valid[:33] + valid[-12:])
        self.assertFalse(check_release(self.root, self.spec())["ok"])

    def accept(self, hosts=HOSTS, artifact=None):
        spec = self.spec()
        config = json.loads((self.plugin / "release.json").read_text())
        for host in hosts:
            relative = artifact or f"release/{host}-raw.txt"
            if artifact is None:
                (self.plugin / relative).write_text(f"PRIVATE_HOST_LOG_{host}")
            evidence = {"schema_version": 1, "status": "accepted", "host": host, "version": spec.version,
                "source_tree_hash": spec.source_tree_hash,
                "package_content_hash": io.sha256(io.canonical_json(file_hashes(package_files(spec, host)))),
                "host_version": "test-host-1", "summary": "Completed the real host case.",
                "artifacts": [{"path": relative, "sha256": io.sha256((self.plugin / relative).read_bytes())}]}
            write_json(self.plugin / f"release/{host}-accepted.json", evidence)
            config["acceptance"][host] = f"release/{host}-accepted.json"
        write_json(self.plugin / "release.json", config)

    def test_host_raw_evidence_cannot_also_be_a_public_registered_resource(self):
        self.accept(["codex"], artifact="README.md")
        report = check_release(self.root, self.spec())
        self.assertFalse(report["ok"], report)

    def test_copied_raw_evidence_cannot_alias_public_source_bytes(self):
        marker = b"PRIVATE_HOST_SESSION_SECRET_TOKEN_EXAMPLE"
        (self.plugin / "README.md").write_bytes(marker)
        (self.plugin / "release/host-raw.txt").write_bytes(marker)
        self.accept(["codex"], artifact="release/host-raw.txt")
        report = prepare_release(self.root, self.spec(), self.output)
        self.assertFalse(report["ok"], report)
        self.assertFalse(self.output.exists())

    def test_hardlinked_raw_evidence_cannot_alias_public_source_bytes(self):
        marker = b"PRIVATE_HOST_SESSION_SECRET_TOKEN_EXAMPLE"
        (self.plugin / "README.md").write_bytes(marker)
        os.link(self.plugin / "README.md", self.plugin / "release/host-raw.txt")
        self.accept(["codex"], artifact="release/host-raw.txt")
        report = prepare_release(self.root, self.spec(), self.output)
        self.assertFalse(report["ok"], report)
        self.assertFalse(self.output.exists())

    def test_accepted_byte_bound_evidence_enables_stable_with_valid_git_facts(self):
        self.accept()
        provenance = {"source_revision": "a" * 40, "working_tree_dirty": False,
            "tag": "ai-one/v1.0.0", "tag_commit": "a" * 40}
        with mock.patch("plugin_tools.release.metadata.git_provenance", return_value=provenance), \
                mock.patch("plugin_tools.build._git_state", return_value=("a" * 40, False)), \
                mock.patch("plugin_tools.release.source_git._head_blob", side_effect=lambda root, revision, relative: (Path(root) / relative).read_bytes()):
            report = self.prepare(mode="stable", tag="ai-one/v1.0.0")
            self.assertTrue(report["publication_ready"], report)
            self.assertTrue(verify_release(self.root, self.spec(), self.output)["ok"])
        for host in HOSTS:
            raw = f"PRIVATE_HOST_LOG_{host}".encode()
            self.assertFalse(any(raw in file.read_bytes() for file in self.output.rglob("*") if file.is_file()))

    def test_invalid_supplied_tag_is_rejected_without_output(self):
        report = prepare_release(self.root, self.spec(), self.output, tag="wrong/v1.0.0")
        self.assertFalse(report["ok"])
        self.assertFalse(self.output.exists())

    @staticmethod
    def unavailable_git_status(arguments, **options):
        if arguments[1] == "status":
            return SimpleNamespace(returncode=128, stdout="", stderr="fatal: Git status unavailable")
        return SimpleNamespace(returncode=0, stdout="a" * 40 + "\n", stderr="")

    def test_stable_status_read_failure_does_not_claim_a_clean_tagged_source(self):
        self.accept()
        with mock.patch("plugin_tools.release.metadata.subprocess.run", side_effect=self.unavailable_git_status):
            report = check_release(self.root, self.spec(), mode="stable")
        self.assertFalse(report["ok"], report)
        self.assertFalse(report["publication_ready"])
        self.assertIsNone(report["working_tree_dirty"])

    def test_draft_status_read_failure_is_reported_instead_of_claiming_clean(self):
        with mock.patch("plugin_tools.release.metadata.subprocess.run", side_effect=self.unavailable_git_status):
            report = check_release(self.root, self.spec(), mode="draft")
        self.assertFalse(report["ok"], report)
        self.assertIsNone(report["working_tree_dirty"])
        self.assertTrue(any("status" in item for item in report["blockers"]), report)

    def test_public_build_cannot_record_failed_git_status_as_clean(self):
        from plugin_tools import build
        with mock.patch("plugin_tools.build.subprocess.run", side_effect=self.unavailable_git_status):
            with self.assertRaisesRegex(io.DataError, "status"):
                build.build_plugins(self.root, [self.spec()], self.output)
        self.assertFalse(self.output.exists())

    def test_late_source_changes_leave_no_output(self):
        from plugin_tools.release import core
        original = core._write_payload
        def change_source(stage, files):
            original(stage, files)
            (self.plugin / "release/NOTES.md").write_text("Late changed notes")
        with mock.patch.object(core, "_write_payload", side_effect=change_source):
            report = prepare_release(self.root, self.spec(), self.output)
        self.assertFalse(report["ok"], report)
        self.assertTrue(any("changed" in item for item in report["blockers"]), report)
        self.assertFalse(self.output.exists())

    def test_missing_publisher_or_oversized_listing_blocks_draft(self):
        product = json.loads((self.plugin / "product.json").read_text())
        product.pop("publisher")
        write_json(self.plugin / "product.json", product)
        self.assertFalse(check_release(self.root, self.spec())["ok"])
        product["publisher"] = {"name": "Example"}
        write_json(self.plugin / "product.json", product)
        adapter = json.loads((self.plugin / "adapters/codex/plugin.json").read_text())
        adapter["extensions"]["com.openai"]["interface"]["shortDescription"] = "x" * 31
        write_json(self.plugin / "adapters/codex/plugin.json", adapter)
        self.assertFalse(check_release(self.root, self.spec())["ok"])

    def test_openai_submission_does_not_silently_drop_unsupported_hooks(self):
        adapter = json.loads((self.plugin / "adapters/codex/plugin.json").read_text())
        adapter["hooks"] = {"PreToolUse": []}
        write_json(self.plugin / "adapters/codex/plugin.json", adapter)
        report = check_release(self.root, self.spec())
        self.assertFalse(report["ok"], report)
        self.assertTrue(any("hooks" in item for item in report["blockers"]), report)

    def test_submission_deletion_cannot_be_hidden_by_self_rehash(self):
        self.prepare()
        (self.output / "submissions/openai/plugins/ai-one/skills/ask/SKILL.md").unlink()
        refresh_record(self.output)
        report = verify_release(self.root, self.spec(), self.output)
        self.assertFalse(report["ok"], report)
        self.assertTrue(any("trusted" in item or "closure" in item for item in report["blockers"]), report)

    def test_hostile_submission_zip_cannot_be_hidden_by_self_rehash(self):
        self.prepare()
        with zipfile.ZipFile(self.output / "submissions/zcode/ai-one-1.0.0.zip", "a") as archive:
            archive.writestr("../outside.txt", "extra")
        refresh_record(self.output)
        self.assertFalse(verify_release(self.root, self.spec(), self.output)["ok"])

    def test_previous_same_version_mutation_and_downgrade_are_rejected(self):
        self.prepare()
        previous = self.output / "release.json"
        (self.plugin / "README.md").write_text("Mutated plugin source")
        self.assertFalse(check_release(self.root, self.spec(), previous=previous)["ok"])
        product = json.loads((self.plugin / "product.json").read_text())
        product["version"] = "0.9.0"
        write_json(self.plugin / "product.json", product)
        self.assertFalse(check_release(self.root, self.spec(), previous=previous)["ok"])

    def test_previous_requires_actual_files_not_a_self_claimed_version(self):
        self.prepare()
        previous = self.output / "release.json"
        (self.output / "downloads/ai-one-1.0.0-codex.zip").write_bytes(b"broken")
        self.assertFalse(check_release(self.root, self.spec(), previous=previous)["ok"])

    def test_source_alias_output_is_rejected_without_mutating_source(self):
        alias = self.base / "alias"
        alias.symlink_to(self.plugin, target_is_directory=True)
        result = prepare_release(self.root, self.spec(), alias / "bundle")
        self.assertFalse(result["ok"], result)
        self.assertFalse((self.plugin / "bundle").exists())

    def test_invalid_evidence_binding_blocks_even_draft(self):
        spec = self.spec()
        evidence = {"schema_version": 1, "status": "accepted", "host": "codex", "version": "0.0.1",
            "source_tree_hash": spec.source_tree_hash, "package_content_hash": "a" * 64,
            "host_version": "test-host", "summary": "Real host case", "artifacts": [{"path": "release/capture.txt", "sha256": "a" * 64}]}
        (self.plugin / "release/capture.txt").write_text("case evidence")
        write_json(self.plugin / "release/codex.json", evidence)
        config = json.loads((self.plugin / "release.json").read_text())
        config["acceptance"]["codex"] = "release/codex.json"
        write_json(self.plugin / "release.json", config)
        report = check_release(self.root, self.spec())
        self.assertFalse(report["ok"], report)
        self.assertTrue(any("evidence" in item for item in report["blockers"]), report)

    def test_repeated_exact_same_candidate_is_allowed_but_never_overwrites(self):
        self.prepare()
        previous = self.output / "release.json"
        self.assertTrue(check_release(self.root, self.spec(), previous=previous)["ok"])
        result = prepare_release(self.root, self.spec(), self.output, previous=previous)
        self.assertFalse(result["ok"])
