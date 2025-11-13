"""Graph execution engine for the backend."""

import base64
import importlib.util
import os
import re
import sys
import typing
from collections import deque
from io import BytesIO
from typing import Any, Callable, Dict, Generator, List, Optional

import pydantic
import requests
import rich
from PIL import Image

from psynapse.backend.node_schemas import get_node_schema
from psynapse.utils import pil_image_to_openai_string

# Global cache for loaded functions from nodepacks
_FUNCTION_CACHE: Dict[str, Callable] = {}

# Global variable to track the current node being executed
_CURRENT_NODE_INFO: Optional[Dict[str, str]] = None


def get_current_node() -> Optional[Dict[str, str]]:
    """Get information about the currently executing node.

    Returns:
        Dictionary with 'node_id' and 'node_type' or None if no execution in progress
    """
    return _CURRENT_NODE_INFO


def set_current_node(node_id: str, node_type: str):
    """Set the currently executing node.

    Args:
        node_id: ID of the node being executed
        node_type: Type of the node being executed
    """
    global _CURRENT_NODE_INFO
    _CURRENT_NODE_INFO = {"node_id": node_id, "node_type": node_type}


def clear_current_node():
    """Clear the current node info (execution completed)."""
    global _CURRENT_NODE_INFO
    _CURRENT_NODE_INFO = None


