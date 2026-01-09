import React, { useState } from "react";
import type { ExecutionStatus } from "../types/schema";

interface StatusPanelProps {
  statusHistory: ExecutionStatus[];
  onClose?: () => void;
}

// Helper to check if string is a base64 encoded image
const isBase64Image = (str: string): boolean => {
  if (!str.startsWith("data:image")) return false;
  const base64Pattern = /^data:image\/(png|jpeg|jpg|gif|webp|svg\+xml);base64,/;
  return base64Pattern.test(str);
};

// Simple Markdown renderer component
const SimpleMarkdown = ({ content }: { content: string }) => {
  const renderMarkdown = (text: string) => {
    const lines = text.split("\n");
    const elements: React.ReactNode[] = [];
    let inCodeBlock = false;
    let codeBlockContent: string[] = [];

    lines.forEach((line, index) => {
      // Code block handling
      if (line.startsWith("```")) {
        if (!inCodeBlock) {
          inCodeBlock = true;
          codeBlockContent = [];
        } else {
          inCodeBlock = false;
          elements.push(
            <pre
              key={`code-${index}`}
              style={{
                backgroundColor: "#1e1e1e",
                color: "#d4d4d4",
                padding: "12px",
                borderRadius: "6px",
                overflow: "auto",
                fontSize: "12px",
                margin: "8px 0",
                fontFamily: "monospace",
              }}
            >
              <code>{codeBlockContent.join("\n")}</code>
            </pre>
          );
        }
        return;
      }

      if (inCodeBlock) {
        codeBlockContent.push(line);
        return;
      }

      // Headers
      if (line.startsWith("### ")) {
        elements.push(
          <h3
            key={index}
            style={{ margin: "12px 0 8px", fontSize: "14px", fontWeight: "bold" }}
          >
            {line.slice(4)}
          </h3>
        );
        return;
      }
      if (line.startsWith("## ")) {
        elements.push(
          <h2
            key={index}
            style={{ margin: "14px 0 10px", fontSize: "16px", fontWeight: "bold" }}
          >
            {line.slice(3)}
          </h2>
        );
        return;
      }
      if (line.startsWith("# ")) {
        elements.push(
          <h1
            key={index}
            style={{ margin: "16px 0 12px", fontSize: "18px", fontWeight: "bold" }}
          >
            {line.slice(2)}
          </h1>
        );
        return;
      }

      // Horizontal rule
      if (line.match(/^(-{3,}|\*{3,}|_{3,})$/)) {
        elements.push(
          <hr
            key={index}
            style={{ margin: "12px 0", border: "none", borderTop: "1px solid #ddd" }}
          />
        );
        return;
      }

      // Empty line
      if (line.trim() === "") {
        elements.push(<div key={index} style={{ height: "8px" }} />);
        return;
      }

      // List items
      if (line.match(/^[\-\*]\s/)) {
        elements.push(
          <div key={index} style={{ paddingLeft: "16px", margin: "4px 0" }}>
            • {renderInlineMarkdown(line.slice(2))}
          </div>
        );
        return;
      }

      // Numbered list
      const numberedMatch = line.match(/^(\d+)\.\s/);
      if (numberedMatch) {
        elements.push(
          <div key={index} style={{ paddingLeft: "16px", margin: "4px 0" }}>
            {numberedMatch[1]}. {renderInlineMarkdown(line.slice(numberedMatch[0].length))}
          </div>
        );
        return;
      }

      // Regular paragraph
      elements.push(
        <p key={index} style={{ margin: "6px 0", lineHeight: "1.5" }}>
          {renderInlineMarkdown(line)}
        </p>
      );
    });

    return <>{elements}</>;
  };

  const renderInlineMarkdown = (text: string): React.ReactNode[] => {
    const result: React.ReactNode[] = [];
    let remaining = text;
    let keyCounter = 0;

    while (remaining.length > 0) {
      // Bold **text** or __text__
      const boldMatch = remaining.match(/^(.*?)(\*\*|__)(.+?)\2(.*)$/);
      if (boldMatch) {
        if (boldMatch[1]) result.push(boldMatch[1]);
        result.push(<strong key={keyCounter++}>{boldMatch[3]}</strong>);
        remaining = boldMatch[4];
        continue;
      }

      // Italic *text* or _text_
      const italicMatch = remaining.match(/^(.*?)(\*|_)(.+?)\2(.*)$/);
      if (italicMatch) {
        if (italicMatch[1]) result.push(italicMatch[1]);
        result.push(<em key={keyCounter++}>{italicMatch[3]}</em>);
        remaining = italicMatch[4];
        continue;
      }

      // Inline code `text`
      const codeMatch = remaining.match(/^(.*?)`(.+?)`(.*)$/);
      if (codeMatch) {
        if (codeMatch[1]) result.push(codeMatch[1]);
        result.push(
          <code
            key={keyCounter++}
            style={{
              backgroundColor: "#f0f0f0",
              padding: "2px 6px",
              borderRadius: "3px",
              fontSize: "11px",
              fontFamily: "monospace",
            }}
          >
            {codeMatch[2]}
          </code>
        );
        remaining = codeMatch[3];
        continue;
      }

      // No more matches, add remaining text
      result.push(remaining);
      break;
    }

    return result;
  };

  return (
    <div style={{ fontFamily: "sans-serif", fontSize: "13px" }}>
      {renderMarkdown(content)}
    </div>
  );
};

