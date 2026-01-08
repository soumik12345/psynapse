import { useState, useMemo } from "react";
import type { FunctionSchema } from "../types/schema";

interface NodeLibraryPanelProps {
  schemas: FunctionSchema[];
  loading: boolean;
  error: string | null;
  isCollapsed: boolean;
  onCollapseToggle: () => void;
}

const NodeLibraryPanel = ({
  schemas,
  loading,
  error,
  isCollapsed,
  onCollapseToggle,
}: NodeLibraryPanelProps) => {
  const [builtInExpanded, setBuiltInExpanded] = useState(true);
  const [nodepacksExpanded, setNodepacksExpanded] = useState<
    Record<string, boolean>
  >({});

  // Group schemas by nodepack
  const schemasByNodepack = useMemo(() => {
    const grouped: Record<string, FunctionSchema[]> = {};

    schemas.forEach((schema) => {
      // Extract nodepack name from filepath
      // Example: nodepacks/basic/ops.py -> basic
      const pathParts = schema.filepath.split("/");
      const nodepackIndex = pathParts.findIndex((part) => part === "nodepacks");
      const nodepackName =
        nodepackIndex !== -1 && pathParts[nodepackIndex + 1]
          ? pathParts[nodepackIndex + 1]
          : "unknown";

      if (!grouped[nodepackName]) {
        grouped[nodepackName] = [];
      }
      grouped[nodepackName].push(schema);
    });

    return grouped;
  }, [schemas]);

  // Initialize expanded state for nodepacks
  useMemo(() => {
    const initialExpanded: Record<string, boolean> = {};
    Object.keys(schemasByNodepack).forEach((nodepack) => {
      if (!(nodepack in nodepacksExpanded)) {
        initialExpanded[nodepack] = true;
      }
    });
    if (Object.keys(initialExpanded).length > 0) {
      setNodepacksExpanded((prev) => ({ ...prev, ...initialExpanded }));
    }
  }, [schemasByNodepack, nodepacksExpanded]);

  const toggleNodepack = (nodepackName: string) => {
    setNodepacksExpanded((prev) => ({
      ...prev,
      [nodepackName]: !prev[nodepackName],
    }));
  };

  const onDragStart = (
    event: React.DragEvent,
    nodeType: "viewNode" | "variableNode" | "listNode" | "functionNode",
    schema?: FunctionSchema,
  ) => {
    const data = schema ? { type: "functionNode", schema } : { type: nodeType };

    event.dataTransfer.setData("application/reactflow", JSON.stringify(data));
    event.dataTransfer.effectAllowed = "move";
  };

  if (loading) {
    return (
      <div
        style={{
          position: "fixed",
          left: isCollapsed ? "-260px" : "0",
          top: 0,
          height: "100%",
          width: "260px",
          transition: "left 0.3s ease-in-out",
          zIndex: 1000,
          boxShadow: isCollapsed ? "none" : "2px 0 8px rgba(0,0,0,0.2)",
          display: "flex",
        }}
      >
        {/* Collapse/Uncollapse Button */}
        <button
          onClick={onCollapseToggle}
          style={{
            position: "absolute",
            right: "-40px",
            top: "50%",
            transform: "translateY(-50%)",
            width: "40px",
            height: "80px",
            background: "#ffffff",
            border: "1px solid #dee2e6",
            borderLeft: "none",
            borderRadius: "0 8px 8px 0",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "20px",
            color: "#6c757d",
            boxShadow: "2px 0 4px rgba(0,0,0,0.1)",
            transition: "background-color 0.2s",
            zIndex: 1,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "#f8f9fa";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "#ffffff";
          }}
          title={isCollapsed ? "Expand panel" : "Collapse panel"}
        >
          {isCollapsed ? "▶" : "◀"}
        </button>

        <div style={styles.panel}>
          <h3 style={styles.title}>Node Library</h3>
          <div style={styles.loading}>Loading nodes...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          position: "fixed",
          left: isCollapsed ? "-260px" : "0",
          top: 0,
          height: "100%",
          width: "260px",
          transition: "left 0.3s ease-in-out",
          zIndex: 1000,
          boxShadow: isCollapsed ? "none" : "2px 0 8px rgba(0,0,0,0.2)",
          display: "flex",
        }}
      >
        {/* Collapse/Uncollapse Button */}
        <button
          onClick={onCollapseToggle}
          style={{
            position: "absolute",
            right: "-40px",
            top: "50%",
            transform: "translateY(-50%)",
            width: "40px",
            height: "80px",
            background: "#ffffff",
            border: "1px solid #dee2e6",
            borderLeft: "none",
            borderRadius: "0 8px 8px 0",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "20px",
            color: "#6c757d",
            boxShadow: "2px 0 4px rgba(0,0,0,0.1)",
            transition: "background-color 0.2s",
            zIndex: 1,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "#f8f9fa";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "#ffffff";
          }}
          title={isCollapsed ? "Expand panel" : "Collapse panel"}
        >
          {isCollapsed ? "▶" : "◀"}
        </button>

        <div style={styles.panel}>
          <h3 style={styles.title}>Node Library</h3>
          <div style={styles.error}>Error: {error}</div>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        position: "fixed",
        left: isCollapsed ? "-260px" : "0",
        top: 0,
        height: "100%",
        width: "260px",
        transition: "left 0.3s ease-in-out",
        zIndex: 1000,
        boxShadow: isCollapsed ? "none" : "2px 0 8px rgba(0,0,0,0.2)",
        display: "flex",
      }}
    >
      {/* Collapse/Uncollapse Button */}
      <button
        onClick={onCollapseToggle}
        style={{
          position: "absolute",
          right: "-40px",
          top: "50%",
          transform: "translateY(-50%)",
          width: "40px",
          height: "80px",
          background: "#ffffff",
          border: "1px solid #dee2e6",
          borderLeft: "none",
          borderRadius: "0 8px 8px 0",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "20px",
          color: "#6c757d",
          boxShadow: "2px 0 4px rgba(0,0,0,0.1)",
          transition: "background-color 0.2s",
          zIndex: 1,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = "#f8f9fa";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = "#ffffff";
        }}
        title={isCollapsed ? "Expand panel" : "Collapse panel"}
      >
        {isCollapsed ? "▶" : "◀"}
      </button>

      <div style={styles.panel}>
        <h3 style={styles.title}>Node Library</h3>

        <div style={styles.section}>
          <button
            onClick={() => setBuiltInExpanded(!builtInExpanded)}
            style={{
              ...styles.sectionTitle,
              background: "none",
              border: "none",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: 0,
              width: "100%",
            }}
          >
            <span style={{ fontSize: "10px" }}>
              {builtInExpanded ? "▼" : "▶"}
            </span>
            <span>Built-in Nodes</span>
          </button>
          {builtInExpanded && (
            <>
              <div
                draggable
                onDragStart={(e) => onDragStart(e, "variableNode")}
                style={styles.nodeItem}
              >
                <div style={styles.nodeName}>Variable</div>
                <div style={styles.nodeDescription}>Store typed values</div>
              </div>
              <div
                draggable
                onDragStart={(e) => onDragStart(e, "listNode")}
                style={styles.nodeItem}
              >
                <div style={styles.nodeName}>List</div>
                <div style={styles.nodeDescription}>
                  Build lists from inputs
                </div>
              </div>
              <div
                draggable
                onDragStart={(e) => onDragStart(e, "viewNode")}
                style={styles.nodeItem}
              >
                <div style={styles.nodeName}>ViewNode</div>
                <div style={styles.nodeDescription}>Display output values</div>
              </div>
            </>
          )}
        </div>

        {/* Render each nodepack as a separate section */}
        {Object.keys(schemasByNodepack)
          .sort()
          .map((nodepackName) => (
            <div key={nodepackName} style={styles.section}>
              <button
                onClick={() => toggleNodepack(nodepackName)}
                style={{
                  ...styles.sectionTitle,
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: 0,
                  width: "100%",
                }}
              >
                <span style={{ fontSize: "10px" }}>
                  {nodepacksExpanded[nodepackName] ? "▼" : "▶"}
                </span>
                <span>{nodepackName}</span>
              </button>
              {nodepacksExpanded[nodepackName] &&
                schemasByNodepack[nodepackName].map((schema) => (
                  <div
                    key={schema.name}
                    draggable
                    onDragStart={(e) => onDragStart(e, "functionNode", schema)}
                    style={styles.nodeItem}
                  >
                    <div style={styles.nodeName}>{schema.name}</div>
                    <div style={styles.nodeDescription}>
                      {schema.params.length} inputs → {schema.returns.length}{" "}
                      outputs
                    </div>
                  </div>
                ))}
            </div>
          ))}
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  panel: {
    width: "260px",
    height: "100vh",
    background: "#f8f9fa",
    borderRight: "1px solid #dee2e6",
    padding: "20px",
    overflowY: "auto",
    boxSizing: "border-box",
  },
  title: {
    margin: "0 0 20px 0",
    fontSize: "18px",
    fontWeight: "bold",
    color: "#212529",
  },
  section: {
    marginBottom: "24px",
  },
  sectionTitle: {
    fontSize: "13px",
    fontWeight: "600",
    color: "#6c757d",
    textTransform: "uppercase",
    marginBottom: "12px",
    letterSpacing: "0.5px",
  },
  nodeItem: {
    padding: "12px",
    marginBottom: "8px",
    background: "#ffffff",
    border: "1px solid #dee2e6",
    borderRadius: "6px",
    cursor: "grab",
    transition: "all 0.2s",
    userSelect: "none",
  },
  nodeName: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#212529",
    marginBottom: "4px",
  },
  nodeDescription: {
    fontSize: "11px",
    color: "#6c757d",
  },
  loading: {
    padding: "12px",
    textAlign: "center",
    color: "#6c757d",
    fontSize: "14px",
  },
  error: {
    padding: "12px",
    background: "#f8d7da",
    color: "#721c24",
    borderRadius: "4px",
    fontSize: "13px",
  },
};

export default NodeLibraryPanel;
