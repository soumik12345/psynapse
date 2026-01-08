import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { NodeData } from "../types/schema";

const VariableNode = ({ data, id }: NodeProps<NodeData>) => {
  const variableName = data.variableName || "unnamed";

  // Determine border color based on execution status
  const getBorderColor = () => {
    if (data.executionStatus === "executing") {
      return "#ffc107"; // Yellow for executing
    } else if (data.executionStatus === "completed") {
      return "#28a745"; // Green for completed
    } else if (data.executionStatus === "error") {
      return "#dc3545"; // Red for error
    }
    return "#9333ea"; // Purple for Variable nodes
  };

  const getBorderWidth = () => {
    if (data.executionStatus) {
      return "3px"; // Thicker border during/after execution
    }
    return "2px";
  };

  return (
    <div
      style={{
        padding: "10px",
        border: `${getBorderWidth()} solid ${getBorderColor()}`,
        borderRadius: "8px",
        background: "#faf5ff",
        minWidth: "180px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
        transition: "border-color 0.3s ease, border-width 0.3s ease",
        cursor: "pointer",
      }}
    >
      <div
        style={{
          fontWeight: "bold",
          marginBottom: "8px",
          color: "#6b21a8",
          fontSize: "14px",
        }}
      >
        Variable: {variableName}
      </div>

      {/* Show type and value preview */}
      <div
        style={{
          fontSize: "11px",
          color: "#7c3aed",
          marginBottom: "4px",
          display: "flex",
          alignItems: "center",
          gap: "6px",
        }}
      >
        <span>Type: {data.variableType || "String"}</span>
        {data.variableType === "String" && data.textContentFormat && (
          <span
            title="LLM Message Content enabled"
            style={{
              fontSize: "12px",
              backgroundColor: "#9333ea",
              color: "#ffffff",
              padding: "2px 6px",
              borderRadius: "3px",
              fontWeight: "600",
              lineHeight: "1",
            }}
          >
            {"{T}"}
          </span>
        )}
        {data.variableType === "Image" && data.imageContentFormat && (
          <span
            title="LLM Image Content enabled"
            style={{
              fontSize: "12px",
              backgroundColor: "#9333ea",
              color: "#ffffff",
              padding: "2px 6px",
              borderRadius: "3px",
              fontWeight: "600",
              lineHeight: "1",
            }}
          >
            {"{I}"}
          </span>
        )}
      </div>

      {data.variableValue !== undefined && data.variableValue !== "" && (
        <div
          style={{
            padding: "4px 6px",
            background: "#ffffff",
            border: "1px solid #c084fc",
            borderRadius: "4px",
            fontSize: "11px",
            color: "#333",
            fontFamily: "monospace",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            maxWidth: "160px",
          }}
        >
          {(() => {
            const value = data.variableValue;
            const type = data.variableType;

            if (type === "Image" && typeof value === "string" && value.startsWith("data:image")) {
              return (
                <img
                  src={value}
                  alt="Preview"
                  style={{
                    maxWidth: "148px",
                    maxHeight: "80px",
                    borderRadius: "2px",
                    display: "block",
                  }}
                />
              );
            } else if (type === "List" && Array.isArray(value)) {
              if (value.length === 0) {
                return "[]";
              }
              // Show first 2 items with truncation
              const preview = value
                .slice(0, 2)
                .map((item) => {
                  if (typeof item === "string") return `"${item}"`;
                  if (typeof item === "object") return "{}";
                  return String(item);
                })
                .join(", ");
              return value.length > 2 ? `[${preview}, ...]` : `[${preview}]`;
            } else if (
              type === "Object" &&
              typeof value === "object" &&
              value !== null &&
              !Array.isArray(value)
            ) {
              const keys = Object.keys(value);
              if (keys.length === 0) {
                return "{}";
              }
              // Show first 2 keys with truncation
              const preview = keys
                .slice(0, 2)
                .map((key) => {
                  const val = value[key];
                  const valStr =
                    typeof val === "string" ? `"${val}"` : String(val);
                  return `${key}: ${valStr}`;
                })
                .join(", ");
              return keys.length > 2 ? `{${preview}, ...}` : `{${preview}}`;
            }

            return String(value);
          })()}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Right}
        id="output"
        style={{
          background: "#9333ea",
          width: "10px",
          height: "10px",
        }}
      />
    </div>
  );
};

export default memo(VariableNode);
