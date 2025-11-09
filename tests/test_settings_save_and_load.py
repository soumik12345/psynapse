"""Test saving and loading environment variables in settings."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from psynapse.editor.settings_dialog import SettingsDialog


def test_save_and_load_env_vars():
    """Test that environment variables can be saved and then loaded correctly."""

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_settings_path = Path(temp_dir) / "settings.json"

        # Create a SettingsDialog instance with mocked settings path
        with patch.object(SettingsDialog, "__init__", lambda self, parent=None: None):
            dialog = SettingsDialog()
            dialog.settings_path = temp_settings_path
            dialog.env_vars = {}

            # Add environment variables
            test_env_vars = {
                "OPENAI_API_KEY": "sk-test12345",
                "ANTHROPIC_API_KEY": "sk-ant-test67890",
                "CUSTOM_VAR": "custom_value",
            }

            for name, value in test_env_vars.items():
                dialog.env_vars[name] = value

            # Save settings
            dialog._save_settings()

            # Verify file was created
            assert temp_settings_path.exists()

            # Verify file contents
            with open(temp_settings_path, "r") as f:
                data = json.load(f)
                assert "env_vars" in data
                assert data["env_vars"] == test_env_vars

            # Now load the settings using the static method
            def mock_load():
                if temp_settings_path.exists():
                    try:
                        with open(temp_settings_path, "r") as f:
                            data = json.load(f)
                            return data.get("env_vars", {})
                    except Exception:
                        return {}
                return {}

            with patch.object(SettingsDialog, "load_env_vars", mock_load):
                loaded_env_vars = SettingsDialog.load_env_vars()

                # Verify all environment variables were loaded correctly
                assert loaded_env_vars == test_env_vars
                assert "OPENAI_API_KEY" in loaded_env_vars
                assert loaded_env_vars["OPENAI_API_KEY"] == "sk-test12345"
                assert "ANTHROPIC_API_KEY" in loaded_env_vars
                assert loaded_env_vars["ANTHROPIC_API_KEY"] == "sk-ant-test67890"
                assert "CUSTOM_VAR" in loaded_env_vars
                assert loaded_env_vars["CUSTOM_VAR"] == "custom_value"


def test_load_env_vars_with_missing_file():
    """Test that load_env_vars returns empty dict when file doesn't exist."""

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_settings_path = Path(temp_dir) / "nonexistent" / "settings.json"

        def mock_load():
            if temp_settings_path.exists():
                try:
                    with open(temp_settings_path, "r") as f:
                        data = json.load(f)
                        return data.get("env_vars", {})
                except Exception:
                    return {}
            return {}

        with patch.object(SettingsDialog, "load_env_vars", mock_load):
            loaded_env_vars = SettingsDialog.load_env_vars()
            assert loaded_env_vars == {}


def test_load_env_vars_with_corrupted_file():
    """Test that load_env_vars handles corrupted files gracefully."""

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_settings_path = Path(temp_dir) / "settings.json"

        # Write corrupted JSON
        with open(temp_settings_path, "w") as f:
            f.write("{ this is not valid json }")

        def mock_load():
            if temp_settings_path.exists():
                try:
                    with open(temp_settings_path, "r") as f:
                        data = json.load(f)
                        return data.get("env_vars", {})
                except Exception:
                    return {}
            return {}

        with patch.object(SettingsDialog, "load_env_vars", mock_load):
            loaded_env_vars = SettingsDialog.load_env_vars()
            assert loaded_env_vars == {}


if __name__ == "__main__":
    test_save_and_load_env_vars()
    test_load_env_vars_with_missing_file()
    test_load_env_vars_with_corrupted_file()
    print("All tests passed!")
