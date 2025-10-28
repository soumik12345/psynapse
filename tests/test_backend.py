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
    assert len(schemas) == 5, "Expected 5 node schemas, got " + str(len(schemas))


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
