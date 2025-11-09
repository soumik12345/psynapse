"""Unit tests for environment variable handling in GraphExecutor."""

import os

from psynapse.backend.executor import GraphExecutor


def test_env_vars_set_during_execution():
    """Test that environment variables are set during execution."""
    # Create a simple graph with a function that reads an environment variable
    graph_data = {
        "nodes": [
            {
                "id": "node_0",
                "type": "view",
                "input_sockets": [
                    {"id": "node_0_input_0", "name": "value", "value": 42}
                ],
                "output_sockets": [],
            }
        ],
        "edges": [],
    }

    # Set test environment variables
    env_vars = {"TEST_VAR": "test_value", "ANOTHER_VAR": "another_value"}

    # Ensure variables don't exist before execution
    assert "TEST_VAR" not in os.environ
    assert "ANOTHER_VAR" not in os.environ

    # Execute with environment variables
    executor = GraphExecutor(graph_data, env_vars)
    results = executor.execute()

    # Verify execution succeeded
    assert "node_0" in results
    assert results["node_0"]["value"] == 42
    assert results["node_0"]["error"] is None

    # Verify environment variables are cleaned up after execution
    assert "TEST_VAR" not in os.environ
    assert "ANOTHER_VAR" not in os.environ


def test_env_vars_restored_after_execution():
    """Test that original environment variables are restored after execution."""
    # Set an existing environment variable
    original_value = "original_value"
    os.environ["EXISTING_VAR"] = original_value

    graph_data = {
        "nodes": [
            {
                "id": "node_0",
                "type": "view",
                "input_sockets": [
                    {"id": "node_0_input_0", "name": "value", "value": 42}
                ],
                "output_sockets": [],
            }
        ],
        "edges": [],
    }

    # Override the existing variable
    env_vars = {"EXISTING_VAR": "new_value"}

    # Execute with environment variables
    executor = GraphExecutor(graph_data, env_vars)
    results = executor.execute()

    # Verify execution succeeded
    assert "node_0" in results
    assert results["node_0"]["value"] == 42
    assert results["node_0"]["error"] is None

    # Verify original value is restored
    assert os.environ["EXISTING_VAR"] == original_value

    # Cleanup
    del os.environ["EXISTING_VAR"]


def test_env_vars_restored_after_error():
    """Test that environment variables are restored even if execution fails."""
    # Create a graph with a cycle (will cause error)
    graph_data = {
        "nodes": [
            {
                "id": "node_0",
                "type": "add",
                "input_sockets": [
                    {"id": "node_0_input_0", "name": "a", "value": None},
                    {"id": "node_0_input_1", "name": "b", "value": 1.0},
                ],
                "output_sockets": [{"id": "node_0_output_0", "name": "result"}],
            },
            {
                "id": "node_1",
                "type": "add",
                "input_sockets": [
                    {"id": "node_1_input_0", "name": "a", "value": None},
                    {"id": "node_1_input_1", "name": "b", "value": 1.0},
                ],
                "output_sockets": [{"id": "node_1_output_0", "name": "result"}],
            },
            {
                "id": "node_2",
                "type": "view",
                "input_sockets": [
                    {"id": "node_2_input_0", "name": "value", "value": None}
                ],
                "output_sockets": [],
            },
        ],
        "edges": [
            {"start_socket": "node_0_output_0", "end_socket": "node_1_input_0"},
            {"start_socket": "node_1_output_0", "end_socket": "node_0_input_0"},
            {"start_socket": "node_1_output_0", "end_socket": "node_2_input_0"},
        ],
    }

    # Set environment variables
    env_vars = {"TEST_VAR": "test_value"}

    # Ensure variable doesn't exist before execution
    assert "TEST_VAR" not in os.environ

    # Execute (will fail due to cycle)
    executor = GraphExecutor(graph_data, env_vars)
    results = executor.execute()

    # Verify execution failed
    assert "node_2" in results
    assert results["node_2"]["value"] is None
    assert results["node_2"]["error"] is not None

    # Verify environment variable is cleaned up even after error
    assert "TEST_VAR" not in os.environ
