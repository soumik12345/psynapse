import { memo, useCallback } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { NodeData } from "../types/schema";

const ListNode = ({ data, id }: NodeProps<NodeData>) => {
  const inputCount = data.inputCount || 1;

  // Determine border color based on execution status
  const getBorderColor = () => {
    if (data.executionStatus === "executing") {
      return "#ffc107"; // Yellow for executing
    } else if (data.executionStatus === "completed") {
      return "#28a745"; // Green for completed
    } else if (data.executionStatus === "error") {
      return "#dc3545"; // Red for error
    }
    return "#9333ea"; // Purple for List nodes
  };

  const getBorderWidth = () => {
    if (data.executionStatus) {
      return "3px"; // Thicker border during/after execution
    }
    return "2px";
  };

  const handleAddInput = useCallback(() => {
    if (data.onChange) {
      data.onChange(id, "inputCount", inputCount + 1);
    }
  }, [data, id, inputCount]);

  const handleRemoveInput = useCallback(
    (index: number) => {
      if (inputCount > 1 && data.onChange) {
        // Remove the input at the specified index
        data.onChange(id, "inputCount", inputCount - 1);
        // Also store which index was removed for edge cleanup
        data.onChange(id, "removedInputIndex", index);
      }
    },
    [data, id, inputCount],
  );

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
          marginBottom: "12px",
          color: "#6b21a8",
          fontSize: "14px",
        }}
      >
        List
      </div>

      {/* Input sockets */}
      <div style={{ marginBottom: "8px" }}>
        {Array.from({ length: inputCount }, (_, index) => (
          <div
            key={index}
            style={{
              display: "flex",
              alignItems: "center",
              marginBottom: "6px",
              position: "relative",
              minHeight: "24px",
            }}
          >
            <Handle
              type="target"
              position={Position.Left}
              id={`input-${index}`}
              style={{
                background: "#9333ea",
                width: "10px",
                height: "10px",
                position: "absolute",
                left: "-5px",
                top: "50%",
                transform: "translateY(-50%)",
              }}
            />
            <div
              style={{
                fontSize: "11px",
                color: "#7c3aed",
                marginLeft: "8px",
                fontFamily: "monospace",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              <span>[{index}]</span>
              {inputCount > 1 && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveInput(index);
                  }}
                  style={{
                    padding: "2px 4px",
                    backgroundColor: "transparent",
                    color: "#6b21a8",
                    border: "1px solid #c084fc",
                    borderRadius: "3px",
                    fontSize: "10px",
                    cursor: "pointer",
                    fontWeight: "400",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    transition: "all 0.2s",
                  }}
                  title="Remove input"
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = "#ede9fe";
                    e.currentTarget.style.borderColor = "#9333ea";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "transparent";
                    e.currentTarget.style.borderColor = "#c084fc";
                  }}
                >
                  🗑️
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Add Input Button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          handleAddInput();
        }}
        style={{
          padding: "4px 12px",
          backgroundColor: "#9333ea",
          color: "#ffffff",
          border: "none",
          borderRadius: "4px",
          fontSize: "11px",
          cursor: "pointer",
          fontWeight: "600",
          transition: "background-color 0.2s",
          width: "100%",
          marginBottom: "4px",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = "#7c3aed";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = "#9333ea";
        }}
      >
        + Add Input
      </button>

      {/* Output socket */}
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

export default memo(ListNode);
