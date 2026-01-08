# Components

## PsynapseEditor

The main editor component that provides the visual node-based programming interface.

### Description

`PsynapseEditor` is the root component of the visual editor. It wraps the editor implementation in a `ReactFlowProvider` to enable React Flow functionality. The actual implementation is in `PsynapseEditorInner`.

### Features

- **Drag-and-drop interface**: Add nodes from the library panel by dragging them onto the canvas
- **Visual node connections**: Connect nodes by dragging edges between input and output handles
- **Graph execution**: Execute the entire node graph with a single button click
- **Real-time updates**: View nodes update automatically after graph execution
- **Mini-map and controls**: Built-in navigation aids for large graphs

### State Management

The component manages several pieces of state:

- `nodes`: Array of nodes in the graph
- `edges`: Array of connections between nodes
- `reactFlowInstance`: Reference to the React Flow instance
- `executing`: Boolean indicating whether graph execution is in progress
- `statusHistory`: Array of execution status updates for real-time display
- `abortExecution`: Cleanup function to abort ongoing execution

### Key Methods

#### `onConnect`

Handles new edge connections between nodes. Updates both the edges state and propagates edge information to all nodes.

**Parameters:**
- `connection: Connection` - The new connection to add

#### `onDrop`

Handles dropping nodes from the library panel onto the canvas. Creates new nodes based on the dropped data.

**Parameters:**
- `event: React.DragEvent` - The drop event

**Supports:**
- `viewNode`: Creates a view node for displaying results
- `functionNode`: Creates a function node with parameters based on schema

#### `handleNodeDataChange`

Updates node data when parameter values change.

**Parameters:**
- `nodeId: string` - The ID of the node to update
- `paramName: string` - The name of the parameter to update
- `value: string` - The new value for the parameter

#### `executeGraph`

Executes the entire node graph using real-time streaming from the backend API.

**Process:**
1. Clears previous execution status history
2. Prepares nodes and edges for execution
3. Sends graph to backend via `api.executeGraphStreaming()`
4. Receives real-time status updates via Server-Sent Events (SSE)
5. Updates status history as nodes execute
6. Updates view nodes with final execution results
7. Handles errors with user feedback

**Callbacks:**
- `onStatus(status: ExecutionStatus)`: Called for each node execution update
- `onComplete(results)`: Called when execution finishes successfully
- `onError(error)`: Called if execution fails

### Usage Example

```typescript
import PsynapseEditor from './components/PsynapseEditor';

function App() {
  return <PsynapseEditor />;
}
```

---

## FunctionNode

A node component representing a Python function with input parameters and output.

### Props

```typescript
interface NodeProps<NodeData> {
  data: NodeData;
  id: string;
}
```

**NodeData includes:**
- `label: string` - The display name of the function
- `params?: ParamSchema[]` - Array of parameter schemas
- `onChange?: (nodeId: string, paramName: string, value: string) => void` - Callback for parameter changes
- `edges?: any[]` - Current graph edges

### Features

- **Dynamic inputs**: Creates input fields based on function schema
- **Connection awareness**: Hides input fields when parameters are connected via edges
- **Type information**: Displays parameter types next to labels
- **Visual feedback**: Shows connection status with colored indicators

### Styling

- **Border**: Blue (`#4a90e2`)
- **Background**: White
- **Handles**: Blue circles for input/output connections

### Input Behavior

Each parameter can be:
- **Connected**: Input field hidden, shows connection indicator (●)
- **Unconnected**: Text input field visible for manual value entry

### Usage Example

```typescript
const nodeTypes = {
  functionNode: FunctionNode,
};

<ReactFlow nodeTypes={nodeTypes} ... />
```

---

## ViewNode

A node component for displaying execution results.

### Props

```typescript
interface NodeProps<NodeData> {
  data: NodeData;
}
```

**NodeData includes:**
- `value?: any` - The value to display (updated after execution)

### Features

- **Result display**: Shows execution results in a monospace font
- **Default message**: Displays "No value" when no result is available
- **Single input**: Accepts one incoming connection

### Styling

- **Border**: Green (`#50c878`)
- **Background**: Light green (`#f0fdf4`)
- **Content box**: White with monospace font

### Display Behavior

- Converts any value to string for display
- Handles undefined values gracefully
- Word-wrapping for long values

### Usage Example

```typescript
const nodeTypes = {
  viewNode: ViewNode,
};

<ReactFlow nodeTypes={nodeTypes} ... />
```

---

## NodeLibraryPanel

A sidebar panel displaying available nodes that can be dragged onto the canvas.

### Props

