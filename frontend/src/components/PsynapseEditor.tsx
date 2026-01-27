import { useCallback, useRef, useState, useEffect } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Node,
  type OnConnect,
  ReactFlowProvider,
} from "reactflow";
import "reactflow/dist/style.css";

import FunctionNode from "./FunctionNode";
import ViewNode from "./ViewNode";
import VariableNode from "./VariableNode";
import ListNode from "./ListNode";
import NodeLibraryPanel from "./NodeLibraryPanel";
import TabbedPanel from "./TabbedPanel";
import NodePanel from "./NodePanel";
import SettingsModal from "./SettingsModal";
import { useSchema } from "../hooks/useSchema";
import { api } from "../utils/api";
import type { FunctionSchema, ExecutionStatus } from "../types/schema";

const nodeTypes = {
  functionNode: FunctionNode,
  viewNode: ViewNode,
  variableNode: VariableNode,
  listNode: ListNode,
};

let nodeId = 0;
const getId = () => `node_${nodeId++}`;

const PsynapseEditorInner = () => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);
  const [executing, setExecuting] = useState(false);
  const [statusHistory, setStatusHistory] = useState<ExecutionStatus[]>([]);
  const [abortExecution, setAbortExecution] = useState<(() => void) | null>(
    null,
  );
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [panelCollapsed, setPanelCollapsed] = useState(true);
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false);
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);

  const { schemas, loading, error } = useSchema();

  // Cleanup abort function on unmount
  useEffect(() => {
    return () => {
      if (abortExecution) {
        abortExecution();
      }
    };
  }, [abortExecution]);

  const onConnect: OnConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => {
        const newEdges = addEdge(connection, eds);
        // Update nodes with new edge information
        setTimeout(() => {
          setNodes((nds) =>
            nds.map((node) => ({
              ...node,
              data: {
                ...node.data,
                edges: newEdges,
              },
            })),
          );
        }, 0);
        return newEdges;
      });
    },
    [setEdges, setNodes],
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  // Callback to open node panel from dedicated button in node UI
  const handleOpenNodePanel = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId);
  }, []);

  const handleNodeDataChange = useCallback(
    (nodeId: string, paramName: string, value: string) => {
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === nodeId) {
            return {
              ...node,
              data: {
                ...node.data,
                [paramName]: value,
              },
            };
          }
          return node;
        }),
      );
    },
    [setNodes],
  );

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      if (!reactFlowWrapper.current || !reactFlowInstance) {
        return;
      }

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const dataStr = event.dataTransfer.getData("application/reactflow");

      if (!dataStr) {
        return;
      }

      const data = JSON.parse(dataStr);
      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      let newNode: Node;

      if (data.type === "viewNode") {
        newNode = {
          id: getId(),
          type: "viewNode",
          position,
          data: {
            label: "View",
            value: undefined,
            edges: [], // Will be updated with actual edges
            onOpenPanel: handleOpenNodePanel,
          },
        };
      } else if (data.type === "variableNode") {
        newNode = {
          id: getId(),
          type: "variableNode",
          position,
          data: {
            label: "Variable",
            variableName: "",
            variableType: "String",
            variableValue: "",
            edges: [], // Will be updated with actual edges
            onOpenPanel: handleOpenNodePanel,
          },
        };
      } else if (data.type === "listNode") {
        newNode = {
          id: getId(),
          type: "listNode",
          position,
          data: {
            label: "List",
            inputCount: 1,
            onChange: handleNodeDataChange,
            edges: [], // Will be updated with actual edges
            onOpenPanel: handleOpenNodePanel,
          },
        };
      } else if (data.type === "functionNode" && data.schema) {
        const schema: FunctionSchema = data.schema;
        const nodeData: any = {
          label: schema.name,
          functionName: schema.name,
          params: schema.params,
          returns: schema.returns,
          docstring: schema.docstring,
          onChange: handleNodeDataChange,
          edges: [], // Will be updated with actual edges
          onOpenPanel: handleOpenNodePanel,
        };

        // Initialize default values for parameters
        schema.params.forEach((param) => {
          // Use default value if available, then first literal value, otherwise empty string
          if (param.default !== undefined) {
            nodeData[param.name] = param.default;
          } else if (param.literal_values && param.literal_values.length > 0) {
            nodeData[param.name] = param.literal_values[0];
          } else {
            nodeData[param.name] = "";
          }
        });

        newNode = {
          id: getId(),
          type: "functionNode",
          position,
          data: nodeData,
        };
      } else {
        return;
      }

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes, handleNodeDataChange, handleOpenNodePanel],
  );

  const handleNodePanelUpdate = useCallback(
    (nodeId: string, updates: any) => {
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === nodeId) {
            if (node.type === "variableNode") {
              // For variable nodes, update label based on variable name
              return {
                ...node,
                data: {
                  ...node.data,
                  ...updates,
                  label: `Variable: ${updates.variableName || node.data.variableName || "unnamed"}`,
                },
              };
            } else if (node.type === "functionNode") {
              // For function nodes, just update the parameters
              return {
                ...node,
                data: {
                  ...node.data,
                  ...updates,
                },
              };
            }
          }
          return node;
        }),
      );
    },
    [setNodes],
  );

  const handlePaneClick = useCallback(() => {
    // Close the node panel when clicking on the canvas
    setSelectedNodeId(null);
  }, []);

  // Update nodes with edge information and onOpenPanel callback whenever edges change
  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: {
          ...node.data,
          edges: edges,
          onOpenPanel: handleOpenNodePanel,
        },
      })),
    );
  }, [edges, setNodes, handleOpenNodePanel]);

  // Clear selected node if it's deleted
  useEffect(() => {
    if (selectedNodeId && !nodes.find((node) => node.id === selectedNodeId)) {
      setSelectedNodeId(null);
    }
  }, [nodes, selectedNodeId]);

  const executeGraph = useCallback(async () => {
    try {
      setExecuting(true);
      setStatusHistory([]); // Clear previous execution history

      // Reset all node execution statuses before starting
      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          data: {
            ...node.data,
            executionStatus: undefined,
          },
        })),
      );

      // Prepare nodes for execution
      const nodesToExecute = nodes.map((node) => ({
        id: node.id,
        type: node.type,
        data: node.data,
      }));

      const edgesToExecute = edges.map((edge) => ({
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle,
        targetHandle: edge.targetHandle,
      }));

      // Execute the graph with streaming
      const cleanup = api.executeGraphStreaming(
        {
          nodes: nodesToExecute,
          edges: edgesToExecute,
        },
        // onStatus callback
        (status: ExecutionStatus) => {
          // Update status history
          setStatusHistory((prev) => {
            // Check if this is an update to an existing node
            const existingIndex = prev.findIndex(
              (s) =>
                s.node_id === status.node_id &&
                (s.status === "executing" || s.status === "progress" || s.status === "streaming"),
            );

            if (
              existingIndex !== -1 &&
              (status.status === "progress" ||
                status.status === "streaming" ||
                status.status === "completed" ||
                status.status === "error")
            ) {
              // Update existing executing/progress/streaming node
              const updated = [...prev];
              updated[existingIndex] = status;
              return updated;
            } else if (status.status === "executing") {
              // Add new executing node
              return [...prev, status];
            } else {
              // This shouldn't normally happen, but add it anyway
              return [...prev, status];
            }
          });

          // Update node visual status
          setNodes((nds) =>
            nds.map((node) => {
              if (node.id === status.node_id) {
                return {
                  ...node,
                  data: {
                    ...node.data,
                    executionStatus: status.status,
                  },
                };
              }
              return node;
            }),
          );
        },
        // onComplete callback
        (results: { [nodeId: string]: any }) => {
          // Update ViewNode values
          setNodes((nds) =>
            nds.map((node) => {
              if (node.type === "viewNode" && results[node.id] !== undefined) {
                return {
                  ...node,
                  data: {
                    ...node.data,
                    value: results[node.id],
                  },
                };
              }
              return node;
            }),
          );

          console.log("Execution results:", results);
          setExecuting(false);
          setAbortExecution(null);
        },
        // onError callback
        (error: string) => {
          console.error("Error executing graph:", error);
          alert("Error executing graph: " + error);
          setExecuting(false);
          setAbortExecution(null);
        },
      );

      setAbortExecution(() => cleanup);
    } catch (err) {
      console.error("Error starting graph execution:", err);
      alert(
        "Error starting graph execution: " +
          (err instanceof Error ? err.message : String(err)),
      );
      setExecuting(false);
      setAbortExecution(null);
    }
  }, [nodes, edges, setNodes, executing]);

  const handleSaveWorkflow = useCallback(() => {
    try {
      // Create workflow object with nodes and edges
      const workflow = {
        nodes: nodes,
        edges: edges,
      };

      // Convert to JSON string
      const jsonString = JSON.stringify(workflow, null, 2);

      // Create blob
      const blob = new Blob([jsonString], { type: "application/json" });

      // Create download link
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;

      // Generate filename with timestamp
      const timestamp = new Date()
        .toISOString()
        .replace(/[:.]/g, "-")
        .slice(0, 19);
      link.download = `workflow-${timestamp}.json`;

      // Trigger download
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      console.log("Workflow saved successfully");
    } catch (err) {
      console.error("Error saving workflow:", err);
      alert(
        "Error saving workflow: " +
          (err instanceof Error ? err.message : String(err)),
      );
    }
  }, [nodes, edges]);

  const handleOpenWorkflow = useCallback(() => {
    try {
      // Trigger file input click
      if (fileInputRef.current) {
        fileInputRef.current.click();
      }
    } catch (err) {
      console.error("Error opening file dialog:", err);
      alert(
        "Error opening file dialog: " +
          (err instanceof Error ? err.message : String(err)),
      );
    }
  }, []);

  const handleFileInputChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) {
        return;
      }

      const reader = new FileReader();

      reader.onload = (e) => {
        try {
          const content = e.target?.result as string;
          if (!content) {
            throw new Error("File is empty");
          }

          // Parse JSON
          const workflow = JSON.parse(content);

          // Validate structure
          if (!workflow.nodes || !Array.isArray(workflow.nodes)) {
            throw new Error(
              'Invalid workflow file: missing or invalid "nodes" array',
            );
          }
          if (!workflow.edges || !Array.isArray(workflow.edges)) {
            throw new Error(
              'Invalid workflow file: missing or invalid "edges" array',
            );
          }

          // Reset execution state
          if (abortExecution) {
            abortExecution();
          }
          setStatusHistory([]);
          setExecuting(false);
          setAbortExecution(null);
          setSelectedNodeId(null);

          // Update node IDs counter to avoid conflicts
          const maxNodeId = workflow.nodes.reduce((max: number, node: any) => {
            const match = node.id.match(/^node_(\d+)$/);
            if (match) {
              return Math.max(max, parseInt(match[1], 10));
            }
            return max;
          }, -1);
          if (maxNodeId >= 0) {
            nodeId = maxNodeId + 1;
          }

          // Restore onChange handlers for function nodes and list nodes
          const nodesWithHandlers = workflow.nodes.map((node: any) => {
            if (node.type === "functionNode" && node.data) {
              return {
                ...node,
                data: {
                  ...node.data,
                  onChange: handleNodeDataChange,
                },
              };
            } else if (node.type === "listNode" && node.data) {
              return {
                ...node,
                data: {
                  ...node.data,
                  onChange: handleNodeDataChange,
                },
              };
            }
            return node;
          });

          // Load workflow
          setNodes(nodesWithHandlers);
          setEdges(workflow.edges);

          // Fit view after loading
          if (reactFlowInstance) {
            setTimeout(() => {
              reactFlowInstance.fitView();
            }, 0);
          }

          console.log("Workflow loaded successfully");
        } catch (err) {
          console.error("Error loading workflow:", err);
          alert(
            "Error loading workflow: " +
              (err instanceof Error ? err.message : String(err)),
          );
        }
      };

      reader.onerror = () => {
        alert("Error reading file. Please try again.");
      };

      reader.readAsText(file);

      // Reset file input so the same file can be loaded again
      if (event.target) {
        event.target.value = "";
      }
    },
    [
      abortExecution,
      setNodes,
      setEdges,
      reactFlowInstance,
      handleNodeDataChange,
    ],
  );

  // Keyboard shortcuts for execution, save, open, and settings
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check for Ctrl+Enter (Windows/Linux) or Cmd+Enter (Mac) - Execute
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        if (!executing) {
          executeGraph();
        }
      }
      // Check for Ctrl+S (Windows/Linux) or Cmd+S (Mac) - Save
      else if ((event.ctrlKey || event.metaKey) && event.key === "s") {
        event.preventDefault();
        handleSaveWorkflow();
      }
      // Check for Ctrl+O (Windows/Linux) or Cmd+O (Mac) - Open
      else if ((event.ctrlKey || event.metaKey) && event.key === "o") {
        event.preventDefault();
        handleOpenWorkflow();
      }
      // Check for Ctrl+, (Windows/Linux) or Cmd+, (Mac) - Settings
      else if ((event.ctrlKey || event.metaKey) && event.key === ",") {
        event.preventDefault();
        setSettingsModalOpen(true);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [executing, executeGraph, handleSaveWorkflow, handleOpenWorkflow]);

  return (
    <div style={{ display: "flex", width: "100vw", height: "100vh" }}>
      {/* Hidden file input for Open functionality */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        style={{ display: "none" }}
        onChange={handleFileInputChange}
      />

      <NodeLibraryPanel
        schemas={schemas}
        loading={loading}
        error={error}
        isCollapsed={leftPanelCollapsed}
        onCollapseToggle={() => setLeftPanelCollapsed(!leftPanelCollapsed)}
      />

      <div style={{ flex: 1, position: "relative" }}>
        <div
          style={{
            position: "absolute",
            top: "10px",
            left: leftPanelCollapsed ? "10px" : "270px",
            right: panelCollapsed ? "10px" : "410px",
            zIndex: 10,
            display: "flex",
            gap: "8px",
            transition: "left 0.3s ease-in-out, right 0.3s ease-in-out",
            justifyContent: "flex-end",
          }}
        >
          <button
            onClick={() => setSettingsModalOpen(true)}
            style={{
              padding: "10px 20px",
              background: "#6c757d",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              fontSize: "14px",
              fontWeight: "600",
              cursor: "pointer",
              boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
              transition: "all 0.2s",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
            title={`Settings (${navigator.platform.toUpperCase().indexOf("MAC") >= 0 ? "⌘" : "Ctrl"}+,)`}
          >
            <span>Settings</span>
            <span
              style={{
                fontSize: "11px",
                opacity: 0.8,
                backgroundColor: "rgba(255,255,255,0.2)",
                padding: "2px 6px",
                borderRadius: "3px",
              }}
            >
              {navigator.platform.toUpperCase().indexOf("MAC") >= 0
                ? "⌘"
                : "Ctrl"}
              +,
            </span>
          </button>

          <button
            onClick={handleOpenWorkflow}
            style={{
              padding: "10px 20px",
              background: "#6c757d",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              fontSize: "14px",
              fontWeight: "600",
              cursor: "pointer",
              boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
              transition: "all 0.2s",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
            title={`Open workflow (${navigator.platform.toUpperCase().indexOf("MAC") >= 0 ? "⌘" : "Ctrl"}+O)`}
          >
            <span>Open</span>
            <span
              style={{
                fontSize: "11px",
                opacity: 0.8,
                backgroundColor: "rgba(255,255,255,0.2)",
                padding: "2px 6px",
                borderRadius: "3px",
              }}
            >
              {navigator.platform.toUpperCase().indexOf("MAC") >= 0
                ? "⌘"
                : "Ctrl"}
              +O
            </span>
          </button>

          <button
            onClick={handleSaveWorkflow}
            style={{
              padding: "10px 20px",
              background: "#007bff",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              fontSize: "14px",
              fontWeight: "600",
              cursor: "pointer",
              boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
              transition: "all 0.2s",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
            title={`Save workflow (${navigator.platform.toUpperCase().indexOf("MAC") >= 0 ? "⌘" : "Ctrl"}+S)`}
          >
            <span>Save</span>
            <span
              style={{
                fontSize: "11px",
                opacity: 0.8,
                backgroundColor: "rgba(255,255,255,0.2)",
                padding: "2px 6px",
                borderRadius: "3px",
              }}
            >
              {navigator.platform.toUpperCase().indexOf("MAC") >= 0
                ? "⌘"
                : "Ctrl"}
              +S
            </span>
          </button>

          <button
            onClick={executeGraph}
            disabled={executing}
            style={{
              padding: "10px 20px",
              background: executing ? "#6c757d" : "#28a745",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              fontSize: "14px",
              fontWeight: "600",
              cursor: executing ? "not-allowed" : "pointer",
              boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
              transition: "all 0.2s",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
            title={`Execute graph (${navigator.platform.toUpperCase().indexOf("MAC") >= 0 ? "⌘" : "Ctrl"}+Enter)`}
          >
            <span>{executing ? "Executing..." : "Execute"}</span>
            {!executing && (
              <span
                style={{
                  fontSize: "11px",
                  opacity: 0.8,
                  backgroundColor: "rgba(255,255,255,0.2)",
                  padding: "2px 6px",
                  borderRadius: "3px",
                }}
              >
                {navigator.platform.toUpperCase().indexOf("MAC") >= 0
                  ? "⌘"
                  : "Ctrl"}
                +↵
              </span>
            )}
          </button>
        </div>

        {/* Floating Node Properties Panel */}
        {selectedNodeId && nodes.find((node) => node.id === selectedNodeId) && (
          <div
            style={{
              position: "absolute",
              top: "60px",
              left: leftPanelCollapsed ? "10px" : "270px",
              right: panelCollapsed ? "10px" : "410px",
              zIndex: 9,
              transition: "left 0.3s ease-in-out, right 0.3s ease-in-out",
              display: "flex",
              justifyContent: "flex-end",
              pointerEvents: "none", // Allow events to pass through container
            }}
          >
            <div style={{ pointerEvents: "auto" }}>
              {" "}
              {/* Re-enable events for panel itself */}
              <NodePanel
                selectedNode={
                  nodes.find((node) => node.id === selectedNodeId) || null
                }
                onClose={() => setSelectedNodeId(null)}
                onUpdate={handleNodePanelUpdate}
              />
            </div>
          </div>
        )}

        <div
          ref={reactFlowWrapper}
          style={{
            width: "100%",
            height: "100%",
            paddingLeft: leftPanelCollapsed ? "0px" : "260px",
            paddingRight: panelCollapsed ? "0px" : "400px",
            transition:
              "padding-left 0.3s ease-in-out, padding-right 0.3s ease-in-out",
            boxSizing: "border-box",
          }}
        >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onPaneClick={handlePaneClick}
            onInit={setReactFlowInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>
      </div>

      <TabbedPanel
        statusHistory={statusHistory}
        isCollapsed={panelCollapsed}
        onCollapseToggle={() => setPanelCollapsed(!panelCollapsed)}
      />

      <SettingsModal
        isOpen={settingsModalOpen}
        onClose={() => setSettingsModalOpen(false)}
      />
    </div>
  );
};

const PsynapseEditor = () => {
  return (
    <ReactFlowProvider>
      <PsynapseEditorInner />
    </ReactFlowProvider>
  );
};

export default PsynapseEditor;
