# Error Handling

Psynapse includes a comprehensive error handling system that catches and displays errors during node execution:

## Features

- **Automatic Error Detection**: All node execution errors are automatically caught
- **Toast Notifications**: Errors appear as toast notifications at the bottom-right corner of the editor
- **Execution Pause**: When an error occurs, graph execution is automatically paused
- **Single Toast Per Error**: Only one toast is shown for each unique error to avoid clutter
- **Visual Node Highlighting**: Nodes with errors are highlighted with a **red border** for easy identification
- **Visual Feedback**: Status bar shows "⏸ Execution Paused" when errors are present
- **Error Details**: Each toast shows:
  - The node where the error occurred
  - The error type (e.g., `ZeroDivisionError`, `TypeError`, `ValueError`)
  - The error message

## How It Works

1. When a node's `execute()` method raises an exception, the error is caught by the error handling system
2. The **node is highlighted with a red border** to visually indicate the error source
3. A toast notification appears at the bottom-right corner with the error details
4. **Graph execution is paused** to prevent cascading errors
5. The status bar displays "⏸ Execution Paused - Fix error and close toast to resume"
6. **Fix the error** (e.g., change input values to avoid division by zero)
7. **Click the ✕ button** on the toast to dismiss it
8. The red border is removed from the node
9. Execution automatically resumes:
   - If the error is fixed, execution continues normally
   - If the error persists, the node is highlighted again and a new toast appears