```typescript
interface NodeLibraryPanelProps {
  schemas: FunctionSchema[];
  loading: boolean;
  error: string | null;
}
```

### Features

- **Built-in nodes section**: Contains ViewNode
- **Function nodes section**: Dynamically generated from backend schemas
- **Drag-and-drop**: All nodes are draggable onto the canvas
- **Loading state**: Shows loading indicator while fetching schemas
- **Error handling**: Displays error messages if schema fetch fails

### Node Information Display

For each function node, displays:
- Function name
- Number of inputs and outputs (e.g., "2 inputs → 1 outputs")

### Drag Data Format

Sends data in `application/reactflow` format:

**For ViewNode:**
```typescript
{ type: 'viewNode' }
```

**For FunctionNode:**
```typescript
{ 
  type: 'functionNode', 
  schema: FunctionSchema 
}
```

### Styling

- **Panel width**: 260px
- **Background**: Light gray (`#f8f9fa`)
- **Node items**: White cards with hover effects

### Usage Example

```typescript
<NodeLibraryPanel 
  schemas={functionSchemas}
  loading={isLoading}
  error={errorMessage}
/>
```

---

## StatusPanel

A real-time execution status panel that displays node execution progress during graph execution.

### Props

```typescript
interface StatusPanelProps {
  statusHistory: ExecutionStatus[];
}
```

### Features

- **Real-time updates**: Shows node execution status as it happens via Server-Sent Events (SSE)
- **Execution history**: Displays all nodes executed in topological order
- **Node information**: Shows node number, name, and status
- **Spinner animation**: Displays animated spinner for nodes currently executing
- **Progress bars**: Visual progress indicators for progress-aware nodes with percentage and messages
- **Collapsible inputs**: Expandable section showing input parameters
- **Output display**: Shows execution results for completed nodes
- **Error handling**: Displays error messages for failed nodes
- **Color coding**: Visual status indicators (blue=executing/progress, green=completed, red=error)

### Status Information Display

For each node in the execution history:
- **Node number badge**: Sequential number (1-indexed) with color-coded background
- **Node name**: Function name or node label
- **Status icon**: Spinner (executing/progress), checkmark (completed), or X (error)
- **Progress bar**: For progress nodes, displays:
  - Horizontal progress bar showing completion percentage (0-100%)
  - Progress message (e.g., "Processing item 3/10")
  - Percentage text display
  - Smooth transitions as progress updates
- **Inputs section**: Collapsible display of input parameters and values
- **Output section**: Result value displayed after completion
- **Error section**: Error message if execution failed

### Styling

- **Panel width**: 400px
- **Position**: Fixed on right side of screen
- **Background**: Light gray (`#f8f9fa`)
- **Node cards**: White with colored borders matching status
- **Status colors**:
  - Executing/Progress: Blue (`#007bff`)
  - Completed: Green (`#28a745`)
  - Error: Red (`#dc3545`)
- **Progress bar styling**:
  - Background: Light gray (`#e9ecef`)
  - Fill: Blue (`#007bff`)
  - Height: 8px with rounded corners
  - Smooth transitions: 0.3s ease

### State Behavior

The panel displays nodes in the order they are executed:
1. When a node starts executing, it appears with a spinner
2. For progress nodes, progress updates replace the executing status with progress bars
3. Progress bars update in real-time as the node reports progress
4. When execution completes, the node updates with output
5. If execution fails, the node shows error details
6. All executed nodes remain visible in a scrollable history

### Progress Node Support

Progress nodes display special progress indicators:
- **Progress status**: Status is set to `"progress"` during execution
- **Progress bar**: Visual bar showing completion percentage
- **Progress message**: Custom message from the node (e.g., "Processing item 5/10")
- **Real-time updates**: Progress bar updates smoothly as progress is reported
- **Completion**: Progress bar is replaced with output when execution completes

See the [Progress Nodes Guide](../guides/progress-nodes.md) for details on creating progress-aware nodes.

### Value Rendering

The panel intelligently renders different value types:
- Primitives: Displayed as strings
- Objects/Arrays: JSON.stringify with formatting
- Null/undefined: Displayed as "null"

### Usage Example

```typescript
<StatusPanel statusHistory={executionStatusHistory} />
```

### Integration

The StatusPanel is integrated into PsynapseEditor and receives real-time updates through the streaming execution API:

```typescript
const [statusHistory, setStatusHistory] = useState<ExecutionStatus[]>([]);

// During execution, status updates are appended to history
api.executeGraphStreaming(
  request,
  (status) => {
    setStatusHistory(prev => {
      // Update logic for managing status history
    });
  },
  onComplete,
  onError
);
```

