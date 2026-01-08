# Hooks

## useSchema

A custom React hook for fetching and managing function schemas from the backend API.

### Signature

```typescript
const useSchema = () => {
  schemas: FunctionSchema[];
  loading: boolean;
  error: string | null;
}
```

### Return Value

Returns an object with three properties:

| Property | Type | Description |
|----------|------|-------------|
| `schemas` | `FunctionSchema[]` | Array of function schemas loaded from the backend |
| `loading` | `boolean` | Indicates whether schemas are currently being fetched |
| `error` | `string \| null` | Error message if fetch failed, null otherwise |

### Behavior

The hook automatically fetches schemas when the component mounts using the `useEffect` hook:

1. Sets `loading` to `true` at the start of the fetch
2. Calls `api.getSchemas()` to retrieve schemas from the backend
3. Updates `schemas` state with the fetched data on success
4. Sets `error` state with error message on failure
5. Sets `loading` to `false` when complete (success or failure)

### Error Handling

Errors are caught and handled gracefully:
- If the error is an `Error` instance, uses its message
- Otherwise, uses a generic "Failed to fetch schemas" message
- Errors are also logged to the console for debugging

### Usage Example

```typescript
import { useSchema } from '../hooks/useSchema';

function MyComponent() {
  const { schemas, loading, error } = useSchema();

  if (loading) {
    return <div>Loading schemas...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      {schemas.map(schema => (
        <div key={schema.name}>{schema.name}</div>
      ))}
    </div>
  );
}
```

### Dependencies

- **Internal**: `api.getSchemas()` from `../utils/api`
- **External**: React's `useState` and `useEffect` hooks
- **Types**: `FunctionSchema` from `../types/schema`

### State Updates

The hook manages three pieces of state internally:

1. **schemas**: Initially an empty array `[]`
2. **loading**: Initially `true`
3. **error**: Initially `null`

### When to Use

Use this hook when you need to:
- Display available function nodes in the UI
- Populate a node library or selection menu
- Validate available functions before graph creation
- Show function metadata to users

### Limitations

- Fetches schemas only once on mount (no refetch mechanism)
- No caching between component unmounts
- No manual refresh capability
- Assumes API endpoint is available at component mount time

