from typing import Any

import pytest

from psynapse.editor.backend_client import BackendClient


@pytest.fixture(scope="module")
def anyio_backend():
    """Use only asyncio backend since aiohttp doesn't support trio."""
    return "asyncio"


@pytest.mark.anyio
async def test_health_check():
    """Test that the backend server is healthy and reachable."""
    client = BackendClient()
    healthy = await client.health_check()
    assert healthy, (
        "Backend server is not running or not healthy. Start it with: psynapse-backend"
    )


@pytest.mark.anyio
async def test_node_schemas():
    client = BackendClient()
    schemas_response = await client.get_node_schemas()
    schemas = schemas_response.get("nodes", [])
    # ViewNode and ObjectNode are frontend-only
    # We dynamically load all operations from nodepacks/basic.py and nodepacks/llm/ops.py
    assert len(schemas) == 13, "Expected 13 node schemas, got " + str(len(schemas))

    # Verify that the core operations are present
    schema_names = [schema["name"] for schema in schemas]
    core_operations = [
        "add",
        "subtract",
        "multiply",
        "divide",
        "modulo",
        "power",
        "sqrt",
        "log",
        "exp",
        "at_index",
        "query_with_index",
    ]
    for op in core_operations:
        assert op in schema_names, f"Expected operation '{op}' not found in schemas"

    # Verify that LLM operations are present
    assert "LLM_Message" in schema_names, (
        "Expected LLM_Message operation not found in schemas"
    )

    # Verify schema structure for one operation
    add_schema = next((s for s in schemas if s["name"] == "add"), None)
    assert add_schema is not None, "add schema not found"
    assert "params" in add_schema, "add schema missing params"
    assert "returns" in add_schema, "add schema missing returns"
    assert len(add_schema["params"]) == 2, "add should have 2 parameters"
    assert len(add_schema["returns"]) == 1, "add should have 1 return value"

    # Verify LLM_Message schema structure
    llm_message_schema = next((s for s in schemas if s["name"] == "LLM_Message"), None)
    assert llm_message_schema is not None, "LLM_Message schema not found"
    assert "params" in llm_message_schema, "LLM_Message schema missing params"
    assert "returns" in llm_message_schema, "LLM_Message schema missing returns"
    assert len(llm_message_schema["params"]) == 2, (
        "LLM_Message should have 2 parameters"
    )
    assert len(llm_message_schema["returns"]) == 1, (
        "LLM_Message should have 1 return value"
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "graph_data",
    [
        {
            "id": "simple_graph",
            "payload": {
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
        },
        {
            "id": "complex_graph",
            "payload": {
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
        },
    ],
)
async def test_backend_grapth_execution(graph_data: dict[str, Any]):
    client = BackendClient()
    payload = {}
    payload = graph_data["payload"]
    result = await client.execute_graph(payload)
    results = result.get("results", {})
    if graph_data["id"] == "simple_graph":
        assert "node_1" in results, "Expected result for node_1, got " + str(results)
        assert results["node_1"].get("value") == 8.0, (
            "Expected result of 8.0, got " + str(results["node_1"].get("value"))
        )
    elif graph_data["id"] == "complex_graph":
        assert "node_2" in results, "Expected result for node_2, got " + str(results)
        assert results["node_2"].get("value") == 5.0, (
            "Expected result of 5.0, got " + str(results["node_2"].get("value"))
        )


@pytest.mark.anyio
async def test_object_node_as_input():
    """Test that ObjectNode can provide values to operation nodes."""
    client = BackendClient()

    # Graph: ObjectNode(10.0) + ObjectNode(25.0) -> ViewNode
    graph_data = {
        "nodes": [
            # ObjectNode #1 - provides value 10.0
            {
                "id": "node_0",
                "type": "object",
                "input_sockets": [],
                "output_sockets": [
                    {"id": "node_0_output_0", "name": "value", "value": 10.0}
                ],
            },
            # ObjectNode #2 - provides value 25.0
            {
                "id": "node_1",
                "type": "object",
                "input_sockets": [],
                "output_sockets": [
                    {"id": "node_1_output_0", "name": "value", "value": 25.0}
                ],
            },
            # Add node
            {
                "id": "node_2",
                "type": "add",
                "input_sockets": [
                    {"id": "node_2_input_0", "name": "a", "value": None},
                    {"id": "node_2_input_1", "name": "b", "value": None},
                ],
                "output_sockets": [{"id": "node_2_output_0", "name": "result"}],
            },
            # ViewNode
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
    }

    result = await client.execute_graph(graph_data)
    results = result.get("results", {})

    assert "node_3" in results, "Expected result for node_3, got " + str(results)
    assert results["node_3"].get("value") == 35.0, (
        "Expected result of 35.0 (10.0 + 25.0), got "
        + str(results["node_3"].get("value"))
    )
