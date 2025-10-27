"""Example demonstrating the error handling system with toast notifications."""

import sys

from PySide6.QtWidgets import QApplication

from psynapse.core.edge import Edge
from psynapse.editor.editor import PsynapseEditor
from psynapse.nodes.object_node import ObjectNode
from psynapse.nodes.ops import DivideNode, ViewNode


def main():
    """Run the error handling demo."""
    app = QApplication(sys.argv)

    # Create editor
    editor = PsynapseEditor()
    editor.setWindowTitle("PySynapse - Error Handling Demo")
    editor.resize(1400, 900)

    # Create Object nodes
    obj_numerator = ObjectNode()
    obj_numerator.set_position(50, 200)
    obj_numerator.type_selector.setCurrentIndex(1)  # Float
    obj_numerator.input_widget.setValue(10.0)
    editor.scene.addItem(obj_numerator.graphics)
    editor.nodes.append(obj_numerator)

    obj_denominator = ObjectNode()
    obj_denominator.set_position(50, 400)
    obj_denominator.type_selector.setCurrentIndex(1)  # Float
    obj_denominator.input_widget.setValue(0.0)  # This will cause division by zero!
    editor.scene.addItem(obj_denominator.graphics)
    editor.nodes.append(obj_denominator)

    # Create Divide node
    divide_node = DivideNode()
    divide_node.set_position(350, 300)
    editor.scene.addItem(divide_node.graphics)
    editor.nodes.append(divide_node)

    # Create View node
    view_node = ViewNode()
    view_node.set_position(650, 300)
    editor.scene.addItem(view_node.graphics)
    editor.nodes.append(view_node)
    editor.view_nodes.append(view_node)

    # Connect nodes: numerator → divide, denominator → divide, divide → view
    edge1 = Edge(obj_numerator.output_sockets[0], divide_node.input_sockets[0])
    editor.scene.addItem(edge1.graphics)
    edge1.update_positions()

    edge2 = Edge(obj_denominator.output_sockets[0], divide_node.input_sockets[1])
    editor.scene.addItem(edge2.graphics)
    edge2.update_positions()

    edge3 = Edge(divide_node.output_sockets[0], view_node.input_sockets[0])
    editor.scene.addItem(edge3.graphics)
    edge3.update_positions()

    # Instructions
    print("=== Error Handling Demo ===")
    print()
    print("This example demonstrates the error handling system:")
    print()
    print("Current Setup:")
    print("  • Numerator: 10.0")
    print("  • Denominator: 0.0 (will cause ZeroDivisionError!)")
    print()
    print("What happens:")
    print("  1. Division by zero error is caught immediately")
    print("  2. A toast notification appears at the bottom-right")
    print("  3. Graph execution is PAUSED (check status bar)")
    print("  4. Only ONE toast is shown for this error")
    print()
    print("To Resolve:")
    print("  1. Change the denominator to a non-zero value (e.g., 2.0)")
    print("  2. Click the '✕' button on the toast to dismiss it")
    print("  3. Execution will automatically resume")
    print("  4. If error is fixed, the graph continues normally")
    print("  5. If error persists, a new toast appears and execution pauses again")
    print()
    print("Visual Indicators:")
    print("  • Status bar shows: '⏸ Execution Paused' when error is present")
    print("  • Status bar shows: '▶ Execution Resumed' after closing toast")
    print()
    print("Try This:")
    print("  • Fix the error, then close the toast")
    print("  • Try setting denominator back to 0 to see the error again")
    print("  • Notice how only one toast appears per unique error")
    print()

    editor.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
