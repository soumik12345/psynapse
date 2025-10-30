# Psynapse Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (PySide6)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐     │
│  │   Editor     │   │  Node View   │   │  Library     │     │
│  │              │───│              │   │  Panel       │     │
│  │  - Run Btn   │   │  - Canvas    │   │              │     │
│  │  - Status    │   │  - Sockets   │   │  - Drag Node │     │
│  └──────────────┘   └──────────────┘   └──────────────┘     │
│         │                                                   │
│         │ (1) User clicks "Run"                             │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────┐           │
│  │         Graph Serializer                     │           │
│  │  - Converts UI nodes to JSON                 │           │
│  │  - Maps node types                           │           │
│  │  - Serializes edges                          │           │
│  └──────────────────────────────────────────────┘           │
│         │                                                   │
│         │ (2) Serialized graph JSON                         │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────┐           │
│  │         Backend Client                       │           │
│  │  - HTTP communication                        │           │
│  │  - Health checks                             │           │
│  │  - Error handling                            │           │
│  └──────────────────────────────────────────────┘           │
│         │                                                   │
└─────────┼───────────────────────────────────────────────────┘
          │
          │ (3) POST /execute
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────┐           │
│  │              FastAPI Server                  │           │
│  │                                              │           │
│  │  GET  /nodes     → Node Schemas              │           │
│  │  POST /execute   → Graph Execution           │           │
│  │  GET  /health    → Health Check              │           │
│  └──────────────────────────────────────────────┘           │
│         │                                                   │
│         │ (4) Receive graph                                 │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────┐           │
│  │           Graph Executor                     │           │
│  │  - Parse nodes and edges                     │           │
│  │  - Resolve dependencies                      │           │
│  │  - Execute operations                        │           │
│  │  - Cache results                             │           │
│  └──────────────────────────────────────────────┘           │
│         │                                                   │
│         │ (5) Compute results                               │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────┐           │
│  │           Node Operations                    │           │
│  │  - Add, Subtract, Multiply, Divide           │           │
│  │  - Type checking                             │           │
│  │  - Error handling                            │           │
│  └──────────────────────────────────────────────┘           │
│         │                                                   │
└─────────┼───────────────────────────────────────────────────┘
          │
          │ (6) Return results JSON
          │     { "results": { "node_1": {"value": 8.0} } }
          ▼
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (PySide6)                   │
├─────────────────────────────────────────────────────────────┤
│         │                                                   │
│         │ (7) Receive results                               │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────┐           │
│  │         Result Handler                       │           │
│  │  - Map results to ViewNodes                  │           │
│  │  - Update displays                           │           │
│  │  - Show errors                               │           │
│  └──────────────────────────────────────────────┘           │
│         │                                                   │
│         │ (8) Update UI                                     │
│         ▼                                                   │
│  ┌──────────────┐                                           │
│  │  ViewNodes   │                                           │
│  │  show values │                                           │
│  └──────────────┘                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Frontend (PySide6)

#### Editor (`editor.py`)
- Main application window
- Manages node library and canvas
- Coordinates execution via Run button
- Displays status and errors

#### Node View (`view.py`)
- Interactive canvas for node graph
- Handles pan, zoom, and connections
- Drag-and-drop support

#### Serializer (`serializer.py`)
- Converts UI graph to JSON
- Maps node classes to backend types
- Serializes sockets and connections

#### Backend Client (`backend_client.py`)
- HTTP client for FastAPI backend
- Async/sync method wrappers
- Connection health checks

### Backend (FastAPI)

#### Server (`server.py`)
- REST API endpoints
- CORS configuration
- Request validation

#### Node Schemas (`node_schemas.py`)
- Defines available node types
- Specifies parameters and returns
- Type information

#### Executor (`executor.py`)
- Graph execution engine
- Dependency resolution
- Result caching
- Error handling

## Data Flow

### Graph Serialization

**Input (UI Nodes):**
```python
nodes = [AddNode(), ViewNode()]
# AddNode has inputs A=5.0, B=3.0
# ViewNode connected to AddNode output
```

**Output (JSON):**
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

### Execution Results

**Backend Response:**
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

**Frontend Processing:**

- Maps `node_1` → second ViewNode in graph

- Updates ViewNode display to show `8.0`

- Clears any error state
