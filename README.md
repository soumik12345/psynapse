# Psynapse

A cross-platform node-based UI editor for Python.

## Features

- **Visual Node Editor**: Intuitive drag-and-drop interface for creating node graphs
- **Decoupled Execution**: FastAPI backend handles graph execution separately from the UI
- **Built-in Nodes**: Includes Object, Add, Subtract, Multiply, Divide, and View nodes
- **Typed Input Nodes**: Object node with dynamic widgets for different data types (int, float, string, bool)
- **Error Handling**: Comprehensive error handling with persistent toast notifications
- **On-Demand Execution**: Execute graphs when you're ready with the Run button
- **Interactive Canvas**: Pan, zoom, and navigate your node graph with ease

https://github.com/user-attachments/assets/af27b17b-ed7a-4bde-8f53-d6eb698d05cb

## Installation

```bash
uv pip install -U git+https://github.com/soumik12345/psynapse.git
```

## Usage

### Quick Start

Simply run the command `psynapse` in the terminal, this would launch the Psynapse application with a locally hosted execution runtime.

### Run with a remote backend

1. Start the execution runtime locally or in a remote VM using

    ```bash
    uv run psynapse-backend
    ```

    The backend will be available at `http://localhost:8000`.

2. Launch the Psynapse editor using

    ```bash
    uv run psynapse
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

4. **Executing the Graph**:
   - Click the "▶ Run Graph" button at the top of the editor
   - The graph will be sent to the backend for execution
   - Results will appear in View nodes

5. **Viewing Results**:
   - Add View nodes to display computation results
   - Results update when you run the graph

6. **Navigation**:
   - **Pan**: Right-click and drag
   - **Zoom**: Mouse wheel
   - **Reset Zoom**: `Ctrl+0`

7. **Deleting**:
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
- `Ctrl+B` (or `Cmd+B` on Mac): Toggle node library panel
- `Ctrl+` (or `Cmd+` on Mac): Toggle terminal panel

## Mouse Controls

- **Left Click**: Select items
- **Left Drag (on node)**: Move node
- **Left Drag (on socket)**: Create connection
- **Right Drag**: Pan canvas
- **Mouse Wheel**: Zoom in/out

## Acknowledgments

Inspired by [Nodezator](https://github.com/IndiePython/nodezator), a powerful node editor for Python.
