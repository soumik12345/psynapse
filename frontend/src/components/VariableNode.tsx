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
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "8px",
        }}
      >
        <div
          style={{
            fontWeight: "bold",
            color: "#6b21a8",
            fontSize: "14px",
          }}
        >
          Variable: {variableName}
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (data.onOpenPanel) {
              data.onOpenPanel(id);
            }
          }}
          style={{
            padding: "4px 6px",
            background: "transparent",
            border: "1px solid #c084fc",
            borderRadius: "4px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.2s",
          }}
          title="Open node panel"
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "#ede9fe";
            e.currentTarget.style.borderColor = "#9333ea";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
            e.currentTarget.style.borderColor = "#c084fc";
          }}
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#6b21a8"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
            <polyline points="15 3 21 3 21 9" />
            <line x1="10" y1="14" x2="21" y2="3" />
          </svg>
        </button>
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
