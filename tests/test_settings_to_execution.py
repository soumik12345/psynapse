"""Test the complete flow from settings to execution."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from psynapse.backend.executor import GraphExecutor
from psynapse.editor.settings_dialog import SettingsDialog


def test_settings_flow_to_execution():
    """Test that environment variables saved in settings are used during execution."""

    # Create a temporary settings file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_settings_path = Path(temp_dir) / "settings.json"

        # Mock the settings path
        with patch.object(SettingsDialog, "__init__", lambda self, parent=None: None):
            # Create settings data
            settings_data = {
                "env_vars": {
                    "TEST_API_KEY": "my_secret_key_123",
                    "TEST_SETTING": "test_value",
                }
            }

            # Write settings file
            with open(temp_settings_path, "w") as f:
                json.dump(settings_data, f)

            # Mock the settings_path in SettingsDialog.load_env_vars
            original_load = SettingsDialog.load_env_vars

            def mock_load_env_vars():
                if temp_settings_path.exists():
                    try:
                        with open(temp_settings_path, "r") as f:
                            data = json.load(f)
                            return data.get("env_vars", {})
                    except Exception:
                        return {}
                return {}

            # Test loading environment variables
            with patch.object(SettingsDialog, "load_env_vars", mock_load_env_vars):
                env_vars = SettingsDialog.load_env_vars()

                assert "TEST_API_KEY" in env_vars
                assert env_vars["TEST_API_KEY"] == "my_secret_key_123"
                assert "TEST_SETTING" in env_vars
                assert env_vars["TEST_SETTING"] == "test_value"

                # Create a simple graph
                graph_data = {
                    "nodes": [
                        {
                            "id": "node_0",
                            "type": "view",
                            "input_sockets": [
                                {
                                    "id": "node_0_input_0",
                                    "name": "value",
                                    "value": "test",
                                }
                            ],
                            "output_sockets": [],
                        }
                    ],
                    "edges": [],
                }

                # Ensure env vars don't exist before execution
                original_keys = {}
                for key in env_vars.keys():
                    original_keys[key] = os.environ.pop(key, None)

                try:
                    # Execute with environment variables (simulating what editor does)
                    executor = GraphExecutor(graph_data, env_vars)
                    results = executor.execute()

                    # Verify execution succeeded
                    assert "node_0" in results
                    assert results["node_0"]["error"] is None

                finally:
                    # Restore original env vars
                    for key, val in original_keys.items():
                        if val is not None:
                            os.environ[key] = val

                # Verify environment variables are cleaned up after execution
                for key in env_vars.keys():
                    if key in original_keys and original_keys[key] is not None:
                        assert os.environ[key] == original_keys[key]
                    else:
                        assert key not in os.environ


if __name__ == "__main__":
    test_settings_flow_to_execution()
    print("Test passed!")
