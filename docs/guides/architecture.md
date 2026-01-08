# Psynapse Architecture Documentation

## Overview

Psynapse is a full-stack node-based workflow editor that enables visual programming through a drag-and-drop interface. The system consists of three main components:

1. **Backend (FastAPI)**: Handles schema extraction from Python functions and executes node graphs
2. **Frontend (React + React Flow)**: Provides visual node graph editor with drag-and-drop functionality
3. **Nodepacks**: Python modules containing executable functions

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       Frontend (React)                           │
│  ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌──────────────┐    │
│  │   Node   │  │   Canvas   │  │  Execute │  │    Status    │    │
│  │ Library  │  │(ReactFlow) │  │  Button  │  │    Panel     │    │
│  │  Panel   │  │            │  │          │  │ (Real-time)  │    │
│  └──────────┘  └────────────┘  └──────────┘  └──────────────┘    │
└──────────────────────┬────────────────────────┬──────────────────┘
                       │ HTTP/REST              │ SSE (Streaming)
                       ↓                        ↓
┌──────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌──────────────┐  ┌───────────┐  ┌──────────────────────────┐   │
│  │ /get_schema  │  │ /execute  │  │ /execute/stream          │   │
│  │  Endpoint    │  │ Endpoint  │  │ Endpoint (SSE)           │   │
│  └──────┬───────┘  └─────┬─────┘  └──────────┬───────────────┘   │
│         │                │                    │                  │
│  ┌──────▼──────┐  ┌──────▼───────────────┐  ┌▼────────────────┐  │
│  │   Schema    │  │  Graph Executor      │  │ Streaming       │  │
│  │  Extractor  │  │  - Topological Sort  │  │ Executor        │  │
│  │  - inspect  │  │  - Sequential Exec   │  │ - SSE Events    │  │
│  │  - types    │  │  - Return Results    │  │ - Real-time     │  │
│  │  - docs     │  │                      │  │ - Status Updates│  │
│  └──────┬──────┘  └──────────────────────┘  └─────────────────┘  │
└─────────┼────────────────────────────────────────────────────────┘
          │
          ↓
┌──────────────────────────────────────────────────────────────────┐
│                          Nodepacks                               │
│  └── <nodepack-name>/                                            │
│      ├── ops.py  (Python functions with type hints)              │
│      └── progress_ops.py  (Progress-aware classes with __call__) │
└──────────────────────────────────────────────────────────────────┘
```

## Backend Architecture

### 1. Schema Extraction (`schema_extractor.py`)

**Purpose**: Dynamically discover and extract metadata from Python functions in nodepacks.

**Process**:
1. Scan `nodepacks/` directory for all `ops.py` and `progress_ops.py` files
2. Load each module dynamically using `importlib`
3. For each function in `ops.py`:
   - Extract function signature using `inspect.signature()`
   - Parse type hints using `typing.get_type_hints()`
   - Extract docstrings using `inspect.getdoc()`
   - Build JSON schema with parameters and return types
4. For each class in `progress_ops.py`:
   - Extract `__call__` method signature
   - Parse type hints from `__call__` method
   - Extract docstrings from class or `__call__` method
   - Build JSON schema with `is_progress_node: true` flag

**Output Schema**:
```json
{
  "name": "function_name",
  "params": [
    {"name": "param1", "type": "float"},
    {"name": "param2", "type": "int"}
  ],
  "returns": [
    {"name": "result", "type": "float"}
  ],
  "docstring": "Function description...",
  "filepath": "/path/to/ops.py"
}
```

### 2. Graph Executor (`executor.py`)

**Purpose**: Execute node graphs in the correct order with dependency resolution.

**Key Features**:

#### Topological Sorting (Kahn's Algorithm)
```python
1. Calculate in-degree for each node (count of incoming edges)
2. Initialize queue with nodes having in-degree = 0
3. While queue is not empty:
   a. Dequeue node and add to sorted list
   b. For each neighbor, decrease in-degree by 1
   c. If neighbor's in-degree becomes 0, enqueue it
