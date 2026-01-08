import StatusPanel from "./StatusPanel";
import type { ExecutionStatus } from "../types/schema";

interface TabbedPanelProps {
  statusHistory: ExecutionStatus[];
  isCollapsed: boolean;
  onCollapseToggle: () => void;
}

const TabbedPanel = ({
  statusHistory,
  isCollapsed,
  onCollapseToggle,
}: TabbedPanelProps) => {
  return (
    <div
      style={{
        position: "fixed",
        right: isCollapsed ? "-400px" : "0",
        top: 0,
        height: "100%",
        width: "400px",
        transition: "right 0.3s ease-in-out",
        zIndex: 1000,
        boxShadow: isCollapsed ? "none" : "-2px 0 8px rgba(0,0,0,0.2)",
        display: "flex",
      }}
    >
      {/* Collapse/Uncollapse Button */}
      <button
        onClick={onCollapseToggle}
        style={{
          position: "absolute",
          left: "-40px",
          top: "50%",
          transform: "translateY(-50%)",
          width: "40px",
          height: "80px",
          background: "#ffffff",
          border: "1px solid #dee2e6",
          borderRight: "none",
          borderRadius: "8px 0 0 8px",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "20px",
          color: "#6c757d",
          boxShadow: "-2px 0 4px rgba(0,0,0,0.1)",
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
        {isCollapsed ? "◀" : "▶"}
      </button>

      {/* Panel Content */}
      <div
        style={{
          width: "100%",
          height: "100%",
          backgroundColor: "#f8f9fa",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "16px",
            backgroundColor: "#ffffff",
            borderBottom: "2px solid #dee2e6",
          }}
        >
          <h2
            style={{
              margin: 0,
              fontSize: "18px",
              fontWeight: "600",
              color: "#212529",
            }}
          >
            Execution Status
          </h2>
        </div>

        {/* Status Panel Content */}
        <div
          style={{
            flex: 1,
            overflow: "hidden",
            position: "relative",
          }}
        >
          <StatusPanel statusHistory={statusHistory} onClose={undefined} />
        </div>
      </div>
    </div>
  );
};

export default TabbedPanel;
