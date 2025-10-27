# Psynapse

A beautiful node-based UI editor built with Python and PySide6, inspired by Nodezator.

## Features

- **Visual Node Editor**: Intuitive drag-and-drop interface for creating node graphs
- **Built-in Nodes**: Includes Object, Add, Subtract, Multiply, Divide, and View nodes
- **Typed Input Nodes**: Object node with dynamic widgets for different data types (int, float, string, bool)
- **Error Handling**: Comprehensive error handling with persistent toast notifications
- **Real-time Evaluation**: Automatic graph evaluation and result display
- **Interactive Canvas**: Pan, zoom, and navigate your node graph with ease
- **Flexible Connections**: Connect nodes with bezier curve edges
- **Modern UI**: Clean, dark-themed interface with smooth interactions

## Installation

```bash
uv pip install -U git+https://github.com/soumik12345/psynapse.git
```

## Usage

### Running the Editor

```bash
uv run psynapse
```

Or using Python directly:

```bash
uv run python -m psynapse
```

### Creating a Node Graph

1. **Adding Nodes**: 
   - Use the `Nodes` menu to add nodes
   - Right-click on the canvas for a context menu
   
2. **Connecting Nodes**:
   - Click and drag from an output socket (right side of node)
   - Release on an input socket (left side of another node)
   - Connections are shown as green bezier curves

3. **Moving Nodes**:
   - Click and drag nodes to reposition them
   - Connections update automatically

4. **Viewing Results**:
   - Add a View node to display computation results
   - Results update in real-time as you modify the graph

5. **Navigation**:
   - **Pan**: Right-click and drag
   - **Zoom**: Mouse wheel
   - **Reset Zoom**: `Ctrl+0`

6. **Deleting**:
   - Select nodes or connections
   - Press `Ctrl+D` (or `Cmd+D` on Mac)

## Available Nodes

### Input Nodes

- **Object Node**: Creates and outputs typed values with dynamic input widgets
  - Output type: Any (adapts to selected type)
  - Features:
    - **Type Selector**: Dropdown to choose data type (Integer, Float, String, Boolean)
    - **Dynamic Widgets**:
      - **Integer**: Spinbox with up/down arrows (range: -999999 to 999999)
      - **Float**: Decimal spinbox with up/down arrows and 4 decimal places
      - **String**: Text input field
      - **Boolean**: Checkbox
    - Widget automatically changes when type is switched
    - Perfect for providing constant values to your node graph

### Math Nodes

- **Add Node**: Adds two numbers (A + B)
  - Input types: Float, Float
  - Includes input fields for direct value entry
- **Subtract Node**: Subtracts two numbers (A - B)
  - Input types: Float, Float
  - Includes input fields for direct value entry
- **Multiply Node**: Multiplies two numbers (A × B)
  - Input types: Float, Float
  - Includes input fields for direct value entry
- **Divide Node**: Divides two numbers (A ÷ B)
  - Input types: Float, Float
  - Includes input fields for direct value entry
  - Demonstrates error handling with division by zero

### Display Nodes

- **View Node**: Displays the input value in the node
  - Input type: Any (accepts any data type)

## Architecture

The editor is built with a modular architecture:

- `scene.py`: Graphics scene with grid background
- `view.py`: Interactive view with pan/zoom and connection handling
- `node.py`: Base node class with socket management and error handling
- `socket.py`: Connection points for nodes
- `edge.py`: Connections between sockets
- `nodes.py`: Specific node implementations
- `editor.py`: Main window and application logic
- `toast_notification.py`: Error notification system

## Error Handling

Psynapse includes a comprehensive error handling system that catches and displays errors during node execution:

### Features

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

### How It Works

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

### Error Flow

```
Error Occurs → Node Highlighted (Red Border) → Toast Shown → Execution Paused
                                                                      ↓
                                                            User Fixes Error
                                                                      ↓
                                                          User Closes Toast
                                                                      ↓
                                                    Red Border Removed → Execution Resumes
                                                                      ↓
                                                            Error Still Exists?
                                                                      ↓
                                                    New Red Border → New Toast → Pause Again
```

### Example

Try the error handling demo:
```bash
uv run python examples/error_handling_demo.py
```

This example demonstrates division by zero error handling:
1. The demo starts with a divide-by-zero error
2. The Divide node is **highlighted with a red border**
3. A toast notification appears and execution pauses
4. Change the denominator to a non-zero value
5. Click the ✕ button on the toast
6. The red border disappears and execution resumes
7. If error is fixed, the graph continues normally!

## Extending Psynapse

### Creating Custom Nodes

Psynapse supports a type system for sockets with automatic input fields for basic types:

```python
from psynapse import Node, SocketDataType

class CustomNode(Node):
    def __init__(self):
        super().__init__(
            title="Custom",
            inputs=[
                ("Input1", SocketDataType.FLOAT),
                ("Input2", SocketDataType.INT)
            ],
            outputs=[("Output", SocketDataType.FLOAT)]
        )
    
    def execute(self):
        # Get input values (automatically from widgets or connections)
        a = self.get_input_value(0)
        b = self.get_input_value(1)
        
        # Perform computation
        result = a + b  # Your logic here
        
        # Store and return result
        self.output_sockets[0].value = result
        return result
```

### Available Socket Types

- `SocketDataType.INT`: Integer values with input field
- `SocketDataType.FLOAT`: Floating point values with input field
- `SocketDataType.STRING`: Text values with input field
- `SocketDataType.BOOL`: Boolean values
- `SocketDataType.ANY`: Any type (no input field, must be connected)

### Input Fields

When you use `INT`, `FLOAT`, or `STRING` types for input sockets:
- An input field automatically appears next to the socket
- Users can type values directly into the node
- The input field is hidden when a connection is made
- The input field reappears when the connection is removed
- Values are automatically validated and converted to the correct type

## Keyboard Shortcuts

- `Ctrl+N` (or `Cmd+N` on Mac): New scene
- `Ctrl+Q` (or `Cmd+Q` on Mac): Quit application
- `Ctrl++` (or `Cmd++` on Mac): Zoom in
- `Ctrl+-` (or `Cmd+-` on Mac): Zoom out
- `Ctrl+0` (or `Cmd+0` on Mac): Reset zoom
- `Ctrl+D` (or `Cmd+D` on Mac): Delete selected items

## Mouse Controls

- **Left Click**: Select items
- **Left Drag (on node)**: Move node
- **Left Drag (on socket)**: Create connection
- **Right Drag**: Pan canvas
- **Mouse Wheel**: Zoom in/out

## Acknowledgments

Inspired by [Nodezator](https://github.com/IndiePython/nodezator), a powerful node editor for Python.