class GraphExecutor:
    """Executes a node graph and returns results."""

    def __init__(self, graph_data: Dict[str, Any], env_vars: Dict[str, str] = None):
        """Initialize executor with graph data.

        Args:
            graph_data: Dictionary containing:
                - nodes: List of node definitions with id, type, and params
                - edges: List of connections between nodes
            env_vars: Optional environment variables to set during execution
        """
        self.nodes = graph_data.get("nodes", [])
        self.edges = graph_data.get("edges", [])
        self.node_cache = {}  # Cache for node execution results
        self.env_vars = env_vars or {}
        # Build node lookup map for faster access
        self.node_map = {node["id"]: node for node in self.nodes}

    def execute(self) -> Dict[str, Any]:
        """Execute the graph using topological sort and return results for ViewNodes.

        Returns:
            Dictionary mapping view node IDs to their computed values
        """
        # Clear cache for fresh execution
        self.node_cache = {}

        # Save current environment variables and set new ones
        original_env = {}
        for key, value in self.env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
            print(
                f"[Executor] Set environment variable: {key} = {'*' * min(len(value), 8)}"
            )

        try:
            # Perform topological sort to get execution order
            sorted_nodes = self._topological_sort()

            # Execute nodes in topologically sorted order
            for node_id in sorted_nodes:
                # Get node info for tracking
                node = self.node_map.get(node_id)
                node_type = node.get("type", "unknown") if node else "unknown"

                # Set current node info
                set_current_node(node_id, node_type)

                rich.print(f"[Executor] Executing node: {node_id}")
                self._execute_node(node_id)

            # Clear current node info when execution completes
            clear_current_node()

            # Collect results for view nodes
            results = {}
            view_node_ids = [
                node["id"] for node in self.nodes if node["type"] == "view"
            ]
            for view_node_id in view_node_ids:
                if view_node_id in self.node_cache:
                    results[view_node_id] = {
                        "value": self.node_cache[view_node_id],
                        "error": None,
                    }
                else:
                    results[view_node_id] = {
                        "value": None,
                        "error": "Node not executed",
                    }

            return results

        except Exception as e:
            # Clear current node info on error
            clear_current_node()

            # If there's an error (like a cycle), return error for all view nodes
            view_node_ids = [
                node["id"] for node in self.nodes if node["type"] == "view"
            ]
            results = {}
            for view_node_id in view_node_ids:
                results[view_node_id] = {"value": None, "error": str(e)}
            return results

        finally:
            # Restore original environment variables
            for key, original_value in original_env.items():
                if original_value is None:
                    # Variable didn't exist before, remove it
                    os.environ.pop(key, None)
                else:
                    # Restore original value
                    os.environ[key] = original_value

    def execute_with_progress(self) -> Generator[Dict[str, Any], None, None]:
        """Execute the graph and yield progress updates.

        Yields:
            Progress dictionaries with:
                - event: 'progress', 'complete', or 'error'
                - node_id: ID of current node being executed (for 'progress' events)
                - node_type: Type of current node (for 'progress' events)
                - results: Final results (for 'complete' event)
                - error: Error message (for 'error' event)
        """
        # Clear cache for fresh execution
        self.node_cache = {}

        # Save current environment variables and set new ones
        original_env = {}
        for key, value in self.env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
            print(
                f"[Executor] Set environment variable: {key} = {'*' * min(len(value), 8)}"
            )

        try:
            # Perform topological sort to get execution order
            sorted_nodes = self._topological_sort()

            # Execute nodes in topologically sorted order
            for node_id in sorted_nodes:
                # Get node info for progress update
                node = self.node_map.get(node_id)
                node_type = node.get("type", "unknown") if node else "unknown"

                # Set current node info
                set_current_node(node_id, node_type)

                # Yield progress update
                yield {
                    "event": "progress",
                    "node_id": node_id,
                    "node_type": node_type,
                }

                rich.print(f"[Executor] Executing node: {node_id}")
                self._execute_node(node_id)

            # Collect results for view nodes
            results = {}
            view_node_ids = [
                node["id"] for node in self.nodes if node["type"] == "view"
            ]
            for view_node_id in view_node_ids:
                if view_node_id in self.node_cache:
                    results[view_node_id] = {
                        "value": self.node_cache[view_node_id],
                        "error": None,
                    }
                else:
                    results[view_node_id] = {
                        "value": None,
                        "error": "Node not executed",
                    }

            # Clear current node info when execution completes
            clear_current_node()

            # Yield completion
            yield {"event": "complete", "results": results}

        except Exception as e:
            # Clear current node info on error
            clear_current_node()

            # If there's an error, yield error event
            view_node_ids = [
                node["id"] for node in self.nodes if node["type"] == "view"
            ]
            results = {}
            for view_node_id in view_node_ids:
                results[view_node_id] = {"value": None, "error": str(e)}

            yield {"event": "error", "error": str(e), "results": results}

        finally:
            # Restore original environment variables
            for key, original_value in original_env.items():
                if original_value is None:
                    # Variable didn't exist before, remove it
                    os.environ.pop(key, None)
                else:
                    # Restore original value
                    os.environ[key] = original_value

    def _topological_sort(self) -> List[str]:
        """Perform topological sort using Kahn's algorithm.

        Returns:
            List of node IDs in topologically sorted order

        Raises:
            ValueError: If the graph contains a cycle
        """
        # Build adjacency list and in-degree count
        adjacency = {node["id"]: [] for node in self.nodes}
        in_degree = {node["id"]: 0 for node in self.nodes}

        # Build the graph structure based on socket connections
        for edge in self.edges:
            # Find source and target nodes
            source_node_id = self._find_node_by_socket(edge["start_socket"], "output")
            target_node_id = self._find_node_by_socket(edge["end_socket"], "input")

            if source_node_id and target_node_id:
                adjacency[source_node_id].append(target_node_id)
                in_degree[target_node_id] += 1

        # Initialize queue with nodes having no dependencies (in-degree = 0)
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        sorted_order = []

        # Process nodes in topological order
        while queue:
            node_id = queue.popleft()
            sorted_order.append(node_id)

            # Reduce in-degree for dependent nodes
            for neighbor in adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check if all nodes were processed (no cycle)
        if len(sorted_order) != len(self.nodes):
            raise ValueError(
                "Graph contains a cycle - topological sort is not possible"
            )

        return sorted_order

    def _find_node_by_socket(self, socket_id: str, socket_type: str) -> str:
        """Find the node ID that owns a given socket.

        Args:
            socket_id: ID of the socket
            socket_type: Either 'input' or 'output'

        Returns:
            Node ID or None if not found
        """
        socket_key = "input_sockets" if socket_type == "input" else "output_sockets"

        for node in self.nodes:
            for socket in node.get(socket_key, []):
                if socket["id"] == socket_id:
                    return node["id"]
        return None

    def _execute_node(self, node_id: str) -> Any:
        """Execute a single node and cache its result.

        Args:
            node_id: ID of the node to execute

        Returns:
            Result value from node execution
        """
        # Check cache first
        if node_id in self.node_cache:
            return self.node_cache[node_id]

        # Find node definition
        node = self.node_map.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")

        # Special handling for TextNode - it has text content and return_as option
        if node["type"] == "text":
            params = node.get("params", {})
            return_as = params.get("return_as", "String")

            # Get the text value from output socket
            output_sockets = node.get("output_sockets", [])
            if output_sockets and "value" in output_sockets[0]:
                text_value = output_sockets[0]["value"]
            else:
                text_value = ""

            # Return in the selected format
            if return_as == "String":
                result = text_value
            elif return_as == "OpenAI LLM Content":
                result = {
                    "type": "input_text",
                    "text": text_value,
                }
            elif return_as == "LiteLLM Content":
                result = {
                    "type": "text",
                    "text": text_value,
                }
            else:
                result = text_value

            self.node_cache[node_id] = result
            return result

        # Special handling for ObjectNode - it has a preset output value
        if node["type"] == "object":
            # ObjectNode has no inputs, just return its output value
            output_sockets = node.get("output_sockets", [])
            if output_sockets and "value" in output_sockets[0]:
                result = output_sockets[0]["value"]
            else:
                result = None
            self.node_cache[node_id] = result
            return result

        # Special handling for ImageNode - loads an image from URL or file
        if node["type"] == "image":
            params = node.get("params", {})
            mode = params.get("mode", "URL")
            return_as = params.get("return_as", "PIL Image")

            try:
                # Load the image first
                image = None
                if mode == "URL":
                    url = params.get("url", "")
                    if url:
                        # Load image from URL
                        response = requests.get(url, timeout=10)
                        response.raise_for_status()
                        image = Image.open(BytesIO(response.content))
                else:  # mode == "Upload"
                    path = params.get("path", "")
                    if path and os.path.exists(path):
                        # Load image from file
                        image = Image.open(path)

                # Return in the selected format
                if image is None:
                    # Image loading failed
                    result = None
                elif return_as == "PIL Image":
                    # Serialize image as dict with base64 data (for backend transmission)
                    result = self._serialize_image(image)
                elif return_as == "OpenAI string":
                    # Return as OpenAI-compatible base64 string
                    result = pil_image_to_openai_string(image)
                elif return_as == "OpenAI LLM Content":
                    # Return as LLM content dictionary
                    result = {
                        "type": "input_image",
                        "image_url": pil_image_to_openai_string(image),
                    }
                elif return_as == "LiteLLM Content":
                    # Return as LiteLLM content dictionary
                    result = {
                        "type": "image_url",
                        "image_url": {"url": pil_image_to_openai_string(image)},
                    }
                else:
                    # Default to serialized image
                    result = self._serialize_image(image)
            except Exception as e:
                print(f"Error loading image: {e}")
                result = None

            self.node_cache[node_id] = result
            return result

        # Special handling for ListNode - it collects all inputs into a list
        if node["type"] == "list":
            # For ListNode, we need to collect inputs in order by socket index
            # since all sockets have the same name "item"
            result = []
            for socket in node.get("input_sockets", []):
                socket_id = socket["id"]

                # Find edge connected to this input socket
                connected_edge = None
                for edge in self.edges:
                    if edge["end_socket"] == socket_id:
                        connected_edge = edge
                        break

                if connected_edge:
                    # Find the source node
                    source_socket_id = connected_edge["start_socket"]
                    source_node_id = self._find_node_by_socket(
                        source_socket_id, "output"
                    )

                    if source_node_id and source_node_id in self.node_cache:
                        # Get the cached result from the source node
                        result.append(self.node_cache[source_node_id])
                    else:
                        # No connection or not in cache, use default value from socket
                        result.append(socket.get("value"))
                else:
                    # No connection, use default value from socket
                    result.append(socket.get("value"))

            self.node_cache[node_id] = result
            return result

        # Special handling for DictionaryNode - it has a preset output value
        if node["type"] == "dictionary":
            # DictionaryNode has no inputs, just return its output value
            output_sockets = node.get("output_sockets", [])
            if output_sockets and "value" in output_sockets[0]:
                result = output_sockets[0]["value"]
            else:
                result = {}
            self.node_cache[node_id] = result
            return result

        # Special handling for PydanticSchemaNode - recreate model from entries
        if node["type"] == "pydantic_schema":
            try:
                params = node.get("params", {})
                entries = params.get("entries", [])

                # Create a safe namespace with typing module contents and builtins
                # for parsing type strings
                safe_globals = {
                    "Any": Any,
                    "List": typing.List,
                    "Dict": typing.Dict,
                    "Optional": typing.Optional,
                    "Union": typing.Union,
                    "Tuple": typing.Tuple,
                    "Set": typing.Set,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                }

                def parse_type_string(type_str: str) -> type:
                    """Parse a type string into a Python type."""
                    if not type_str or not type_str.strip():
                        return str

                    type_str = type_str.strip()

                    try:
                        # Try to evaluate the type string
                        parsed_type = eval(type_str, safe_globals, {})
                        return parsed_type
                    except Exception:
                        # If parsing fails, default to str
                        return str

                schema_dict = {}
                for entry in entries:
                    field_name = entry.get("field", "").strip()
                    if field_name:
                        type_str = entry.get("type", "str")
                        python_type = parse_type_string(type_str)
                        default_value = entry.get("default_value")

                        # Format: { field_name: type } or { field_name: (type, default_value) }
                        if default_value is not None:
                            schema_dict[field_name] = (python_type, default_value)
                        else:
                            schema_dict[field_name] = python_type

                # Get schema name from params, default to "DynamicSchema"
                schema_name = params.get("schema_name", "DynamicSchema")
                if not schema_name or not schema_name.strip():
                    schema_name = "DynamicSchema"

                # Create Pydantic model with the custom schema name
                if schema_dict:
                    model_type = pydantic.create_model(schema_name, **schema_dict)
                else:
                    # Empty schema - create a model with no fields
                    model_type = pydantic.create_model(schema_name)

                # Serialize the model type as a special dict so frontend can identify it
                # We'll include the JSON schema so frontend can display it
                result = {
                    "__type__": "PydanticModelType",
                    "model_name": model_type.__name__,
                    "json_schema": model_type.model_json_schema(),
                }
                self.node_cache[node_id] = result
                return result
            except Exception as e:
                # If model creation fails, return None
                result = None
                self.node_cache[node_id] = result
                return result

        # Get input values from already-executed nodes (thanks to topological sort)
        inputs = self._get_node_inputs(node_id)

        # Get filepath from node data if available
        filepath = node.get("filepath")
        source_nodepack = node.get("source_nodepack")

        # Execute based on node type
        result = self._execute_node_operation(
            node["type"], inputs, filepath, source_nodepack
        )

        # Cache result
        self.node_cache[node_id] = result

        return result

    def _get_node_inputs(self, node_id: str) -> Dict[str, Any]:
        """Get input values for a node from the cache.

        Since we execute in topological order, all dependencies are already computed.

        Args:
            node_id: ID of the node to get inputs for

        Returns:
            Dictionary mapping input parameter names to their values
        """
        node = self.node_map.get(node_id)
        inputs = {}

        # Helper function to strip index from socket names (e.g., "NUMBERS [0]" -> "NUMBERS")
        def strip_socket_index(socket_name: str) -> str:
            """Strip index suffix from socket name if present."""
            # Match pattern like " [0]", " [1]", etc.
            match = re.match(r"^(.+?)\s*\[\d+\]$", socket_name)
            if match:
                return match.group(1)
            return socket_name

        # Get node schema to identify list-type parameters and map socket names to parameter names
        node_type = node.get("type")
        schema = None
        list_type_params = set()
        socket_to_param_name = {}  # Map socket names (uppercase) to schema parameter names (lowercase)

        # Only check schema for OpNode types (not special nodes like "text", "list", etc.)
        if node_type not in ["text", "list", "object", "image", "view", "dictionary"]:
            try:
                from psynapse.backend.node_schemas import get_node_schema

                schema = get_node_schema(node_type)
                if schema:
                    # Identify list-type parameters and create name mapping
                    for param in schema.get("params", []):
                        param_name_lower = param["name"].lower()
                        param_name_upper = param["name"].upper()

                        # Map both lowercase and uppercase socket names to schema parameter name
                        socket_to_param_name[param_name_lower] = param_name_lower
                        socket_to_param_name[param_name_upper] = param_name_lower

                        # Also map indexed versions (e.g., "NUMBERS [0]", "NUMBERS [1]")
                        # These will be handled by strip_socket_index, but we can pre-populate
                        # the mapping for common cases
                        for i in range(10):  # Support up to 10 indexed sockets
                            indexed_upper = f"{param_name_upper} [{i}]"
                            indexed_lower = f"{param_name_lower} [{i}]"
                            socket_to_param_name[indexed_upper] = param_name_lower
                            socket_to_param_name[indexed_lower] = param_name_lower

                        if param.get("type", "").lower() == "list":
                            list_type_params.add(param_name_lower)
                            list_type_params.add(param_name_upper)
            except Exception:
                # If schema lookup fails, continue without list-type detection
                pass

        # Track which parameters appear multiple times (variadic parameters)
        # Use schema parameter names for tracking
        param_counts = {}
        for socket in node.get("input_sockets", []):
            socket_param_name = socket["name"]
            # Strip index from socket name if present
            base_socket_name = strip_socket_index(socket_param_name)
            schema_param_name = socket_to_param_name.get(
                base_socket_name, base_socket_name
            )
            param_counts[schema_param_name] = param_counts.get(schema_param_name, 0) + 1

        # Track which parameters we've already processed
        param_lists = {}

        # For each input socket of this node
        for socket in node.get("input_sockets", []):
            socket_id = socket["id"]
            socket_param_name = socket["name"]

            # Strip index from socket name to get base parameter name
            base_socket_name = strip_socket_index(socket_param_name)

            # Find edge connected to this input socket
            connected_edge = None
            for edge in self.edges:
                if edge["end_socket"] == socket_id:
                    connected_edge = edge
                    break

            # Get the value for this socket
            if connected_edge:
                # Find the source node
                source_socket_id = connected_edge["start_socket"]
                source_node_id = self._find_node_by_socket(source_socket_id, "output")

                if source_node_id and source_node_id in self.node_cache:
                    # Get the cached result from the source node
                    value = self.node_cache[source_node_id]
                else:
                    # No connection or not in cache, use default value from socket
                    value = socket.get("value")
            else:
                # No connection, use default value from socket
                value = socket.get("value")

            # Map socket name to schema parameter name (use lowercase from schema)
            schema_param_name = socket_to_param_name.get(
                base_socket_name, base_socket_name
            )

            # Check if this is a list-type parameter (case-insensitive)
            is_list_type = (
                base_socket_name.lower() in list_type_params
                or base_socket_name.upper() in list_type_params
            )

            # If this parameter appears multiple times OR is a list-type parameter,
            # collect values into a list
            if param_counts[schema_param_name] > 1 or is_list_type:
                # Use schema parameter name for the list
                if schema_param_name not in param_lists:
                    param_lists[schema_param_name] = []
                param_lists[schema_param_name].append(value)
            else:
                # Single occurrence, use schema parameter name
                inputs[schema_param_name] = value

        # Add collected lists to inputs
        inputs.update(param_lists)

        return inputs

    def _execute_node_operation(
        self,
        node_type: str,
        inputs: Dict[str, Any],
        filepath: str = None,
        source_nodepack: str = None,
    ) -> Any:
        """Execute a node's operation based on its type.

        Args:
            node_type: Type of node (e.g., add, subtract, multiply, divide, view)
            inputs: Dictionary of input values
            filepath: Optional filepath to the node's implementation (if not provided, will be looked up)
            source_nodepack: Optional source nodepack name (if not provided, will be looked up)
        Returns:
            Result of the operation
        """
        # Special handling for view node
        if node_type == "view":
            # View node just passes through its input
            return inputs.get("value")

        # Check if function is already cached
        if node_type in _FUNCTION_CACHE:
            func = _FUNCTION_CACHE[node_type]
            return func(**inputs)

        # Get filepath - use provided filepath or look it up from schema
        if not filepath:
            # Get the node schema from nodepacks
            schema = get_node_schema(node_type)
            if not schema:
                raise ValueError(f"Unknown node type: {node_type}")
            filepath = schema["filepath"]

        # Create a unique module name based on the filepath
        module_name = f"nodepack_{filepath.replace('/', '_').replace('.', '_')}"

        # Check if module is already loaded
        if module_name in sys.modules:
            module = sys.modules[module_name]
        else:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None or spec.loader is None:
                raise ValueError(f"Could not load module from {filepath}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

        # Get the function from the module
        if not hasattr(module, node_type):
            raise ValueError(f"Function {node_type} not found in {filepath}")

        func = getattr(module, node_type)

        # Cache the function for future use
        _FUNCTION_CACHE[node_type] = func

        # Call the function with the inputs
        return func(**inputs)

    def _serialize_image(self, image: Image.Image) -> Dict[str, Any]:
        """Serialize a PIL Image to a dictionary with base64 encoded data.

        Args:
            image: PIL Image object

        Returns:
            Dictionary with image metadata and base64 encoded data
        """
        # Convert image to bytes
        buffer = BytesIO()
        # Save as PNG to preserve quality and support transparency
        image.save(buffer, format="PNG")
        buffer.seek(0)

        # Encode as base64
        image_data = base64.b64encode(buffer.read()).decode("utf-8")

        return {
            "__type__": "PIL.Image",
            "format": "PNG",
            "mode": image.mode,
            "size": image.size,
            "data": image_data,
        }