4. If sorted list size ≠ total nodes, graph has cycle
```

#### Node Execution Flow
1. **Function Nodes**:
   - Gather inputs from connected edges or default values
   - Convert input types as needed (string → float/int)
   - Call corresponding Python function
   - Store output for downstream nodes

2. **Progress Nodes** (from `progress_ops.py`):
   - Instantiate progress-aware class
   - Set up progress callback mechanism
   - Execute `__call__` method in separate thread
   - Stream progress updates via SSE during execution
   - Report progress percentage (0.0-1.0) and messages
   - Store output for downstream nodes

3. **ViewNodes**:
   - Receive input from connected edge
   - Store value for display
   - No function execution

4. **Error Handling**:
   - Type conversion errors
   - Missing functions/classes
   - Execution exceptions
   - Thread execution errors for progress nodes

### 3. API Endpoints (`main.py`)

#### GET `/get_schema`
- Returns list of all function schemas
- Used by frontend on startup to populate node library

#### POST `/execute`
- Accepts node graph (nodes + edges)
- Executes graph using GraphExecutor
- Returns ViewNode results
- Traditional single-response execution

#### POST `/execute/stream`
- Accepts node graph (nodes + edges)
- Streams execution status via Server-Sent Events (SSE)
- Provides real-time updates as nodes execute
- Returns status for each node: executing → completed/error
- Final event contains ViewNode results

**SSE Event Format:**
```json
data: {"node_id":"node_1","node_number":1,"node_name":"add","status":"executing","inputs":{"a":"5","b":"10"}}

data: {"node_id":"node_1","node_number":1,"node_name":"add","status":"completed","inputs":{"a":"5","b":"10"},"output":15}

data: {"status":"done","results":{"view_node_id":15}}
```

**Progress Node Event Format:**
```json
data: {"node_id":"node_2","node_number":2,"node_name":"ProgressOpp","status":"executing","inputs":{"count":10}}

data: {"node_id":"node_2","node_number":2,"node_name":"ProgressOpp","status":"progress","progress":0.3,"progress_message":"Processing item 3/10","inputs":{"count":10}}

data: {"node_id":"node_2","node_number":2,"node_name":"ProgressOpp","status":"progress","progress":0.6,"progress_message":"Processing item 6/10","inputs":{"count":10}}

data: {"node_id":"node_2","node_number":2,"node_name":"ProgressOpp","status":"completed","inputs":{"count":10},"output":90}
```

#### CORS Configuration
- Allows frontend to communicate with backend
- Should be restricted in production

## Frontend Architecture

### Component Hierarchy

```
App
└── PsynapseEditor (ReactFlowProvider)
    ├── NodeLibraryPanel
    │   ├── Built-in Nodes
    │   │   └── ViewNode
    │   └── Function Nodes
    │       └── [Dynamic from schemas]
    │
    ├── ReactFlow Canvas
    │   ├── Controls
    │   ├── MiniMap
    │   ├── Background
    │   └── Custom Nodes
    │       ├── FunctionNode
    │       └── ViewNode
    │
    └── StatusPanel
        └── ExecutionStatus[]
            ├── Node Number Badge
            ├── Node Name
            ├── Status Spinner/Icon
            ├── Collapsible Inputs
            └── Outputs/Errors
```

### Key Components

#### 1. PsynapseEditor (`PsynapseEditor.tsx`)

**Responsibilities**:
- Manage React Flow state (nodes, edges)
- Handle drag-and-drop from library panel
- Coordinate graph execution
- Update ViewNodes with results

**State Management**:
```typescript
- nodes: Node[]                    // All nodes on canvas
- edges: Edge[]                    // All connections
- reactFlowInstance                // React Flow API
- executing: boolean               // Execution status
- statusHistory: ExecutionStatus[] // Real-time execution updates
- abortExecution: (() => void)     // Cleanup function for aborting
```

**Key Functions**:
- `onDrop`: Create new node from dragged library item
- `executeGraph`: Serialize graph and stream execution from backend
- `handleNodeDataChange`: Update node input values

**Execution Flow**:
1. Clears previous status history
2. Calls `api.executeGraphStreaming()` with callbacks
3. Receives real-time status updates via SSE
4. Updates `statusHistory` state as nodes execute
5. Updates ViewNodes with final results

#### 2. NodeLibraryPanel (`NodeLibraryPanel.tsx`)

**Responsibilities**:
- Fetch schemas from backend
- Display draggable node items
- Handle drag events

**Drag Data Format**:
```typescript
{
  type: 'functionNode' | 'viewNode',
  schema?: FunctionSchema  // For function nodes
}
```

#### 3. FunctionNode (`FunctionNode.tsx`)

**Features**:
- Input handles for each parameter
- Input fields with type information
- Single output handle
- Real-time value updates

**Styling**:
- Blue border and handles
- White background
- Input fields for each parameter

#### 4. ViewNode (`ViewNode.tsx`)

**Features**:
- Single input handle
- Display area for value
- No output handles
- Updates after execution

**Styling**:
- Green border and handles
- Light green background
- Monospace font for values

#### 5. StatusPanel (`StatusPanel.tsx`)

**Features**:
- Real-time execution monitoring
- Displays nodes in execution order
- Animated spinner for executing nodes
- Collapsible inputs section
- Output/error display
- Scrollable history

**Styling**:
- Fixed 400px width on right side
- Color-coded status (blue/green/red)
- White cards with status borders
- Monospace font for values

**State Updates**:
- Receives ExecutionStatus[] from parent
- Updates in real-time as SSE events arrive
- Shows execution progress visually

### Data Flow

#### 1. Initialization Flow
```
1. Frontend loads → useSchema hook triggers
2. Fetch /get_schema from backend
3. Populate NodeLibraryPanel with schemas
4. User can drag nodes onto canvas
```

#### 2. Execution Flow (Streaming)
```
1. User clicks "Execute" button
2. Frontend clears previous status history
3. Serialize current graph state:
   - nodes: [{ id, type, data }]
   - edges: [{ source, target, sourceHandle, targetHandle }]
