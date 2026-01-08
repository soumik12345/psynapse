"""
Simple test script to verify backend functionality
"""

from psynapse_backend.executor import GraphExecutor
from psynapse_backend.schema_extractor import extract_all_schemas


def test_schema_extraction():
    """Test schema extraction from nodepacks"""
    print("Testing schema extraction...")
    schemas = extract_all_schemas("../nodepacks")
    print(f"✓ Found {len(schemas)} functions")

    # Verify we found the expected functions
    function_names = [s["name"] for s in schemas]
    expected_functions = ["add", "subtract", "multiply", "divide"]

    for func in expected_functions:
        assert func in function_names, f"Missing expected function: {func}"

    print(f"✓ All expected functions found: {expected_functions}")
    return schemas


def test_graph_execution():
    """Test graph execution with a simple workflow"""
    print("\nTesting graph execution...")

    executor = GraphExecutor("../nodepacks")

    # Create a simple graph: add(5, 3) -> ViewNode
    nodes = [
        {
            "id": "node_1",
            "type": "functionNode",
            "data": {"functionName": "add", "a": 5, "b": 3},
        },
        {"id": "node_2", "type": "viewNode", "data": {}},
    ]

    edges = [
        {
            "source": "node_1",
            "target": "node_2",
            "sourceHandle": "output",
            "targetHandle": "input",
        }
    ]

    results = executor.execute_graph(nodes, edges)

    assert "node_2" in results, "ViewNode result not found"
    assert results["node_2"] == 8, f"Expected 8, got {results['node_2']}"

    print(f"✓ Simple graph executed correctly: add(5, 3) = {results['node_2']}")


def test_complex_graph():
    """Test a more complex graph with multiple operations"""
    print("\nTesting complex graph execution...")

    executor = GraphExecutor("../nodepacks")

    # Create graph: (add(5, 3) * add(2, 4)) -> ViewNode
    # Should result in (8 * 6) = 48
    nodes = [
        {
            "id": "add1",
            "type": "functionNode",
            "data": {"functionName": "add", "a": 5, "b": 3},
        },
        {
            "id": "add2",
            "type": "functionNode",
            "data": {"functionName": "add", "a": 2, "b": 4},
        },
        {
            "id": "mult",
            "type": "functionNode",
            "data": {"functionName": "multiply", "a": 0, "b": 0},
        },
        {"id": "view", "type": "viewNode", "data": {}},
    ]

    edges = [
        {
            "source": "add1",
            "target": "mult",
            "sourceHandle": "output",
            "targetHandle": "a",
        },
        {
            "source": "add2",
            "target": "mult",
            "sourceHandle": "output",
            "targetHandle": "b",
        },
        {
            "source": "mult",
            "target": "view",
            "sourceHandle": "output",
            "targetHandle": "input",
        },
    ]

    results = executor.execute_graph(nodes, edges)

    assert "view" in results, "ViewNode result not found"
    assert results["view"] == 48, f"Expected 48, got {results['view']}"

    print(f"✓ Complex graph executed correctly: (5+3) * (2+4) = {results['view']}")


if __name__ == "__main__":
    print("=" * 50)
    print("Running Psynapse Backend Tests")
    print("=" * 50)

    try:
        test_schema_extraction()
        test_graph_execution()
        test_complex_graph()

        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
