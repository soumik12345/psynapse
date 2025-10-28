# Psynapse Backend

The Psynapse backend is a FastAPI server that handles node graph execution. This decouples the compute from the UI, allowing for more scalable and testable node execution.

## Architecture

### Components

1. **FastAPI Server** (`psynapse/backend/server.py`)
   - Provides REST API endpoints for node operations
   - Handles graph execution requests

2. **Node Schemas** (`psynapse/backend/node_schemas.py`)
   - Defines the schema for available nodes
   - Specifies parameters and return types for each node

3. **Graph Executor** (`psynapse/backend/executor.py`)
   - Executes node graphs
   - Manages node dependencies and caching
   - Returns results for ViewNodes

### Frontend Integration

1. **Graph Serializer** (`psynapse/core/serializer.py`)
   - Converts the UI node graph to a JSON format
   - Serializes nodes and edges for backend consumption

2. **Backend Client** (`psynapse/editor/backend_client.py`)
   - HTTP client for communicating with the backend
   - Provides sync wrappers for async operations

## API Endpoints

### GET `/nodes`

Returns the schema of all available nodes.

**Response:**
```json
{
  "nodes": [
    {
      "name": "add",
      "params": [
        {"name": "a", "type": "float"},
        {"name": "b", "type": "float"}
      ],
      "returns": [
        {"name": "result", "type": "float"}
      ]
    }
  ]
}
```

### POST `/execute`

Executes a node graph and returns results.

**Request:**
```json
{
  "nodes": [
    {
      "id": "node_0",
      "type": "add",
      "input_sockets": [
        {"id": "node_0_input_0", "name": "a", "value": 5.0},
        {"id": "node_0_input_1", "name": "b", "value": 3.0}
      ],
      "output_sockets": [
        {"id": "node_0_output_0", "name": "result"}
      ]
    },
    {
      "id": "node_1",
      "type": "view",
      "input_sockets": [
        {"id": "node_1_input_0", "name": "value", "value": null}
      ],
      "output_sockets": []
    }
  ],
  "edges": [
    {
      "start_socket": "node_0_output_0",
      "end_socket": "node_1_input_0"
    }
  ]
}
```

**Response:**
```json
{
  "results": {
    "node_1": {
      "value": 8.0,
      "error": null
    }
  }
}
```

### GET `/health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

## Running the Backend

### Method 1: Using the helper script

```bash
uv run python start_backend.py
```

### Method 2: Using uvicorn directly

```bash
uvicorn psynapse.backend.server:app --reload
```

### Method 3: Using uvicorn with custom host/port

```bash
uvicorn psynapse.backend.server:app --reload --host 0.0.0.0 --port 8000
```

## Usage Workflow

1. **Start the backend server**
   ```bash
   uv run python start_backend.py
   ```

2. **Launch the Psynapse editor**
   ```bash
   uv run psynapse
   ```

3. **Build your node graph**
   - Drag nodes from the library panel
   - Connect nodes by dragging from output to input sockets

4. **Execute the graph**
   - Click the "▶ Run Graph" button
   - The frontend will serialize the graph and send it to the backend
   - Results will be displayed in ViewNodes

## Development

### Adding New Node Types

To add a new node type:

1. **Add the node schema** in `psynapse/backend/node_schemas.py`:
   ```python
   {
       "name": "new_node",
       "params": [
           {"name": "param1", "type": "float"},
       ],
       "returns": [
           {"name": "result", "type": "float"},
       ],
   }
   ```

2. **Implement the execution logic** in `psynapse/backend/executor.py`:
   ```python
   elif node_type == "new_node":
       param1 = float(inputs.get("param1", 0.0))
       return some_computation(param1)
   ```

3. **Create the frontend node class** in `psynapse/nodes/`:
   ```python
   class NewNode(Node):
       def __init__(self):
           super().__init__(
               title="New Node",
               inputs=[("Param1", SocketDataType.FLOAT)],
               outputs=[("Result", SocketDataType.FLOAT)],
           )
   ```

4. **Register the node** in the serializer mapping (`psynapse/core/serializer.py`):
   ```python
   NODE_TYPE_MAP = {
       NewNode: "new_node",
       # ... other nodes
   }
   ```

## Testing

Test the backend endpoints using curl or any HTTP client:

```bash
# Health check
curl http://localhost:8000/health

# Get node schemas
curl http://localhost:8000/nodes

# Execute a graph
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"nodes": [...], "edges": [...]}'
```

