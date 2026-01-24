import { memo, useCallback, useMemo, useState } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { NodeData } from "../types/schema";

const FunctionNode = ({ data, id }: NodeProps<NodeData>) => {
  const params = data.params || [];
  const edges = data.edges || [];
  // Get returns array - default to single "output" handle for backward compatibility
  const returns = data.returns || [{ name: "output", type: "any" }];
  const hasMultipleOutputs = returns.length > 1;

  // State for accordion expansion (default parameters)
  const [defaultsExpanded, setDefaultsExpanded] = useState(false);

  // Filter params: only show those WITHOUT default values in the node
  const paramsWithoutDefaults = useMemo(() => {
    return params.filter((param) => param.default === undefined);
  }, [params]);

  // Filter params: those WITH default values (for accordion)
  const paramsWithDefaults = useMemo(() => {
    return params.filter((param) => param.default !== undefined);
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
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "10px",
        }}
      >
        <div
          style={{
            fontWeight: "bold",
            color: "#333",
            fontSize: "14px",
          }}
        >
          {data.label}
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
            border: "1px solid #ddd",
            borderRadius: "4px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.2s",
          }}
          title="Open node panel"
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "#f0f0f0";
            e.currentTarget.style.borderColor = "#4a90e2";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
            e.currentTarget.style.borderColor = "#ddd";
          }}
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#666"
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

      {paramsWithoutDefaults.map((param) => {
        const isConnected = connectedInputs.has(param.name);
        return (
          <div
            key={param.name}
            style={{
              marginBottom: "8px",
              position: "relative",
            }}
          >
            <Handle
              type="target"
              position={Position.Left}
              id={param.name}
              style={{
                background: "#4a90e2",
                width: "10px",
                height: "10px",
                position: "absolute",
                left: "-15px",
                top: "50%",
                transform: "translateY(-50%)",
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

      {/* Collapsible accordion for params with defaults */}
      {paramsWithDefaults.length > 0 && (
        <div
          style={{
            marginTop: "8px",
            borderTop: "1px solid #eee",
            paddingTop: "8px",
          }}
        >
          <button
            onClick={() => setDefaultsExpanded(!defaultsExpanded)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              background: "none",
              border: "none",
              padding: "4px 0",
              cursor: "pointer",
              fontSize: "11px",
              color: "#666",
              width: "100%",
              textAlign: "left",
            }}
          >
            <span
              style={{
                display: "inline-block",
                transition: "transform 0.2s ease",
                transform: defaultsExpanded ? "rotate(90deg)" : "rotate(0deg)",
                fontSize: "10px",
              }}
            >
              ▶
            </span>
            <span>Defaults ({paramsWithDefaults.length})</span>
          </button>

          {/* Expanded content with handles */}
          {defaultsExpanded && (
            <div style={{ marginTop: "6px" }}>
              {paramsWithDefaults.map((param) => {
                const isConnected = connectedInputs.has(param.name);
                return (
                  <div
                    key={param.name}
                    style={{
                      marginBottom: "8px",
                      position: "relative",
                    }}
                  >
                    <Handle
                      type="target"
                      position={Position.Left}
                      id={param.name}
                      style={{
                        background: "#4a90e2",
                        width: "10px",
                        height: "10px",
                        position: "absolute",
                        left: "-15px",
                        top: "50%",
                        transform: "translateY(-50%)",
                      }}
                    />
                    <label
                      style={{
                        display: "block",
                        fontSize: "11px",
                        color: "#666",
                      }}
                    >
                      {param.name} ({param.type})
                      {isConnected && (
                        <span style={{ color: "#4a90e2", marginLeft: "4px" }}>●</span>
                      )}
                      {!isConnected && (
                        <span style={{ color: "#999", marginLeft: "4px", fontStyle: "italic" }}>
                          = {typeof param.default === "string" ? `"${param.default}"` : String(param.default)}
                        </span>
                      )}
                    </label>
                  </div>
                );
              })}
            </div>
          )}

          {/* Hidden handles when collapsed (needed for connections to still work) */}
          {!defaultsExpanded &&
            paramsWithDefaults.map((param) => (
              <Handle
                key={`default-${param.name}`}
                type="target"
                position={Position.Left}
                id={param.name}
                style={{
                  background: "#4a90e2",
                  width: "10px",
                  height: "10px",
                  opacity: 0,
                }}
              />
            ))}
        </div>
      )}

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
