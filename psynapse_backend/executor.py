import importlib.util
import inspect
import os
import queue
import threading
from collections import defaultdict, deque
from typing import Any


def _extract_output_value(
    node_outputs: dict[str, Any], source_id: str, source_handle: str
) -> Any:
    """
    Extract the output value from a node, handling AnnotatedDict outputs.

    For AnnotatedDict nodes (which have multiple output handles), the sourceHandle
    specifies which key to extract from the dictionary. For regular nodes with
    a single "output" or "result" handle, the full value is returned.

    Args:
        node_outputs: Dictionary mapping node IDs to their output values.
        source_id: The ID of the source node.
        source_handle: The handle name (e.g., "output", "result", or a key name for AnnotatedDict).

    Returns:
        The extracted value.

    Raises:
        ValueError: If the sourceHandle is a key that doesn't exist in the dict output.
    """
    source_value = node_outputs[source_id]

    # If sourceHandle is "output" or "result", return the full value (backward compatible)
    if source_handle in ("output", "result"):
        return source_value

    # Otherwise, treat sourceHandle as a key to extract from a dict (AnnotatedDict case)
    if isinstance(source_value, dict):
        if source_handle not in source_value:
            raise ValueError(
                f"AnnotatedDict output missing expected key '{source_handle}'. "
                f"Available keys: {list(source_value.keys())}"
            )
        return source_value[source_handle]

    # If not a dict but sourceHandle is not "output"/"result", this is an error
    raise ValueError(
        f"Cannot extract key '{source_handle}' from non-dict output of type {type(source_value).__name__}"
    )


