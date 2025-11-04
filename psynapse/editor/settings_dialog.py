"""Settings dialog for managing environment variables."""

import json
from pathlib import Path
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    """Dialog for managing environment variables for backend execution."""

    def __init__(self, parent=None):
        """Initialize the settings dialog.

        Args:
            parent: Parent widget (typically the main window)
        """
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(700, 500)

        # Path to store settings
        self.settings_path = Path.home() / ".psynapse" / "settings.json"
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing environment variables
        self.env_vars = self._load_settings()

        # Create UI
        self._create_ui()

    def _create_ui(self):
        """Create the dialog UI."""
        layout = QVBoxLayout()

        # Title and description
        title_label = QLabel("Environment Variables")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        description_label = QLabel(
            "Set environment variables that will be available during node graph execution.\n"
            "For example, add OPENAI_API_KEY for nodes that use the OpenAI SDK."
        )
        description_label.setStyleSheet("color: #666666; margin-bottom: 10px;")
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        # Table to display environment variables
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Variable Name", "Value"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 250)
        layout.addWidget(self.table)

        # Populate table with existing variables
        self._populate_table()

        # Add/Edit section
        add_section = QWidget()
        add_layout = QHBoxLayout()
        add_layout.setContentsMargins(0, 0, 0, 0)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Variable name (e.g., OPENAI_API_KEY)")
        add_layout.addWidget(QLabel("Name:"))
        add_layout.addWidget(self.name_input)

        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Value")
        self.value_input.setEchoMode(QLineEdit.Password)  # Hide values for security
        add_layout.addWidget(QLabel("Value:"))
        add_layout.addWidget(self.value_input)

        # Toggle visibility button
        self.show_value_btn = QPushButton("👁")
        self.show_value_btn.setFixedWidth(40)
        self.show_value_btn.setCheckable(True)
        self.show_value_btn.toggled.connect(self._toggle_value_visibility)
        add_layout.addWidget(self.show_value_btn)

        add_section.setLayout(add_layout)
        layout.addWidget(add_section)

        # Buttons
        button_layout = QHBoxLayout()

        add_button = QPushButton("Add / Update")
        add_button.clicked.connect(self._add_or_update_variable)
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(add_button)

        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self._remove_variable)
        remove_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        button_layout.addWidget(remove_button)

        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _populate_table(self):
        """Populate the table with current environment variables."""
        self.table.setRowCount(len(self.env_vars))
        for i, (name, value) in enumerate(self.env_vars.items()):
            # Name
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, name_item)

            # Value (masked)
            masked_value = "*" * min(len(value), 20) if value else ""
            value_item = QTableWidgetItem(masked_value)
            value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
            value_item.setData(Qt.UserRole, value)  # Store actual value
            self.table.setItem(i, 1, value_item)

    def _toggle_value_visibility(self, checked):
        """Toggle the visibility of the value input field.

        Args:
            checked: Whether the button is checked (show values)
        """
        if checked:
            self.value_input.setEchoMode(QLineEdit.Normal)
            self.show_value_btn.setText("🙈")
        else:
            self.value_input.setEchoMode(QLineEdit.Password)
            self.show_value_btn.setText("👁")

    def _add_or_update_variable(self):
        """Add or update an environment variable."""
        name = self.name_input.text().strip()
        value = self.value_input.text()

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a variable name.")
            return

        # Add or update the variable
        self.env_vars[name] = value

        # Save to file
        self._save_settings()

        # Refresh table
        self._populate_table()

        # Clear inputs
        self.name_input.clear()
        self.value_input.clear()

        # Show confirmation
        QMessageBox.information(
            self,
            "Success",
            f"Environment variable '{name}' has been saved.",
        )

    def _remove_variable(self):
        """Remove the selected environment variable."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self, "No Selection", "Please select a variable to remove."
            )
            return

        # Get the variable name from the table
        name_item = self.table.item(current_row, 0)
        if name_item:
            name = name_item.text()

            # Confirm deletion
            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to remove '{name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                # Remove from dictionary
                if name in self.env_vars:
                    del self.env_vars[name]

                # Save to file
                self._save_settings()

                # Refresh table
                self._populate_table()

    def _load_settings(self) -> Dict[str, str]:
        """Load settings from file.

        Returns:
            Dictionary of environment variables
        """
        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r") as f:
                    data = json.load(f)
                    return data.get("env_vars", {})
            except Exception:
                return {}
        return {}

    def _save_settings(self):
        """Save settings to file."""
        try:
            data = {"env_vars": self.env_vars}
            with open(self.settings_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save settings: {str(e)}",
            )

    def get_env_vars(self) -> Dict[str, str]:
        """Get the current environment variables.

        Returns:
            Dictionary of environment variables
        """
        return self.env_vars.copy()

    @staticmethod
    def load_env_vars() -> Dict[str, str]:
        """Load environment variables from settings file.

        Returns:
            Dictionary of environment variables
        """
        settings_path = Path.home() / ".psynapse" / "settings.json"
        if settings_path.exists():
            try:
                with open(settings_path, "r") as f:
                    data = json.load(f)
                    return data.get("env_vars", {})
            except Exception:
                return {}
        return {}
