# Utilities

## API Client

The API client module provides functions for communicating with the Psynapse backend server.

### Configuration

```typescript
const API_BASE_URL = 'http://localhost:8000';
```

The default base URL points to a local backend server running on port 8000.

---

## API Methods

### getSchemas

Fetches available function schemas from the backend.

#### Signature

```typescript
async getSchemas(): Promise<FunctionSchema[]>
```

#### Returns

A promise that resolves to an array of `FunctionSchema` objects.

#### Endpoint

```
GET /get_schema
```

#### Response Format

```typescript
[
  {
    name: string;
    params: ParamSchema[];
    returns: ReturnSchema[];
    docstring: string;
    filepath: string;
  },
  ...
]
```

#### Usage Example

```typescript
import { api } from '../utils/api';

async function loadSchemas() {
  try {
    const schemas = await api.getSchemas();
    console.log('Available functions:', schemas);
  } catch (error) {
    console.error('Failed to load schemas:', error);
  }
}
```

#### Error Handling

- Throws an error if the request fails
- Network errors are propagated from axios
- HTTP error responses (4xx, 5xx) throw exceptions

---

### executeGraph

Executes a computational graph on the backend.

#### Signature

```typescript
async executeGraph(request: ExecuteRequest): Promise<ExecuteResponse>
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `request` | `ExecuteRequest` | The graph execution request containing nodes and edges |

#### ExecuteRequest Structure

```typescript
{
  nodes: Array<{
    id: string;
    type: string;
    data: any;
  }>;
  edges: Array<{
    source: string;
    target: string;
    sourceHandle: string;
    targetHandle: string;
  }>;
}
```

#### Returns

A promise that resolves to an `ExecuteResponse` object.

#### ExecuteResponse Structure

```typescript
{
  results: {
    [nodeId: string]: any;
  }
}
```

The `results` object maps node IDs to their computed values. Typically includes results for ViewNodes and intermediate computations.

#### Endpoint

```
POST /execute
```

#### Usage Example

```typescript
import { api } from '../utils/api';

async function runGraph(nodes, edges) {
  try {
    const response = await api.executeGraph({
      nodes: nodes.map(n => ({
        id: n.id,
        type: n.type,
        data: n.data,
      })),
      edges: edges.map(e => ({
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle,
      })),
    });
    
    console.log('Execution results:', response.results);
    return response.results;
  } catch (error) {
    console.error('Graph execution failed:', error);
    throw error;
  }
}
```

#### Error Handling

- Throws an error if the request fails
- Network errors are propagated from axios
- Backend validation errors are returned in the response
- HTTP error responses include error details in the exception

---

### executeGraphStreaming

Executes a computational graph with real-time status updates via Server-Sent Events (SSE).

#### Signature

```typescript
executeGraphStreaming(
  request: ExecuteRequest,
  onStatus: (status: ExecutionStatus) => void,
  onComplete: (results: { [nodeId: string]: any }) => void,
  onError: (error: string) => void
): () => void
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `request` | `ExecuteRequest` | The graph execution request containing nodes and edges |
| `onStatus` | `(status: ExecutionStatus) => void` | Callback invoked for each node execution status update |
| `onComplete` | `(results: { [nodeId: string]: any }) => void` | Callback invoked when execution completes successfully |
| `onError` | `(error: string) => void` | Callback invoked if execution fails |

#### Returns

A cleanup function that aborts the ongoing execution when called.

#### ExecutionStatus Structure

```typescript
{
  node_id: string;
  node_number: number;
  node_name: string;
  status: 'executing' | 'completed' | 'error';
  inputs?: Record<string, any>;
  output?: any;
  error?: string;
}
```

#### Endpoint

```
POST /execute/stream
```

#### SSE Event Format

The backend streams events in Server-Sent Events format:

```
data: {"node_id":"node_1","node_number":1,"node_name":"add","status":"executing","inputs":{"a":"5","b":"10"}}

data: {"node_id":"node_1","node_number":1,"node_name":"add","status":"completed","inputs":{"a":"5","b":"10"},"output":15}

data: {"status":"done","results":{"view_node_id":15}}
```

#### Usage Example

```typescript
import { api } from '../utils/api';

function executeWithStatus(nodes, edges) {
  const cleanup = api.executeGraphStreaming(
    {
      nodes: nodes.map(n => ({ id: n.id, type: n.type, data: n.data })),
      edges: edges.map(e => ({
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle,
      })),
    },
    // onStatus callback
    (status) => {
      console.log(`Node ${status.node_number}: ${status.node_name} - ${status.status}`);
      if (status.status === 'completed') {
        console.log('Output:', status.output);
      }
    },
    // onComplete callback
    (results) => {
      console.log('Execution complete:', results);
    },
    // onError callback
    (error) => {
      console.error('Execution failed:', error);
    }
  );

  // To abort execution:
  // cleanup();
  
  return cleanup;
}
```

#### Execution Flow

1. **Connection**: Establishes SSE connection using fetch API with POST method
2. **Streaming**: Receives status updates as nodes execute in topological order
3. **Status Updates**: 
   - "executing" status when node starts
   - "completed" status with output when node finishes
   - "error" status with error message if node fails
4. **Completion**: Receives "done" event with final ViewNode results
5. **Cleanup**: Connection automatically closes, or can be aborted via cleanup function

#### Error Handling

- Network errors are caught and passed to `onError` callback
- Backend execution errors are streamed as error events
- Connection can be aborted using the returned cleanup function
- Abort errors are silently ignored (not passed to `onError`)

#### Implementation Details

- Uses fetch API with `ReadableStream` for SSE support
- Supports POST requests (unlike EventSource API)
- Parses `data: ` prefixed SSE messages
- Handles incomplete messages with buffer management
- Provides AbortController for cancellation

---

## HTTP Client

The API client uses [axios](https://axios-http.com/) for HTTP requests (for non-streaming endpoints) and the native fetch API for Server-Sent Events, providing:

- Automatic JSON serialization/deserialization
- Promise-based API
- Request/response interceptors (if needed)
- Timeout handling
- Error handling

### Type Safety

All API methods are fully typed using TypeScript interfaces from `../types/schema`, ensuring type safety throughout the application.

### Extensibility

To add new API methods:

1. Define request/response types in `../types/schema.ts`
2. Add method to the `api` object
3. Use axios for the HTTP request
4. Return properly typed response

Example:

```typescript
export const api = {
  // ... existing methods ...
  
  async newMethod(param: ParamType): Promise<ReturnType> {
    const response = await axios.post<ReturnType>(
      `${API_BASE_URL}/new_endpoint`,
      param
    );
    return response.data;
  },
};
```