4. POST to /execute/stream endpoint (SSE)
5. Backend:
   - Topologically sort nodes
   - For each node in order:
     a. Yield "executing" status with inputs
     b. Execute node function
     c. Yield "completed" status with output (or "error" if failed)
   - Yield "done" event with final results
6. Frontend:
   - Receives SSE events in real-time
   - Updates StatusPanel with each status update
   - Shows spinner for executing nodes
   - Displays outputs/errors as they complete
   - Updates ViewNode components with final results
```

#### 3. Execution Flow (Traditional)
```
1. User clicks "Execute" button
2. Serialize current graph state
3. POST to /execute endpoint
4. Backend:
   - Topologically sort nodes
   - Execute all in order
   - Return ViewNode results
5. Frontend updates ViewNode components with results
```

## Node Graph Execution Details

### Example Graph

```
Input: 5,3      Input: 2,4
    ↓               ↓
  [add]           [add]
    ↓               ↓
    └─→ [multiply] ←┘
            ↓
        [ViewNode]
```

### Execution Steps

1. **Topological Sort**:
   ```
   Order: add1 → add2 → multiply → view
   ```

2. **Sequential Execution**:
   ```
   add1: result = 5 + 3 = 8
   add2: result = 2 + 4 = 6
   multiply: result = 8 * 6 = 48
   view: display = 48
   ```

3. **Result**:
   ```json
   {
     "results": {
       "view_node_id": 48
     }
   }
   ```

## Type System

### Supported Types

Backend and frontend support these primitive types:
- `float`: Floating-point numbers
- `int`: Integers
- `str`: Strings
- `bool`: Booleans

### Type Conversion

The executor automatically converts input values:
```python
if param_type == float:
    value = float(input_value)
elif param_type == int:
    value = int(input_value)
```

## Error Handling

### Backend Errors
- **Schema extraction**: Module loading failures, missing type hints
- **Graph execution**: Cycle detection, missing functions, type errors
- **API errors**: Invalid request format, execution failures

### Frontend Errors
- **Schema loading**: Network errors, invalid response
- **Graph execution**: Network errors, backend failures
- **User input**: Invalid values, disconnected nodes

## Performance Considerations

### Backend
- Function registry cached on startup
- Module imports cached by Python
- Topological sort: O(V + E) complexity

### Frontend
- React Flow handles large graphs efficiently
- Memoized node components prevent unnecessary re-renders
- State updates batched for performance

## Extension Points

### Adding New Node Types
1. Create new component in `frontend/src/components/`
2. Add to `nodeTypes` object in PsynapseEditor
3. Handle in drag-and-drop logic
4. Update executor if special handling needed

### Adding New Data Types
1. Update type hints in Python functions
2. Update `get_type_name()` in schema_extractor
3. Add type conversion in executor
4. Update frontend input components

### Custom Nodepacks
1. Create directory in `nodepacks/`
2. Add `ops.py` with type-hinted functions
3. Restart backend
4. Functions automatically appear in library

## Testing

### Backend Tests
- Schema extraction verification
- Graph execution correctness
- Topological sort validation
- Type conversion accuracy

### Frontend Tests (Recommended)
- Component rendering
- Drag-and-drop functionality
- Graph execution flow
- Error handling

## Deployment

### Backend Deployment
```bash
# Use production ASGI server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Deployment
```bash
# Build for production
npm run build

# Serve static files with nginx/apache
```

## Future Enhancements

1. **Persistence**: Save/load workflows
2. **Validation**: Pre-execution graph validation
3. **Debugging**: Step-through execution
4. **Advanced Types**: Lists, dictionaries, custom objects
5. **Async Execution**: Long-running operations
6. **Caching**: Memoize node results
7. **Undo/Redo**: Workflow history
8. **Export**: Generate standalone Python scripts

## Conclusion

Psynapse provides a flexible, extensible platform for visual programming. The architecture separates concerns effectively, making it easy to extend and maintain. The use of Python's introspection capabilities and React Flow's powerful graph editing features creates a seamless user experience.
