import { memo, useCallback, useMemo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { NodeData } from "../types/schema";

const FunctionNode = ({ data, id }: NodeProps<NodeData>) => {
  const params = data.params || [];
  const edges = data.edges || [];
  // Get returns array - default to single "output" handle for backward compatibility
  const returns = data.returns || [{ name: "output", type: "any" }];
  const hasMultipleOutputs = returns.length > 1;

  // Filter params: only show those WITHOUT default values in the node
  const paramsWithoutDefaults = useMemo(() => {
    return params.filter((param) => param.default === undefined);
  }, [params]);

  // Check which input handles are connected
  const connectedInputs = useMemo(() => {
    const connected = new Set<string>();
    edges.forEach((edge: any) => {
      if (edge.target === id && edge.targetHandle) {
        connected.add(edge.targetHandle);
      }
    });
    return connected;
  }, [edges, id]);

  const handleInputChange = useCallback(
    (paramName: string, value: string) => {
      // Update node data
      if (data.onChange) {
        data.onChange(id, paramName, value);
      }
    },
    [data, id],
  );

  // Determine border color based on execution status
  const getBorderColor = () => {
    if (data.executionStatus === "executing") {
      return "#ffc107"; // Yellow for executing
    } else if (data.executionStatus === "completed") {
      return "#28a745"; // Green for completed
    } else if (data.executionStatus === "error") {
      return "#dc3545"; // Red for error
    }
    return "#4a90e2"; // Default blue
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
        background: "#ffffff",
        minWidth: "200px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
        transition: "border-color 0.3s ease, border-width 0.3s ease",
      }}
    >
      <div
        style={{
          fontWeight: "bold",
          marginBottom: "10px",
          color: "#333",
          fontSize: "14px",
        }}
      >
        {data.label}
      </div>

      {paramsWithoutDefaults.map((param, index) => {
        const isConnected = connectedInputs.has(param.name);
        return (
          <div key={param.name} style={{ marginBottom: "8px" }}>
            <Handle
              type="target"
              position={Position.Left}
              id={param.name}
              style={{
                top: `${50 + index * 40}px`,
                background: "#4a90e2",
                width: "10px",
                height: "10px",
              }}
            />
            <label
              style={{
                display: "block",
                fontSize: "11px",
                color: "#666",
                marginBottom: "3px",
              }}
            >
              {param.name} ({param.type})
              {isConnected && (
                <span style={{ color: "#4a90e2", marginLeft: "4px" }}>●</span>
              )}
            </label>
            {!isConnected &&
              (param.literal_values && param.literal_values.length > 0 ? (
                <select
                  value={
                    data[param.name] ??
                    (param.default !== undefined
                      ? param.default
                      : param.literal_values[0])
                  }
                  onChange={(e) => handleInputChange(param.name, e.target.value)}
                  style={{
                    width: "100%",
                    padding: "4px",
                    border: "1px solid #ddd",
                    borderRadius: "4px",
                    fontSize: "12px",
                    boxSizing: "border-box",
                    cursor: "pointer",
                  }}
                >
                  {param.literal_values.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  defaultValue={data[param.name] || ""}
                  onChange={(e) => handleInputChange(param.name, e.target.value)}
                  style={{
                    width: "100%",
                    padding: "4px",
                    border: "1px solid #ddd",
                    borderRadius: "4px",
                    fontSize: "12px",
                    boxSizing: "border-box",
                  }}
                  placeholder={`Enter ${param.type}`}
                />
              ))}
          </div>
        );
      })}

      {/* Add handles for params with defaults (hidden inputs, but need handles for connections) */}
      {params
        .filter((param) => param.default !== undefined)
        .map((param, index) => {
          const handleTop = 50 + (paramsWithoutDefaults.length + index) * 40;
          return (
            <Handle
              key={`default-${param.name}`}
              type="target"
              position={Position.Left}
              id={param.name}
              style={{
                top: `${handleTop}px`,
                background: "#4a90e2",
                width: "10px",
                height: "10px",
                opacity: 0, // Hide the handle visually but keep it functional
              }}
            />
          );
        })}

      {/* Output section for multiple outputs */}
      {hasMultipleOutputs ? (
        <div
          style={{
            marginTop: "10px",
            borderTop: "1px solid #eee",
            paddingTop: "8px",
          }}
        >
          <div
            style={{
              fontSize: "10px",
              color: "#999",
              marginBottom: "6px",
            }}
          >
            Outputs:
          </div>
          {returns.map((ret) => (
            <div
              key={ret.name}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "flex-end",
                marginBottom: "6px",
                position: "relative",
                minHeight: "20px",
                paddingRight: "8px",
              }}
            >
              <span
                style={{
                  fontSize: "11px",
                  color: "#666",
                }}
              >
                {ret.name}
              </span>
              <Handle
                type="source"
                position={Position.Right}
                id={ret.name}
                style={{
                  background: "#4a90e2",
                  width: "10px",
                  height: "10px",
                  position: "absolute",
                  right: "-5px",
                  top: "50%",
                  transform: "translateY(-50%)",
                }}
              />
            </div>
          ))}
        </div>
      ) : (
        /* Single output - default centered position */
        <Handle
          type="source"
          position={Position.Right}
          id={returns[0]?.name || "output"}
          style={{
            background: "#4a90e2",
            width: "10px",
            height: "10px",
          }}
        />
      )}
    </div>
  );
};

export default memo(FunctionNode);