// TreeView Component for structured rendering of objects and arrays
interface TreeViewProps {
  data: any;
  level?: number;
  parentKey?: string;
  renderMode?: "raw" | "markdown";
}

const TreeView = ({
  data,
  level = 0,
  parentKey = "root",
  renderMode = "raw",
}: TreeViewProps) => {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const toggleExpand = (key: string) => {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const indent = level * 16;

  if (data === null || data === undefined) {
    return <span style={{ color: "#999", fontStyle: "italic" }}>null</span>;
  }

  if (typeof data === "boolean") {
    return <span style={{ color: "#d73a49" }}>{data ? "true" : "false"}</span>;
  }

  if (typeof data === "number") {
    return <span style={{ color: "#005cc5" }}>{data}</span>;
  }

  if (typeof data === "string") {
    // Check if it's a base64 encoded image - always render as image
    if (isBase64Image(data)) {
      return (
        <div
          style={{
            marginTop: "8px",
            marginBottom: "8px",
            padding: "8px",
            border: "1px solid #e0e0e0",
            borderRadius: "4px",
            backgroundColor: "#f9f9f9",
            display: "inline-block",
          }}
        >
          <img
            src={data}
            alt="Image"
            style={{
              maxWidth: "100%",
              maxHeight: "300px",
              borderRadius: "4px",
              display: "block",
            }}
          />
          <div
            style={{
              marginTop: "4px",
              fontSize: "11px",
              color: "#6a737d",
              fontStyle: "italic",
            }}
          >
            Image ({data.split(",")[0].split("/")[1].split(";")[0]})
          </div>
        </div>
      );
    }

    // Render based on mode
    if (renderMode === "markdown") {
      return <SimpleMarkdown content={data} />;
    }

    return <span style={{ color: "#22863a" }}>"{data}"</span>;
  }

  if (Array.isArray(data)) {
    if (data.length === 0) {
      return <span style={{ color: "#6a737d" }}>[]</span>;
    }

    const key = `${parentKey}-array-${level}`;
    const isExpanded = expanded[key];

    return (
      <div style={{ marginLeft: level === 0 ? "0" : `${indent}px` }}>
        <span
          onClick={() => toggleExpand(key)}
          style={{
            cursor: "pointer",
            userSelect: "none",
            color: "#6a737d",
            marginRight: "4px",
          }}
        >
          {isExpanded ? "▼" : "▶"}
        </span>
        <span style={{ color: "#6a737d" }}>Array({data.length})</span>
        {isExpanded && (
          <div style={{ marginLeft: "12px", marginTop: "4px" }}>
            {data.map((item, index) => (
              <div key={index} style={{ marginBottom: "4px" }}>
                <span style={{ color: "#6a737d", marginRight: "8px" }}>
                  [{index}]:
                </span>
                <TreeView
                  data={item}
                  level={level + 1}
                  parentKey={`${key}-${index}`}
                  renderMode={renderMode}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (typeof data === "object") {
    const keys = Object.keys(data);
    if (keys.length === 0) {
      return <span style={{ color: "#6a737d" }}>{"{}"}</span>;
    }

    const key = `${parentKey}-object-${level}`;
    const isExpanded = expanded[key];

    return (
      <div style={{ marginLeft: level === 0 ? "0" : `${indent}px` }}>
        <span
          onClick={() => toggleExpand(key)}
          style={{
            cursor: "pointer",
            userSelect: "none",
            color: "#6a737d",
            marginRight: "4px",
          }}
        >
          {isExpanded ? "▼" : "▶"}
        </span>
        <span style={{ color: "#6a737d" }}>Object({keys.length})</span>
        {isExpanded && (
          <div style={{ marginLeft: "12px", marginTop: "4px" }}>
            {keys.map((k) => (
              <div key={k} style={{ marginBottom: "4px" }}>
                <span style={{ color: "#6f42c1", marginRight: "8px" }}>
                  {k}:
                </span>
                <TreeView
                  data={data[k]}
                  level={level + 1}
                  parentKey={`${key}-${k}`}
                  renderMode={renderMode}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return <span>{String(data)}</span>;
};

const StatusPanel = ({ statusHistory, onClose }: StatusPanelProps) => {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [renderModes, setRenderModes] = useState<Record<string, "raw" | "markdown">>({});

  const toggleExpanded = (nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  const toggleRenderMode = (nodeId: string) => {
    setRenderModes((prev) => ({
      ...prev,
      [nodeId]: prev[nodeId] === "markdown" ? "raw" : "markdown",
    }));
  };

  return (
    <div
      style={{
        width: "400px",
        height: "100%",
        backgroundColor: "#f8f9fa",
        borderLeft: "1px solid #dee2e6",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {onClose && (
        <div
          style={{
            padding: "16px",
            backgroundColor: "#ffffff",
            borderBottom: "2px solid #dee2e6",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
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
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              fontSize: "24px",
              color: "#6c757d",
              cursor: "pointer",
              padding: "0",
              width: "28px",
              height: "28px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              borderRadius: "4px",
              transition: "background-color 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "#e9ecef";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "transparent";
            }}
            title="Close panel"
          >
            ×
          </button>
        </div>
      )}

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: onClose ? "16px" : "16px 16px 16px 16px",
          paddingTop: onClose ? "16px" : "20px",
        }}
      >
        {statusHistory.length === 0 ? (
          <div
            style={{
              textAlign: "center",
              color: "#6c757d",
              marginTop: "40px",
              fontSize: "14px",
            }}
          >
            No execution in progress
          </div>
        ) : (
          <div
            style={{ display: "flex", flexDirection: "column", gap: "12px" }}
          >
            {statusHistory.map((status, index) => {
              const isExpanded = expandedNodes.has(status.node_id);
              const isExecuting = status.status === "executing";
              const isError = status.status === "error";
              const isCompleted = status.status === "completed";
              const isProgress = status.status === "progress";

              return (
                <div
                  key={`${status.node_id}-${index}`}
                  style={{
                    backgroundColor: "#ffffff",
                    border: `2px solid ${
                      isError
                        ? "#dc3545"
                        : isExecuting || isProgress
                          ? "#007bff"
                          : "#28a745"
                    }`,
                    borderRadius: "8px",
                    padding: "12px",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                  }}
                >
                  {/* Header */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      marginBottom: "8px",
                    }}
                  >
                    {/* Node Number Badge */}
                    <div
                      style={{
                        backgroundColor: isError
                          ? "#dc3545"
                          : isExecuting || isProgress
                            ? "#007bff"
                            : "#28a745",
                        color: "#ffffff",
                        borderRadius: "50%",
                        width: "28px",
                        height: "28px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "12px",
                        fontWeight: "600",
                        flexShrink: 0,
                      }}
                    >
                      {status.node_number}
                    </div>

                    {/* Node Name */}
                    <div
                      style={{
                        flex: 1,
                        fontSize: "14px",
                        fontWeight: "600",
                        color: "#212529",
                      }}
                    >
                      {status.node_name}
                    </div>

                    {/* Spinner for executing nodes */}
                    {isExecuting && (
                      <div
                        style={{
                          width: "20px",
                          height: "20px",
                          border: "3px solid #f3f3f3",
                          borderTop: "3px solid #007bff",
                          borderRadius: "50%",
                          animation: "spin 1s linear infinite",
                        }}
                      />
                    )}

                    {/* Progress indicator for progress nodes */}
                    {isProgress && (
                      <div
                        style={{
                          width: "20px",
                          height: "20px",
                          border: "3px solid #f3f3f3",
                          borderTop: "3px solid #007bff",
                          borderRadius: "50%",
                          animation: "spin 1s linear infinite",
                        }}
                      />
                    )}

                    {/* Status icon for completed/error */}
                    {isCompleted && (
                      <div
                        style={{
                          width: "20px",
                          height: "20px",
                          color: "#28a745",
                          fontSize: "20px",
                          lineHeight: "20px",
                        }}
                      >
                        ✓
                      </div>
                    )}
                    {isError && (
                      <div
                        style={{
                          width: "20px",
                          height: "20px",
                          color: "#dc3545",
                          fontSize: "20px",
                          lineHeight: "20px",
                        }}
                      >
                        ✗
                      </div>
                    )}
                  </div>

                  {/* Inputs Section */}
                  {status.inputs && Object.keys(status.inputs).length > 0 && (
                    <div style={{ marginBottom: "8px" }}>
                      <button
                        onClick={() => toggleExpanded(status.node_id)}
                        style={{
                          background: "none",
                          border: "none",
                          padding: "4px 0",
                          cursor: "pointer",
                          fontSize: "13px",
                          fontWeight: "600",
                          color: "#495057",
                          display: "flex",
                          alignItems: "center",
                          gap: "4px",
                        }}
                      >
                        <span>{isExpanded ? "▼" : "▶"}</span>
                        <span>Inputs</span>
                      </button>
                      {isExpanded && (
                        <div
                          style={{
                            marginTop: "4px",
                            padding: "8px",
                            backgroundColor: "#f8f9fa",
                            borderRadius: "4px",
                            fontSize: "12px",
                            fontFamily: "monospace",
                          }}
                        >
                          {Object.entries(status.inputs).map(([key, value]) => (
                            <div key={key} style={{ marginBottom: "8px" }}>
                              <span
                                style={{ color: "#6c757d", fontWeight: "600" }}
                              >
                                {key}:
                              </span>{" "}
                              <TreeView
                                data={value}
                                parentKey={`${status.node_id}-input-${key}`}
                              />
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Progress Bar Section */}
                  {isProgress && status.progress !== undefined && (
                    <div style={{ marginBottom: "8px" }}>
                      <div
                        style={{
                          fontSize: "12px",
                          color: "#495057",
                          marginBottom: "4px",
                          fontWeight: "500",
                        }}
                      >
                        {status.progress_message || "Processing..."}
                      </div>
                      <div
                        style={{
                          width: "100%",
                          height: "8px",
                          backgroundColor: "#e9ecef",
                          borderRadius: "4px",
                          overflow: "hidden",
                        }}
                      >
                        <div
                          style={{
                            width: `${status.progress * 100}%`,
                            height: "100%",
                            backgroundColor: "#007bff",
                            transition: "width 0.3s ease",
                          }}
                        />
                      </div>
                      <div
                        style={{
                          fontSize: "11px",
                          color: "#6c757d",
                          marginTop: "2px",
                          textAlign: "right",
                          fontWeight: "500",
                        }}
                      >
                        {Math.round(status.progress * 100)}%
                      </div>
                    </div>
                  )}

                  {/* Output Section */}
                  {isCompleted && status.output !== undefined && (
                    <div>
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          marginBottom: "4px",
                        }}
                      >
                        <div
                          style={{
                            fontSize: "13px",
                            fontWeight: "600",
                            color: "#495057",
                          }}
                        >
                          Output
                        </div>
                        {typeof status.output === "string" &&
                          !isBase64Image(status.output) && (
                            <button
                              onClick={() => toggleRenderMode(status.node_id)}
                              style={{
                                background: "none",
                                border: "1px solid #6c757d",
                                borderRadius: "4px",
                                padding: "2px 8px",
                                cursor: "pointer",
                                fontSize: "11px",
                                color: "#6c757d",
                                fontWeight: "500",
                              }}
                              title={
                                renderModes[status.node_id] === "markdown"
                                  ? "Switch to raw view"
                                  : "Switch to markdown view"
                              }
                            >
                              {renderModes[status.node_id] === "markdown"
                                ? "Raw"
                                : "MD"}
                            </button>
                          )}
                      </div>
                      <div
                        style={{
                          padding: "8px",
                          backgroundColor: "#e7f5e7",
                          borderRadius: "4px",
                          fontSize: "12px",
                          fontFamily: "monospace",
                          color: "#212529",
                          wordBreak: "break-word",
                          maxHeight: "300px",
                          overflowY: "auto",
                        }}
                      >
                        <TreeView
                          data={status.output}
                          parentKey={`${status.node_id}-output`}
                          renderMode={renderModes[status.node_id] || "raw"}
                        />
                      </div>
                    </div>
                  )}

                  {/* Error Section */}
                  {isError && status.error && (
                    <div>
                      <div
                        style={{
                          fontSize: "13px",
                          fontWeight: "600",
                          color: "#dc3545",
                          marginBottom: "4px",
                        }}
                      >
                        Error
                      </div>
                      <div
                        style={{
                          padding: "8px",
                          backgroundColor: "#f8d7da",
                          borderRadius: "4px",
                          fontSize: "12px",
                          fontFamily: "monospace",
                          color: "#721c24",
                          wordBreak: "break-word",
                        }}
                      >
                        {status.error}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* CSS Animation for spinner */}
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
};

export default StatusPanel;
