import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from friman.commands import ensurepath, use
from friman.utils import helpers


class PathPriorityTests(unittest.TestCase):
    def test_powershell_prepends_instead_of_appending(self):
        block = ensurepath.build_profile_block("windows", "", r"C:\Users\fixture\.friman\bin")
        self.assertNotIn("$env:PATH +=", block)
        self.assertIn("+ $env:PATH", block)
        self.assertIn("$env:PATH =", block)

    def test_powershell_quotes_literal_path(self):
        block = ensurepath.build_profile_block("windows", "", r"C:\Users\O'Brien\.friman\bin")
        self.assertIn("O''Brien", block)

    def test_old_managed_block_is_migrated_and_idempotent(self):
        with tempfile.TemporaryDirectory(prefix="friman-profile-test-") as temporary:
            profile = Path(temporary) / "profile.ps1"
            entry = r"C:\Users\fixture\.friman\bin"
            unrelated = "# user's existing config\n$env:OTHER = 'keep'\n"
            profile.write_text(unrelated + f'# >>> friman >>>\n$env:PATH += ";{entry}"\n# <<< friman <<<\n', encoding="utf-8")
            with patch.object(ensurepath.platform, "system", return_value="Windows"), patch.object(ensurepath, "get_path_entry", return_value=entry), patch.object(ensurepath, "get_shell_profile", return_value=profile), patch.object(helpers, "create_current_bin_shims"), contextlib.redirect_stdout(io.StringIO()):
                ensurepath.ensurepath()
                first = profile.read_text(encoding="utf-8")
                ensurepath.ensurepath()
                second = profile.read_text(encoding="utf-8")
            self.assertNotIn("$env:PATH +=", first)
            self.assertEqual(first.count("# >>> friman >>>"), 1)
            self.assertIn(unrelated, first)
            self.assertEqual(first, second)

    def test_windows_ensurepath_prints_cmd_activation(self):
        with tempfile.TemporaryDirectory(prefix="friman-profile-test-") as temporary:
            profile = Path(temporary) / "profile.ps1"
            output = io.StringIO()
            with patch.object(ensurepath.platform, "system", return_value="Windows"), patch.object(ensurepath, "get_shell_profile", return_value=profile), patch.object(helpers, "create_current_bin_shims"), contextlib.redirect_stdout(output):
                ensurepath.ensurepath()
            self.assertIn('set "PATH=', output.getvalue())
            self.assertIn(';%PATH%"', output.getvalue())

    def test_selected_command_does_not_warn(self):
        env = str(Path.cwd() / "test-environment")
        expected = helpers.get_env_command_path(env, "frida")
        with patch("shutil.which", return_value=expected), patch.object(use.frimanlog, "warning") as warning:
            use._warn_if_shadowed(env)
        warning.assert_not_called()

    def test_global_command_shadowing_is_reported(self):
        env = str(Path.cwd() / "test-environment")
        other = str(Path.cwd() / "global-python" / "frida.exe")
        with patch("shutil.which", return_value=other), patch.object(use.frimanlog, "warning") as warning, patch.object(use.frimanlog, "info"):
            use._warn_if_shadowed(env)
        self.assertIn(other, warning.call_args.args[0])

    def test_missing_command_prints_activation_instructions(self):
        output = io.StringIO()
        with patch("shutil.which", return_value=None), contextlib.redirect_stdout(output):
            use._warn_if_shadowed(str(Path.cwd() / "test-environment"))
        self.assertIn("PATH", output.getvalue())
        self.assertIn("friman", output.getvalue())


if __name__ == "__main__":
    unittest.main()
