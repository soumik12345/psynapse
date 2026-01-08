# Type Definitions

Type definitions for the Psynapse frontend application.

---

## Function Schema Types

### ParamSchema

Describes a function parameter.

```typescript
interface ParamSchema {
  name: string;
  type: string;
}
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `string` | The parameter name |
| `type` | `string` | The parameter type (e.g., "int", "str", "float") |

#### Example

```typescript
const param: ParamSchema = {
  name: "x",
  type: "int"
};
```

---

### ReturnSchema

Describes a function return value.

```typescript
interface ReturnSchema {
  name: string;
  type: string;
}
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `string` | The return value name |
| `type` | `string` | The return value type |

#### Example

```typescript
const returnVal: ReturnSchema = {
  name: "result",
  type: "int"
};
```

---

### FunctionSchema

Complete schema for a Python function exposed to the visual editor.

```typescript
interface FunctionSchema {
  name: string;
  params: ParamSchema[];
  returns: ReturnSchema[];
  docstring: string;
  filepath: string;
}
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `string` | The function name |
| `params` | `ParamSchema[]` | Array of parameter schemas |
| `returns` | `ReturnSchema[]` | Array of return value schemas |
| `docstring` | `string` | The function's documentation string |
| `filepath` | `string` | Path to the source file containing the function |

#### Example

```typescript
const schema: FunctionSchema = {
  name: "add",
  params: [
    { name: "a", type: "int" },
    { name: "b", type: "int" }
  ],
  returns: [
    { name: "sum", type: "int" }
  ],
  docstring: "Adds two integers together",
  filepath: "/path/to/ops.py"
};
```

---

## Node Data Types

### NodeData

Data structure for node instances in the graph.

```typescript
interface NodeData {
  label: string;
  functionName?: string;
  params?: ParamSchema[];
  [key: string]: any;
}
```

#### Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `label` | `string` | Yes | Display name for the node |
| `functionName` | `string` | No | Name of the function (for function nodes) |
| `params` | `ParamSchema[]` | No | Parameter schemas (for function nodes) |
| `[key: string]` | `any` | No | Dynamic properties for parameter values, edges, callbacks, etc. |

#### Common Dynamic Properties

- `edges`: Current graph edges
- `onChange`: Callback for parameter changes
- `value`: Result value (for view nodes)
- Parameter values (e.g., `x: "5"`, `y: "10"`)

#### Example

```typescript
const functionNodeData: NodeData = {
  label: "Add",
  functionName: "add",
  params: [
    { name: "a", type: "int" },
    { name: "b", type: "int" }
  ],
  a: "5",
  b: "10",
  edges: [],
  onChange: (nodeId, param, value) => { /* ... */ }
};

const viewNodeData: NodeData = {
  label: "View",
  value: 15,
  edges: []
};
```

---

## API Request/Response Types

### ExecuteRequest

Request structure for graph execution.

```typescript
interface ExecuteRequest {
  nodes: any[];
  edges: any[];
}
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `nodes` | `any[]` | Array of node objects with id, type, and data |
| `edges` | `any[]` | Array of edge objects with source, target, and handle information |

#### Node Structure

```typescript
{
  id: string;
  type: string;
  data: NodeData;
}
```

#### Edge Structure

```typescript
{
  source: string;
  target: string;
  sourceHandle: string;
  targetHandle: string;
}
```

#### Example

```typescript
const request: ExecuteRequest = {
  nodes: [
    {
      id: "node_1",
      type: "functionNode",
      data: {
        label: "Add",
        functionName: "add",
        a: "5",
        b: "10"
      }
    },
    {
      id: "node_2",
      type: "viewNode",
      data: {
        label: "View"
      }
    }
  ],
  edges: [
    {
      source: "node_1",
      target: "node_2",
      sourceHandle: "output",
      targetHandle: "input"
    }
  ]
};
```

---

### ExecuteResponse

Response structure from graph execution.

```typescript
interface ExecuteResponse {
  results: { [nodeId: string]: any };
}
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `results` | `{ [nodeId: string]: any }` | Map of node IDs to their computed values |

#### Example

```typescript
const response: ExecuteResponse = {
  results: {
    "node_1": 15,
    "node_2": 15
  }
};
```

---

### ExecutionStatus

Status information for a node during graph execution, used for real-time execution monitoring.

```typescript
interface ExecutionStatus {
  node_id: string;
  node_number: number;
  node_name: string;
  status: 'executing' | 'completed' | 'error';
  inputs?: Record<string, any>;
  output?: any;
  error?: string;
}
```

#### Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `node_id` | `string` | Yes | The unique identifier of the node |
| `node_number` | `number` | Yes | Sequential execution number (1-indexed) |
| `node_name` | `string` | Yes | Display name of the node or function |
| `status` | `'executing' \| 'completed' \| 'error'` | Yes | Current execution status |
| `inputs` | `Record<string, any>` | No | Input parameters and their values |
| `output` | `any` | No | Result value (present when status is 'completed') |
| `error` | `string` | No | Error message (present when status is 'error') |

#### Status Values

- **`executing`**: Node execution has started
- **`completed`**: Node execution finished successfully
- **`error`**: Node execution failed with an error

#### Example - Executing Status

```typescript
const executingStatus: ExecutionStatus = {
  node_id: "node_1",
  node_number: 1,
  node_name: "add",
  status: "executing",
  inputs: {
    a: "5",
    b: "10"
  }
};
```

#### Example - Completed Status

```typescript
const completedStatus: ExecutionStatus = {
  node_id: "node_1",
  node_number: 1,
  node_name: "add",
  status: "completed",
  inputs: {
    a: "5",
    b: "10"
  },
  output: 15
};
```

#### Example - Error Status

```typescript
const errorStatus: ExecutionStatus = {
  node_id: "node_2",
  node_number: 2,
  node_name: "divide",
  status: "error",
  inputs: {
    a: "10",
    b: "0"
  },
  error: "division by zero"
};
```

#### Usage Context

ExecutionStatus objects are received via Server-Sent Events during graph execution:

```typescript
api.executeGraphStreaming(
  request,
  (status: ExecutionStatus) => {
    // Handle status update
    console.log(`${status.node_name}: ${status.status}`);
  },
  onComplete,
  onError
);
```

---

## Type Usage Guidelines

### Importing Types

```typescript
import type { 
  FunctionSchema, 
  NodeData, 
  ExecuteRequest, 
  ExecuteResponse 
} from '../types/schema';
```

### Type Guards

When working with dynamic `NodeData`, consider creating type guards:

```typescript
function isFunctionNodeData(data: NodeData): data is NodeData & {
  functionName: string;
  params: ParamSchema[];
} {
  return 'functionName' in data && 'params' in data;
}
```

### Extending Types

For component-specific needs, extend the base types:

```typescript
interface FunctionNodeData extends NodeData {
  functionName: string;
  params: ParamSchema[];
  onChange: (nodeId: string, param: string, value: string) => void;
}
```

