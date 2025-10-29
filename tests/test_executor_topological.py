"""Unit tests for the GraphExecutor with topological sorting."""

import pytest

from psynapse.backend.executor import GraphExecutor


@pytest.mark.parametrize(
    "test_id,graph_data,expected_view_node,expected_value,description",
    [
        (
            "simple_add",
            {
                "nodes": [
                    {
                        "id": "node_0",
                        "type": "add",
                        "input_sockets": [
                            {"id": "node_0_input_0", "name": "a", "value": 5.0},
                            {"id": "node_0_input_1", "name": "b", "value": 3.0},
                        ],
                        "output_sockets": [{"id": "node_0_output_0", "name": "result"}],
                    },
                    {
                        "id": "node_1",
                        "type": "view",
                        "input_sockets": [
                            {"id": "node_1_input_0", "name": "value", "value": None}
                        ],
                        "output_sockets": [],
                    },
                ],
                "edges": [
                    {
                        "start_socket": "node_0_output_0",
                        "end_socket": "node_1_input_0",
                    }
                ],
            },
            "node_1",
            8.0,
            "Simple add operation (5.0 + 3.0 = 8.0)",
        ),
        (
            "chain_operations",
            {
                "nodes": [
                    {
                        "id": "node_0",
                        "type": "multiply",
                        "input_sockets": [
                            {"id": "node_0_input_0", "name": "a", "value": 10.0},
                            {"id": "node_0_input_1", "name": "b", "value": 2.0},
                        ],
                        "output_sockets": [{"id": "node_0_output_0", "name": "result"}],
                    },
                    {
                        "id": "node_1",
                        "type": "divide",
                        "input_sockets": [
                            {"id": "node_1_input_0", "name": "a", "value": None},
                            {"id": "node_1_input_1", "name": "b", "value": 4.0},
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
                    {
                        "start_socket": "node_0_output_0",
                        "end_socket": "node_1_input_0",
                    },
                    {
                        "start_socket": "node_1_output_0",
                        "end_socket": "node_2_input_0",
                    },
                ],
            },
            "node_2",
            5.0,
            "Chain operations: multiply then divide ((10.0 * 2.0) / 4.0 = 5.0)",
        ),
        (
            "object_nodes",
            {
                "nodes": [
                    {
                        "id": "node_0",
                        "type": "object",
                        "input_sockets": [],
                        "output_sockets": [
                            {"id": "node_0_output_0", "name": "value", "value": 10.0}
                        ],
                    },
                    {
                        "id": "node_1",
                        "type": "object",
                        "input_sockets": [],
                        "output_sockets": [
                            {"id": "node_1_output_0", "name": "value", "value": 25.0}
                        ],
                    },
                    {
                        "id": "node_2",
                        "type": "add",
                        "input_sockets": [
                            {"id": "node_2_input_0", "name": "a", "value": None},
                            {"id": "node_2_input_1", "name": "b", "value": None},
                        ],
                        "output_sockets": [{"id": "node_2_output_0", "name": "result"}],
                    },
                    {
                        "id": "node_3",
                        "type": "view",
                        "input_sockets": [
                            {"id": "node_3_input_0", "name": "value", "value": None}
                        ],
                        "output_sockets": [],
                    },
                ],
                "edges": [
                    {"start_socket": "node_0_output_0", "end_socket": "node_2_input_0"},
                    {"start_socket": "node_1_output_0", "end_socket": "node_2_input_1"},
                    {"start_socket": "node_2_output_0", "end_socket": "node_3_input_0"},
                ],
            },
            "node_3",
            35.0,
            "ObjectNodes as inputs (10.0 + 25.0 = 35.0)",
        ),
        (
            "diamond_graph",
            {
                "nodes": [
                    {
                        "id": "node_0",
                        "type": "object",
                        "input_sockets": [],
                        "output_sockets": [
                            {"id": "node_0_output_0", "name": "value", "value": 10.0}
                        ],
                    },
                    {
                        "id": "node_1",
                        "type": "multiply",
                        "input_sockets": [
                            {"id": "node_1_input_0", "name": "a", "value": None},
                            {"id": "node_1_input_1", "name": "b", "value": 2.0},
                        ],
                        "output_sockets": [{"id": "node_1_output_0", "name": "result"}],
                    },
                    {
                        "id": "node_2",
                        "type": "add",
                        "input_sockets": [
                            {"id": "node_2_input_0", "name": "a", "value": None},
                            {"id": "node_2_input_1", "name": "b", "value": 5.0},
                        ],
                        "output_sockets": [{"id": "node_2_output_0", "name": "result"}],
                    },
                    {
                        "id": "node_3",
                        "type": "add",
                        "input_sockets": [
                            {"id": "node_3_input_0", "name": "a", "value": None},
                            {"id": "node_3_input_1", "name": "b", "value": None},
                        ],
                        "output_sockets": [{"id": "node_3_output_0", "name": "result"}],
                    },
                    {
                        "id": "node_4",
                        "type": "view",
                        "input_sockets": [
                            {"id": "node_4_input_0", "name": "value", "value": None}
                        ],
                        "output_sockets": [],
                    },
                ],
                "edges": [
                    {"start_socket": "node_0_output_0", "end_socket": "node_1_input_0"},
                    {"start_socket": "node_0_output_0", "end_socket": "node_2_input_0"},
                    {"start_socket": "node_1_output_0", "end_socket": "node_3_input_0"},
                    {"start_socket": "node_2_output_0", "end_socket": "node_3_input_1"},
                    {"start_socket": "node_3_output_0", "end_socket": "node_4_input_0"},
                ],
            },
            "node_4",
            35.0,
            "Diamond-shaped dependency graph ((10.0 * 2.0) + (10.0 + 5.0) = 35.0)",
        ),
    ],
)
def test_successful_graph_execution(
    test_id, graph_data, expected_view_node, expected_value, description
):
    """Test successful graph execution with various graph structures."""
    executor = GraphExecutor(graph_data)
    results = executor.execute()

    assert expected_view_node in results, (
        f"{description}: View node not found in results"
    )
    assert results[expected_view_node]["value"] == expected_value, (
        f"{description}: Expected {expected_value}, got {results[expected_view_node]['value']}"
    )
    assert results[expected_view_node]["error"] is None, (
        f"{description}: Expected no error, got {results[expected_view_node]['error']}"
    )


@pytest.mark.parametrize(
    "test_id,graph_data,expected_view_node,expected_error_keyword,description",
    [
        (
            "simple_cycle",
            {
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
            },
            "node_2",
            "cycle",
            "Cyclic graph detection (node_0 -> node_1 -> node_0)",
        ),
    ],
)
def test_error_handling(
    test_id, graph_data, expected_view_node, expected_error_keyword, description
):
    """Test error handling for invalid graph structures."""
    executor = GraphExecutor(graph_data)
    results = executor.execute()

    assert expected_view_node in results, (
        f"{description}: View node not found in results"
    )
    assert results[expected_view_node]["value"] is None, (
        f"{description}: Expected None value for error case"
    )
    assert expected_error_keyword in results[expected_view_node]["error"].lower(), (
        f"{description}: Expected error containing '{expected_error_keyword}', "
        f"got {results[expected_view_node]['error']}"
    )


@pytest.mark.parametrize(
    "test_id,graph_data,expected_view_node,expected_value,description",
    [
        (
            "disconnected_nodes",
            {
                "nodes": [
                    {
                        "id": "node_0",
                        "type": "add",
                        "input_sockets": [
                            {"id": "node_0_input_0", "name": "a", "value": 5.0},
                            {"id": "node_0_input_1", "name": "b", "value": 3.0},
                        ],
                        "output_sockets": [{"id": "node_0_output_0", "name": "result"}],
                    },
                    {
                        "id": "node_1",
                        "type": "view",
                        "input_sockets": [
                            {"id": "node_1_input_0", "name": "value", "value": 42.0}
                        ],
                        "output_sockets": [],
                    },
                ],
                "edges": [],
            },
            "node_1",
            42.0,
            "Disconnected nodes with default value",
        ),
    ],
)
def test_edge_cases(
    test_id, graph_data, expected_view_node, expected_value, description
):
    """Test edge cases in graph execution."""
    executor = GraphExecutor(graph_data)
    results = executor.execute()

    assert expected_view_node in results, (
        f"{description}: View node not found in results"
    )
    assert results[expected_view_node]["value"] == expected_value, (
        f"{description}: Expected {expected_value}, got {results[expected_view_node]['value']}"
    )
    assert results[expected_view_node]["error"] is None, (
        f"{description}: Expected no error, got {results[expected_view_node]['error']}"
    )