class GraphExecutor:
    """
    GraphExecutor is responsible for executing the node graph.
    The graph is executed in the correct order with dependency resolution by topological sorting using Kahn's algorithm.

    Args:
        nodepacks_dir: The directory containing the nodepacks.

    Attributes:
        nodepacks_dir: The directory containing the nodepacks.
        function_registry: A dictionary of functions from the nodepacks.
        progress_class_registry: A dictionary of progress classes from the nodepacks.
        stream_class_registry: A dictionary of stream classes from the nodepacks.
    """

    def __init__(self, nodepacks_dir: str):
        self.nodepacks_dir = nodepacks_dir
        self.function_registry = {}
        self.progress_class_registry = {}
        self.stream_class_registry = {}
        self._load_functions()

    def _load_functions(self):
        """Load all functions, progress classes, and stream classes from nodepacks into registries."""
        from pathlib import Path

        nodepacks_path = Path(self.nodepacks_dir)
        if not nodepacks_path.exists():
            return

        for nodepack_dir in nodepacks_path.iterdir():
            if nodepack_dir.is_dir():
                # Load regular functions from ops.py
                ops_file = nodepack_dir / "ops.py"
                if ops_file.exists():
                    self._load_functions_from_file(str(ops_file))

                # Load progress classes from progress_ops.py
                progress_ops_file = nodepack_dir / "progress_ops.py"
                if progress_ops_file.exists():
                    self._load_progress_classes_from_file(str(progress_ops_file))

                # Load stream classes from stream_ops.py
                stream_ops_file = nodepack_dir / "stream_ops.py"
                if stream_ops_file.exists():
                    self._load_stream_classes_from_file(str(stream_ops_file))

    def _load_functions_from_file(self, filepath: str):
        """Load functions from a specific file."""
        try:
            spec = importlib.util.spec_from_file_location("module", filepath)
            if spec is None or spec.loader is None:
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and obj.__module__ == module.__name__:
                    self.function_registry[name] = obj

        except Exception as e:
            print(f"Error loading functions from {filepath}: {e}")

    def _load_progress_classes_from_file(self, filepath: str):
        """Load progress classes from a specific file."""
        try:
            spec = importlib.util.spec_from_file_location("module", filepath)
            if spec is None or spec.loader is None:
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for name, obj in inspect.getmembers(module):
                # Load classes with __call__ method (skip private classes)
                if (
                    inspect.isclass(obj)
                    and obj.__module__ == module.__name__
                    and hasattr(obj, "__call__")
                    and not name.startswith("_")
                ):
                    # Store the class (not instance) in registry
                    self.progress_class_registry[name] = obj

        except Exception as e:
            print(f"Error loading progress classes from {filepath}: {e}")

    def _load_stream_classes_from_file(self, filepath: str):
        """Load stream classes from a specific file."""
        try:
            spec = importlib.util.spec_from_file_location("module", filepath)
            if spec is None or spec.loader is None:
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for name, obj in inspect.getmembers(module):
                # Load classes with __call__ method (skip private classes)
                if (
                    inspect.isclass(obj)
                    and obj.__module__ == module.__name__
                    and hasattr(obj, "__call__")
                    and not name.startswith("_")
                ):
                    # Store the class (not instance) in registry
                    self.stream_class_registry[name] = obj

        except Exception as e:
            print(f"Error loading stream classes from {filepath}: {e}")

    def topological_sort(self, nodes: list[dict], edges: list[dict]) -> list[str]:
        """
        Perform topological sort using Kahn's algorithm.
        Returns list of node IDs in execution order.

        Args:
            nodes: The nodes of the graph.
            edges: The edges of the graph.

        Returns:
            A list of node IDs in execution order.
        """
        # Build adjacency list and in-degree map
        graph = defaultdict(list)
        in_degree = defaultdict(int)

        # Initialize all nodes with in-degree 0
        for node in nodes:
            node_id = node["id"]
            if node_id not in in_degree:
                in_degree[node_id] = 0

        # Build graph from edges
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            graph[source].append(target)
            in_degree[target] += 1

        # Queue of nodes with no incoming edges
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        sorted_nodes = []

        while queue:
            node_id = queue.popleft()
            sorted_nodes.append(node_id)

            # Reduce in-degree for neighbors
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(sorted_nodes) != len(nodes):
            raise ValueError("Graph contains a cycle")

        return sorted_nodes

    def execute_graph(
        self,
        nodes: list[dict],
        edges: list[dict],
        env_vars: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute the node graph and return results for `ViewNodes`.

        Args:
            nodes: The nodes of the graph.
            edges: The edges of the graph.
            env_vars: Optional environment variables to set during execution.

        Returns:
            A dictionary of node IDs and their results.
        """
        # Store original environment variables
        original_env = {}
        if env_vars:
            for key in env_vars:
                original_env[key] = os.environ.get(key)
            os.environ.update(env_vars)

        try:
            # Create node lookup
            node_map = {node["id"]: node for node in nodes}

            # Build edge lookup for getting inputs
            incoming_edges = defaultdict(list)
            for edge in edges:
                incoming_edges[edge["target"]].append(edge)

            # Topologically sort nodes
            sorted_node_ids = self.topological_sort(nodes, edges)

            # Store execution results
            node_outputs = {}
            view_node_results = {}

            # Execute nodes in order
            for node_id in sorted_node_ids:
                node = node_map[node_id]
                node_type = node.get("type", "default")

                if node_type == "viewNode":
                    # ViewNode: get input value and store it
                    incoming = incoming_edges.get(node_id, [])
                    if incoming:
                        edge = incoming[0]  # ViewNode has single input
                        source_id = edge["source"]
                        source_handle = edge.get("sourceHandle", "output")

                        if source_id in node_outputs:
                            # Use helper to extract value (handles AnnotatedDict outputs)
                            view_node_results[node_id] = _extract_output_value(
                                node_outputs, source_id, source_handle
                            )
                        else:
                            view_node_results[node_id] = None
                    else:
                        view_node_results[node_id] = None

                elif node_type == "variableNode":
                    # Variable node: output the stored value
                    node_data = node.get("data", {})
                    variable_value = node_data.get("variableValue")
                    variable_type = node_data.get("variableType", "String")
                    text_content_format = node_data.get("textContentFormat", False)
                    image_content_format = node_data.get("imageContentFormat", False)
                    llm_message_format = node_data.get("llmMessageFormat", False)
                    llm_message_role = node_data.get("llmMessageRole", "user")

                    # Convert value based on type
                    if variable_type == "Number":
                        try:
                            if isinstance(variable_value, (int, float)):
                                node_outputs[node_id] = variable_value
                            elif isinstance(variable_value, str):
                                # Try to parse as int first, then float
                                if "." in variable_value:
                                    node_outputs[node_id] = float(variable_value)
                                else:
                                    node_outputs[node_id] = int(variable_value)
                            else:
                                node_outputs[node_id] = 0
                        except (ValueError, TypeError):
                            node_outputs[node_id] = 0
                    elif variable_type == "Boolean":
                        if isinstance(variable_value, bool):
                            node_outputs[node_id] = variable_value
                        elif isinstance(variable_value, str):
                            node_outputs[node_id] = variable_value.lower() in (
                                "true",
                                "1",
                                "yes",
                            )
                        else:
                            node_outputs[node_id] = bool(variable_value)
                    elif variable_type == "List":
                        # Output as Python list
                        if isinstance(variable_value, list):
                            node_outputs[node_id] = variable_value
                        else:
                            node_outputs[node_id] = []
                    elif variable_type == "Object":
                        # Parse JSON string to dict or use as-is if already a dict
                        if isinstance(variable_value, dict):
                            node_outputs[node_id] = variable_value
                        elif isinstance(variable_value, str):
                            try:
                                import json

                                node_outputs[node_id] = json.loads(variable_value)
                            except json.JSONDecodeError:
                                node_outputs[node_id] = {}
                        else:
                            node_outputs[node_id] = {}
                    elif variable_type == "Image":
                        # Output image data URL
                        output_data_url = (
                            str(variable_value) if variable_value is not None else ""
                        )
                        # Apply LLM Message format if enabled (complete message with role and content array)
                        if llm_message_format:
                            node_outputs[node_id] = {
                                "role": llm_message_role,
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": output_data_url},
                                    }
                                ],
                            }
                        else:
                            node_outputs[node_id] = output_data_url
                    else:  # String
                        output_string = (
                            str(variable_value) if variable_value is not None else ""
                        )
                        # Apply LLM Message format if enabled (takes precedence)
                        if llm_message_format:
                            node_outputs[node_id] = {
                                "role": llm_message_role,
                                "content": output_string,
                            }
                        # Apply LLM Message Content if enabled (legacy)
                        elif text_content_format:
                            node_outputs[node_id] = {
                                "type": "text",
                                "content": output_string,
                            }
                        else:
                            node_outputs[node_id] = output_string

                elif node_type == "listNode":
                    # List node: collect values from all connected inputs
                    incoming = incoming_edges.get(node_id, [])

                    # Sort by input index (from targetHandle like "input-0", "input-1")
                    def get_input_index(edge):
                        target_handle = edge.get("targetHandle", "input-0")
                        try:
                            return int(target_handle.split("-")[1])
                        except (IndexError, ValueError):
                            return 0

                    sorted_edges = sorted(incoming, key=get_input_index)

                    # Build list from connected outputs
                    output_list = []
                    for edge in sorted_edges:
                        source_id = edge["source"]
                        source_handle = edge.get("sourceHandle", "output")
                        if source_id in node_outputs:
                            # Use helper to extract value (handles AnnotatedDict outputs)
                            output_list.append(
                                _extract_output_value(
                                    node_outputs, source_id, source_handle
                                )
                            )

                    node_outputs[node_id] = output_list

                else:
                    # Function node: execute the function
                    function_name = node.get("data", {}).get("functionName")
                    if not function_name or function_name not in self.function_registry:
                        continue

                    func = self.function_registry[function_name]

                    # Gather inputs
                    node_data = node.get("data", {})
                    inputs = {}

                    # Get parameter names from function signature
                    sig = inspect.signature(func)
                    param_names = list(sig.parameters.keys())

                    # First, use default values from node data
                    for param_name in param_names:
                        if param_name in node_data:
                            inputs[param_name] = node_data[param_name]

                    # Then, override with values from connected edges
                    for edge in incoming_edges.get(node_id, []):
                        target_handle = edge.get("targetHandle", "")
                        source_id = edge["source"]
                        source_handle = edge.get("sourceHandle", "output")

                        if source_id in node_outputs:
                            # The target handle should indicate which parameter to set
                            if target_handle in param_names:
                                # Use helper to extract value (handles AnnotatedDict outputs)
                                inputs[target_handle] = _extract_output_value(
                                    node_outputs, source_id, source_handle
                                )

                    # Execute function
                    try:
                        # Convert string inputs to appropriate types if needed
                        sig = inspect.signature(func)
                        type_hints = {}
                        try:
                            from typing import get_type_hints

                            type_hints = get_type_hints(func)
                        except:
                            pass

                        converted_inputs = {}
                        for param_name, value in inputs.items():
                            if param_name in type_hints:
                                param_type = type_hints[param_name]
                                if param_type == float and not isinstance(value, float):
                                    converted_inputs[param_name] = float(value)
                                elif param_type == int and not isinstance(
                                    value, (int, bool)
                                ):
                                    converted_inputs[param_name] = int(value)
                                elif param_type == str and not isinstance(value, str):
                                    converted_inputs[param_name] = str(value)
                                elif param_type == bool and not isinstance(value, bool):
                                    converted_inputs[param_name] = bool(value)
                                else:
                                    converted_inputs[param_name] = value
                            else:
                                converted_inputs[param_name] = value

                        result = func(**converted_inputs)
                        node_outputs[node_id] = result

                    except Exception as e:
                        print(f"Error executing node {node_id} ({function_name}): {e}")
                        node_outputs[node_id] = None

            return view_node_results
        finally:
            # Restore original environment variables
            if env_vars:
                for key, value in original_env.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

    def execute_graph_streaming(
        self,
        nodes: list[dict],
        edges: list[dict],
        env_vars: dict[str, str] | None = None,
    ) -> Any:
        """
        Execute the node graph and yield status updates for each node.

        Args:
            nodes: The nodes of the graph.
            edges: The edges of the graph.
            env_vars: Optional environment variables to set during execution.

        Yields:
            Status dictionaries containing execution progress information.
        """
        # Store original environment variables
        original_env = {}
        if env_vars:
            for key in env_vars:
                original_env[key] = os.environ.get(key)
            os.environ.update(env_vars)

        try:
            # Create node lookup
            node_map = {node["id"]: node for node in nodes}

            # Build edge lookup for getting inputs
            incoming_edges = defaultdict(list)
            for edge in edges:
                incoming_edges[edge["target"]].append(edge)

            # Topologically sort nodes
            sorted_node_ids = self.topological_sort(nodes, edges)

            # Store execution results
            node_outputs = {}
            view_node_results = {}

            # Execute nodes in order
            for idx, node_id in enumerate(sorted_node_ids):
                node = node_map[node_id]
                node_type = node.get("type", "default")
                node_number = idx + 1  # 1-indexed

                if node_type == "viewNode":
                    # Get node name
                    node_name = node.get("data", {}).get("label", "View")

                    # Gather inputs
                    inputs = {}
                    incoming = incoming_edges.get(node_id, [])
                    if incoming:
                        edge = incoming[0]  # ViewNode has single input
                        source_id = edge["source"]
                        source_handle = edge.get("sourceHandle", "output")
                        if source_id in node_outputs:
                            # Use helper to extract value (handles AnnotatedDict outputs)
                            inputs["input"] = _extract_output_value(
                                node_outputs, source_id, source_handle
                            )

                    # Yield executing status
                    yield {
                        "node_id": node_id,
                        "node_number": node_number,
                        "node_name": node_name,
                        "status": "executing",
                        "inputs": inputs,
                    }

                    # ViewNode: get input value and store it
                    if incoming:
                        edge = incoming[0]
                        source_id = edge["source"]
                        source_handle = edge.get("sourceHandle", "output")

                        if source_id in node_outputs:
                            # Use helper to extract value (handles AnnotatedDict outputs)
                            output = _extract_output_value(
                                node_outputs, source_id, source_handle
                            )
                            view_node_results[node_id] = output
                        else:
                            view_node_results[node_id] = None
                            output = None
                    else:
                        view_node_results[node_id] = None
                        output = None

                    # Yield completed status
                    yield {
                        "node_id": node_id,
                        "node_number": node_number,
                        "node_name": node_name,
                        "status": "completed",
                        "inputs": inputs,
                        "output": output,
                    }

                elif node_type == "variableNode":
                    # Variable node: output the stored value
                    node_data = node.get("data", {})
                    node_name = node_data.get("label", "Variable")
                    variable_value = node_data.get("variableValue")
                    variable_type = node_data.get("variableType", "String")
                    text_content_format = node_data.get("textContentFormat", False)
                    image_content_format = node_data.get("imageContentFormat", False)
                    llm_message_format = node_data.get("llmMessageFormat", False)
                    llm_message_role = node_data.get("llmMessageRole", "user")

                    # Yield executing status
                    yield {
                        "node_id": node_id,
                        "node_number": node_number,
                        "node_name": node_name,
                        "status": "executing",
                        "inputs": {},
                    }

                    # Convert value based on type
                    if variable_type == "Number":
                        try:
                            if isinstance(variable_value, (int, float)):
                                output = variable_value
                            elif isinstance(variable_value, str):
                                # Try to parse as int first, then float
                                if "." in variable_value:
                                    output = float(variable_value)
                                else:
                                    output = int(variable_value)
                            else:
                                output = 0
                        except (ValueError, TypeError):
                            output = 0
                    elif variable_type == "Boolean":
                        if isinstance(variable_value, bool):
                            output = variable_value
                        elif isinstance(variable_value, str):
                            output = variable_value.lower() in ("true", "1", "yes")
                        else:
                            output = bool(variable_value)
                    elif variable_type == "List":
                        # Output as Python list
                        if isinstance(variable_value, list):
                            output = variable_value
                        else:
                            output = []
                    elif variable_type == "Object":
                        # Parse JSON string to dict or use as-is if already a dict
                        if isinstance(variable_value, dict):
                            output = variable_value
                        elif isinstance(variable_value, str):
                            try:
                                import json

                                output = json.loads(variable_value)
                            except json.JSONDecodeError:
                                output = {}
                        else:
                            output = {}
                    elif variable_type == "Image":
                        # Output image data URL
                        output_data_url = (
                            str(variable_value) if variable_value is not None else ""
                        )
                        # Apply LLM Message format if enabled (complete message with role and content array)
                        if llm_message_format:
                            output = {
                                "role": llm_message_role,
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": output_data_url},
                                    }
                                ],
                            }
                        else:
                            output = output_data_url
                    else:  # String
                        output_string = (
                            str(variable_value) if variable_value is not None else ""
                        )
                        # Apply LLM Message format if enabled (takes precedence)
                        if llm_message_format:
                            output = {
                                "role": llm_message_role,
                                "content": output_string,
                            }
                        # Apply LLM Message Content if enabled (legacy)
                        elif text_content_format:
                            output = {
                                "type": "text",
                                "content": output_string,
                            }
                        else:
                            output = output_string

                    node_outputs[node_id] = output

                    # Yield completed status
                    yield {
                        "node_id": node_id,
                        "node_number": node_number,
                        "node_name": node_name,
                        "status": "completed",
                        "inputs": {},
                        "output": output,
                    }

                elif node_type == "listNode":
                    # List node: collect values from all connected inputs
                    node_data = node.get("data", {})
                    node_name = node_data.get("label", "List")

                    # Gather inputs
                    incoming = incoming_edges.get(node_id, [])

                    # Sort by input index (from targetHandle like "input-0", "input-1")
                    def get_input_index(edge):
                        target_handle = edge.get("targetHandle", "input-0")
                        try:
                            return int(target_handle.split("-")[1])
                        except (IndexError, ValueError):
                            return 0

                    sorted_edges = sorted(incoming, key=get_input_index)

                    # Build inputs dict for status
                    inputs = {}
                    for idx, edge in enumerate(sorted_edges):
                        source_id = edge["source"]
                        source_handle = edge.get("sourceHandle", "output")
                        if source_id in node_outputs:
                            # Use helper to extract value (handles AnnotatedDict outputs)
                            inputs[f"input-{idx}"] = _extract_output_value(
                                node_outputs, source_id, source_handle
                            )

                    # Yield executing status
                    yield {
                        "node_id": node_id,
                        "node_number": node_number,
                        "node_name": node_name,
                        "status": "executing",
                        "inputs": inputs,
                    }

                    # Build list from connected outputs
                    output_list = []
                    for edge in sorted_edges:
                        source_id = edge["source"]
                        source_handle = edge.get("sourceHandle", "output")
                        if source_id in node_outputs:
                            # Use helper to extract value (handles AnnotatedDict outputs)
                            output_list.append(
                                _extract_output_value(
                                    node_outputs, source_id, source_handle
                                )
                            )

                    node_outputs[node_id] = output_list

                    # Yield completed status
                    yield {
                        "node_id": node_id,
                        "node_number": node_number,
                        "node_name": node_name,
                        "status": "completed",
                        "inputs": inputs,
                        "output": output_list,
                    }

                else:
                    # Function node: execute the function, progress class, or stream class
                    function_name = node.get("data", {}).get("functionName")
                    node_name = node.get("data", {}).get(
                        "label", function_name or "Unknown"
                    )

                    # Check if it's a progress class, stream class, or regular function
                    is_progress_node = function_name in self.progress_class_registry
                    is_stream_node = function_name in self.stream_class_registry

                    if not function_name:
                        continue

                    if (
                        not is_progress_node
                        and not is_stream_node
                        and function_name not in self.function_registry
                    ):
                        continue

                    # Get the callable (function or class)
                    if is_progress_node:
                        progress_class = self.progress_class_registry[function_name]
                        # Get signature from __call__ method
                        sig = inspect.signature(progress_class.__call__)
                        # Filter out 'self' parameter
                        param_names = [p for p in sig.parameters.keys() if p != "self"]
                    elif is_stream_node:
                        stream_class = self.stream_class_registry[function_name]
                        # Get signature from __call__ method
                        sig = inspect.signature(stream_class.__call__)
                        # Filter out 'self' parameter
                        param_names = [p for p in sig.parameters.keys() if p != "self"]
                    else:
                        func = self.function_registry[function_name]
                        sig = inspect.signature(func)
                        param_names = list(sig.parameters.keys())

                    # Gather inputs
                    node_data = node.get("data", {})
                    inputs = {}

                    # First, use default values from node data
                    for param_name in param_names:
                        if param_name in node_data:
                            inputs[param_name] = node_data[param_name]

                    # Then, override with values from connected edges
                    for edge in incoming_edges.get(node_id, []):
                        target_handle = edge.get("targetHandle", "")
                        source_id = edge["source"]
                        source_handle = edge.get("sourceHandle", "output")

                        if source_id in node_outputs:
                            # The target handle should indicate which parameter to set
                            if target_handle in param_names:
                                # Use helper to extract value (handles AnnotatedDict outputs)
                                inputs[target_handle] = _extract_output_value(
                                    node_outputs, source_id, source_handle
                                )

                    # Yield executing status
                    yield {
                        "node_id": node_id,
                        "node_number": node_number,
                        "node_name": node_name,
                        "status": "executing",
                        "inputs": inputs,
                    }

                    # Execute function, progress class, or stream class
                    try:
                        # Convert string inputs to appropriate types if needed
                        type_hints = {}
                        try:
                            from typing import get_type_hints

                            if is_progress_node:
                                type_hints = get_type_hints(progress_class.__call__)
                            elif is_stream_node:
                                type_hints = get_type_hints(stream_class.__call__)
                            else:
                                type_hints = get_type_hints(func)
                        except:
                            pass

                        converted_inputs = {}
                        for param_name, value in inputs.items():
                            if param_name in type_hints:
                                param_type = type_hints[param_name]
                                if param_type == float and not isinstance(value, float):
                                    converted_inputs[param_name] = float(value)
                                elif param_type == int and not isinstance(
                                    value, (int, bool)
                                ):
                                    converted_inputs[param_name] = int(value)
                                elif param_type == str and not isinstance(value, str):
                                    converted_inputs[param_name] = str(value)
                                elif param_type == bool and not isinstance(value, bool):
                                    converted_inputs[param_name] = bool(value)
                                else:
                                    converted_inputs[param_name] = value
                            else:
                                converted_inputs[param_name] = value

                        if is_progress_node:
                            # Execute progress node with threading and progress updates
                            progress_queue = queue.Queue()
                            result_container = []
                            error_container = []

                            # Instantiate the progress class
                            instance = progress_class()

                            # Set up progress callback
                            def progress_callback(percent: float, message: str):
                                progress_queue.put(
                                    {
                                        "node_id": node_id,
                                        "node_number": node_number,
                                        "node_name": node_name,
                                        "status": "progress",
                                        "progress": percent,
                                        "progress_message": message,
                                        "inputs": inputs,
                                    }
                                )

                            # Access the _progress_reporter and set callback
                            if hasattr(instance, "_progress_reporter"):
                                instance._progress_reporter.set_callback(
                                    progress_callback
                                )

                            # Execute in a separate thread
                            def execute_with_progress():
                                try:
                                    result = instance(**converted_inputs)
                                    result_container.append(result)
                                except Exception as e:
                                    error_container.append(e)

                            exec_thread = threading.Thread(target=execute_with_progress)
                            exec_thread.start()

                            # Yield progress updates while executing
                            while exec_thread.is_alive():
                                try:
                                    progress_update = progress_queue.get(timeout=0.1)
                                    yield progress_update
                                except queue.Empty:
                                    pass

                            exec_thread.join()

                            # Drain remaining progress updates
                            while not progress_queue.empty():
                                yield progress_queue.get()

                            # Handle result or error
                            if error_container:
                                error_msg = str(error_container[0])
                                print(
                                    f"Error executing node {node_id} ({function_name}): {error_container[0]}"
                                )
                                node_outputs[node_id] = None

                                # Yield error status
                                yield {
                                    "node_id": node_id,
                                    "node_number": node_number,
                                    "node_name": node_name,
                                    "status": "error",
                                    "inputs": inputs,
                                    "error": error_msg,
                                }
                            else:
                                result = (
                                    result_container[0] if result_container else None
                                )
                                node_outputs[node_id] = result

                                # Yield completed status
                                yield {
                                    "node_id": node_id,
                                    "node_number": node_number,
                                    "node_name": node_name,
                                    "status": "completed",
                                    "inputs": inputs,
                                    "output": result,
                                }
                        elif is_stream_node:
                            # Execute stream node with threading and streaming updates
                            stream_queue = queue.Queue()
                            result_container = []
                            error_container = []
                            accumulated_text = []

                            # Instantiate the stream class
                            instance = stream_class()

                            # Set up stream callback
                            def stream_callback(chunk: str):
                                accumulated_text.append(chunk)
                                stream_queue.put(
                                    {
                                        "node_id": node_id,
                                        "node_number": node_number,
                                        "node_name": node_name,
                                        "status": "streaming",
                                        "streaming_text": "".join(accumulated_text),
                                        "streaming_chunk": chunk,
                                        "inputs": inputs,
                                    }
                                )

                            # Access the _stream_reporter and set callback
                            if hasattr(instance, "_stream_reporter"):
                                instance._stream_reporter.set_callback(stream_callback)

                            # Execute in a separate thread
                            def execute_with_stream():
                                try:
                                    result = instance(**converted_inputs)
                                    result_container.append(result)
                                except Exception as e:
                                    error_container.append(e)

                            exec_thread = threading.Thread(target=execute_with_stream)
                            exec_thread.start()

                            # Yield stream updates while executing
                            while exec_thread.is_alive():
                                try:
                                    stream_update = stream_queue.get(timeout=0.1)
                                    yield stream_update
                                except queue.Empty:
                                    pass

                            exec_thread.join()

                            # Drain remaining stream updates
                            while not stream_queue.empty():
                                yield stream_queue.get()

                            # Handle result or error
                            if error_container:
                                error_msg = str(error_container[0])
                                print(
                                    f"Error executing node {node_id} ({function_name}): {error_container[0]}"
                                )
                                node_outputs[node_id] = None

                                # Yield error status
                                yield {
                                    "node_id": node_id,
                                    "node_number": node_number,
                                    "node_name": node_name,
                                    "status": "error",
                                    "inputs": inputs,
                                    "error": error_msg,
                                }
                            else:
                                result = (
                                    result_container[0] if result_container else None
                                )
                                node_outputs[node_id] = result

                                # Yield completed status
                                yield {
                                    "node_id": node_id,
                                    "node_number": node_number,
                                    "node_name": node_name,
                                    "status": "completed",
                                    "inputs": inputs,
                                    "output": result,
                                }
                        else:
                            # Execute regular function
                            result = func(**converted_inputs)
                            node_outputs[node_id] = result

                            # Yield completed status
                            yield {
                                "node_id": node_id,
                                "node_number": node_number,
                                "node_name": node_name,
                                "status": "completed",
                                "inputs": inputs,
                                "output": result,
                            }

                    except Exception as e:
                        error_msg = str(e)
                        print(f"Error executing node {node_id} ({function_name}): {e}")
                        node_outputs[node_id] = None

                        # Yield error status
                        yield {
                            "node_id": node_id,
                            "node_number": node_number,
                            "node_name": node_name,
                            "status": "error",
                            "inputs": inputs,
                            "error": error_msg,
                        }

            # Yield final results
            yield {
                "status": "done",
                "results": view_node_results,
            }
        finally:
            # Restore original environment variables
            if env_vars:
                for key, value in original_env.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
