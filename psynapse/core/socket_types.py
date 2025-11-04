from enum import Enum


class SocketDataType(Enum):
    """Data types for socket values."""

    ANY = "any"
    INT = "int"
    FLOAT = "float"
    STRING = "str"
    BOOL = "bool"

    def __str__(self):
        return self.value

    @classmethod
    def from_string(cls, type_str: str):
        """Convert string to SocketDataType."""
        type_map = {
            "any": cls.ANY,
            "int": cls.INT,
            "float": cls.FLOAT,
            "str": cls.STRING,
            "string": cls.STRING,
            "bool": cls.BOOL,
        }
        return type_map.get(type_str.lower(), cls.ANY)

    def get_default_value(self):
        """Get default value for this type."""
        defaults = {
            SocketDataType.ANY: None,
            SocketDataType.INT: 0,
            SocketDataType.FLOAT: 0.0,
            SocketDataType.STRING: "",
            SocketDataType.BOOL: False,
        }
        return defaults.get(self, None)

    def validate(self, value):
        """Validate and convert value to this type."""
        if self == SocketDataType.ANY:
            return value

        try:
            if self == SocketDataType.INT:
                return int(value)
            elif self == SocketDataType.FLOAT:
                return float(value)
            elif self == SocketDataType.STRING:
                return str(value)
            elif self == SocketDataType.BOOL:
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes")
                return bool(value)
        except (TypeError, ValueError):
            return self.get_default_value()

        return value

    def needs_input_widget(self):
        """Check if this type needs an input widget."""
        return self in (
            SocketDataType.INT,
            SocketDataType.FLOAT,
            SocketDataType.STRING,
            SocketDataType.BOOL,
        )
