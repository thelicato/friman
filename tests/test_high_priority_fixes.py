"""Offline regression tests for the four high-priority review findings."""
import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import typer
from friman.commands import download, install, pushserver
from friman.utils import definitions, helpers


class HighPriorityFixTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="friman-regression-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.env_root = self.root / "env"
        self.env_root.mkdir()
        self.bin_root = self.root / "bin"
        self.bin_root.mkdir()
        self.current = self.root / "current"
        self.stack.enter_context(patch.multiple(
            definitions, FRIMAN_FOLDER=str(self.root),
            FRIMAN_ENV_FOLDER=str(self.env_root),
            FRIMAN_CURRENT_FOLDER=str(self.current),
            FRIMAN_BIN_FOLDER=str(self.bin_root),
        ))

    def patch(self, obj, attribute, **kwargs):
        return self.stack.enter_context(patch.object(obj, attribute, **kwargs))

    def test_windows_shims_use_scripts_directory(self):
        self._check_shims("nt", "Scripts", "frida.exe")

    def test_posix_shims_use_bin_directory(self):
        self._check_shims("posix", "bin", "frida")

    def _check_shims(self, os_name, bin_name, command):
        scripts = self.current / bin_name
        scripts.mkdir(parents=True)
        (scripts / command).write_bytes(b"command")
        (scripts / "python").write_bytes(b"not a frida command")
        symlink = self.patch(helpers.os, "symlink")
        with patch.object(helpers.os, "name", os_name):
            helpers.create_current_bin_shims()
        symlink.assert_called_once_with(
            str(scripts / command), str(self.bin_root / command),
            target_is_directory=False,
        )

    def test_shims_without_selected_environment_are_noop(self):
        symlink = self.patch(helpers.os, "symlink")
        helpers.create_current_bin_shims()
        symlink.assert_not_called()

    def _download_setup(self, assets):
        self.patch(helpers, "get_current_version_in_use", return_value="16.0.0")
        self.patch(helpers, "get_github_release_assets", return_value=assets)
        return self.patch(helpers, "make_request", return_value=b"fixture asset")

    def test_empty_release_exits_cleanly(self):
        request = self._download_setup([])
        with self.assertRaises(typer.Exit) as caught:
            download.download("server", "android-arm64", str(self.root))
        self.assertEqual(caught.exception.exit_code, 1)
        request.assert_not_called()

    def test_no_matching_asset_exits_cleanly(self):
        request = self._download_setup([
            ("frida-server-16.0.0-linux-x86_64.xz", "https://example.invalid/asset"),
        ])
        with self.assertRaises(typer.Exit) as caught:
            download.download("server", "android-arm64", str(self.root))
        self.assertEqual(caught.exception.exit_code, 1)
        request.assert_not_called()

    def test_matching_asset_is_saved(self):
        name = "frida-server-16.0.0-android-arm64.xz"
        request = self._download_setup([(name, "https://example.invalid/asset")])
        result = download.download("server", "android-arm64", str(self.root))
        self.assertEqual(Path(result).read_bytes(), b"fixture asset")
        request.assert_called_once()

    def test_push_uses_native_basename(self):
        self.patch(helpers, "get_current_version_in_use", return_value="16.0.0")
        self.patch(pushserver, "list_devices", return_value=[
            {"id": "TEST", "type": "usb", "name": "fixture"},
        ])
        self.patch(pushserver.shutil, "which", return_value="adb")
        local_path = self.root / "directory with spaces" / "frida-server"
        self.patch(download, "download", return_value=str(local_path) + ".xz")
        self.patch(helpers, "extract_xz", return_value=str(local_path))
        run = self.patch(pushserver.subprocess, "run", return_value=Mock(returncode=0))
        pushserver.push_server("TEST", "arm64")
        self.assertEqual(run.call_args.args[0], [
            "adb", "-s", "TEST", "push", str(local_path),
            "/data/local/tmp/frida-server",
        ])

    def _install_setup(self, existing=True, legacy=False):
        self.patch(helpers, "get_config_updated_at", return_value="2026-09-20 00:00:00")
        self.patch(helpers, "is_older_than", return_value=False)
        self.patch(helpers, "get_frida_tags", return_value=["16.0.0"])
        self.patch(helpers, "get_matching_frida_tools_version", return_value="12.0.0")
        env = self.env_root / "16.0.0"
        if existing:
            env.mkdir()
            (env / "original.marker").write_bytes(b"original environment")
            if not legacy:
                (env / "pyvenv.cfg").write_text("home = fixture", encoding="utf-8")
                python_path = Path(helpers.get_env_python_path(str(env)))
                python_path.parent.mkdir()
                python_path.write_bytes(b"fixture python")
        return env

    def _process(self, env, failure=None, stage=1, wrong_version=False):
        calls = []

        def run(args, **kwargs):
            calls.append(args)
            if len(calls) == 1:
                self.assertEqual(args[-1], str(env))
                env.mkdir(exist_ok=True)
                (env / "new.marker").write_bytes(b"new environment")
            if len(calls) == stage and isinstance(failure, BaseException):
                raise failure
            rc = 1 if len(calls) == stage and failure == "nonzero" else 0
            output = "99.0.0\n" if wrong_version else "16.0.0\n"
            return subprocess.CompletedProcess(args, rc, output, "simulated error" if rc else "")

        mocked = self.patch(install.subprocess, "run", side_effect=run)
        return mocked

    def _assert_restored(self, env):
        self.assertTrue((env / "original.marker").exists(), "original environment was lost")
        self.assertEqual((env / "original.marker").read_bytes(), b"original environment")
        self.assertFalse((env / "new.marker").exists())
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["bin", "env"])

    def test_force_venv_failure_restores_original(self):
        env = self._install_setup()
        self._process(env, "nonzero", stage=1)
        with self.assertRaises(typer.Exit):
            install.install("16.0.0", force=True)
        self._assert_restored(env)

    def test_force_pip_failure_restores_original(self):
        env = self._install_setup()
        self._process(env, "nonzero", stage=2)
        with self.assertRaises(typer.Exit):
            install.install("16.0.0", force=True)
        self._assert_restored(env)

    def test_force_process_exception_restores_original(self):
        env = self._install_setup()
        self._process(env, OSError("simulated launch failure"), stage=2)
        with self.assertRaises(OSError):
            install.install("16.0.0", force=True)
        self._assert_restored(env)

    def test_force_interrupt_restores_original(self):
        env = self._install_setup()
        self._process(env, KeyboardInterrupt(), stage=2)
        with self.assertRaises(KeyboardInterrupt):
            install.install("16.0.0", force=True)
        self._assert_restored(env)

    def test_force_validation_failure_restores_original(self):
        env = self._install_setup()
        self._process(env, "nonzero", stage=3)
        with self.assertRaises(typer.Exit):
            install.install("16.0.0", force=True)
        self._assert_restored(env)

    def test_force_wrong_installed_version_restores_original(self):
        env = self._install_setup()
        self._process(env, wrong_version=True)
        with self.assertRaises(typer.Exit):
            install.install("16.0.0", force=True)
        self._assert_restored(env)

    def test_force_legacy_failure_restores_original(self):
        env = self._install_setup(legacy=True)
        self._process(env, "nonzero", stage=2)
        with self.assertRaises(typer.Exit):
            install.install("16.0.0", force=True)
        self._assert_restored(env)

    def test_force_success_validates_and_cleans_backup(self):
        env = self._install_setup()
        run = self._process(env)
        install.install("16.0.0", force=True)
        self.assertFalse((env / "original.marker").exists())
        self.assertTrue((env / "new.marker").exists())
        self.assertEqual(run.call_count, 3)
        self.assertEqual(run.call_args.args[0], [
            helpers.get_env_command_path(str(env), "frida"), "--version",
        ])
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["bin", "env"])

    def test_backup_move_failure_keeps_original(self):
        env = self._install_setup()
        self.patch(install.os, "replace", side_effect=PermissionError("backup move denied"))
        run = self.patch(install.subprocess, "run")
        with self.assertRaises(PermissionError):
            install.install("16.0.0", force=True)
        run.assert_not_called()
        self._assert_restored(env)

    def test_failed_recovery_keeps_backup_for_manual_restore(self):
        env = self._install_setup()
        self._process(env, "nonzero", stage=2)
        self.patch(install.shutil, "rmtree", side_effect=PermissionError("partial env locked"))
        with self.assertRaises(PermissionError):
            install.install("16.0.0", force=True)
        backups = list(self.root.glob(".friman-*-backup-*/environment/original.marker"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), b"original environment")

    def test_backup_cleanup_failure_keeps_successful_install(self):
        env = self._install_setup()
        self._process(env)
        self.patch(install.shutil, "rmtree", side_effect=PermissionError("backup locked"))
        install.install("16.0.0", force=True)
        self.assertTrue((env / "new.marker").exists())
        backups = list(self.root.glob(".friman-*-backup-*/environment/original.marker"))
        self.assertEqual(len(backups), 1)

    def test_existing_without_force_is_untouched(self):
        env = self._install_setup()
        run = self.patch(install.subprocess, "run")
        with self.assertRaises(typer.Exit) as caught:
            install.install("16.0.0", force=False)
        self.assertEqual(caught.exception.exit_code, 0)
        run.assert_not_called()
        self._assert_restored(env)

    def test_fresh_install_failure_cleans_partial_environment(self):
        env = self._install_setup(existing=False)
        self._process(env, "nonzero", stage=2)
        with self.assertRaises(typer.Exit):
            install.install("16.0.0", force=False)
        self.assertFalse(env.exists())

    def test_fresh_install_success(self):
        env = self._install_setup(existing=False)
        self._process(env)
        install.install("16.0.0", force=False)
        self.assertTrue((env / "new.marker").exists())


if __name__ == "__main__":
    unittest.main()
