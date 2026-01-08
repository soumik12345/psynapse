import React, { memo, useState } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { NodeData } from "../types/schema";

// Helper to check if string is a base64 encoded image
const isBase64Image = (str: string): boolean => {
  if (!str.startsWith("data:image")) return false;
  const base64Pattern = /^data:image\/(png|jpeg|jpg|gif|webp|svg\+xml);base64,/;
  return base64Pattern.test(str);
};

// Simple Markdown renderer component
const SimpleMarkdown = ({ content }: { content: string }) => {
  const renderMarkdown = (text: string) => {
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];
    let inCodeBlock = false;
    let codeBlockContent: string[] = [];

    lines.forEach((line, index) => {
      // Code block handling
      if (line.startsWith('```')) {
        if (!inCodeBlock) {
          inCodeBlock = true;
          codeBlockContent = [];
        } else {
          inCodeBlock = false;
          elements.push(
            <pre
              key={`code-${index}`}
              style={{
                backgroundColor: '#1e1e1e',
                color: '#d4d4d4',
                padding: '12px',
                borderRadius: '6px',
                overflow: 'auto',
                fontSize: '12px',
                margin: '8px 0',
                fontFamily: 'monospace',
              }}
            >
              <code>{codeBlockContent.join('\n')}</code>
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
      if (line.startsWith('### ')) {
        elements.push(<h3 key={index} style={{ margin: '12px 0 8px', fontSize: '14px', fontWeight: 'bold' }}>{line.slice(4)}</h3>);
        return;
      }
      if (line.startsWith('## ')) {
        elements.push(<h2 key={index} style={{ margin: '14px 0 10px', fontSize: '16px', fontWeight: 'bold' }}>{line.slice(3)}</h2>);
        return;
      }
      if (line.startsWith('# ')) {
        elements.push(<h1 key={index} style={{ margin: '16px 0 12px', fontSize: '18px', fontWeight: 'bold' }}>{line.slice(2)}</h1>);
        return;
      }

      // Horizontal rule
      if (line.match(/^(-{3,}|\*{3,}|_{3,})$/)) {
        elements.push(<hr key={index} style={{ margin: '12px 0', border: 'none', borderTop: '1px solid #ddd' }} />);
        return;
      }

      // Empty line
      if (line.trim() === '') {
        elements.push(<div key={index} style={{ height: '8px' }} />);
        return;
      }

      // List items
      if (line.match(/^[\-\*]\s/)) {
        elements.push(
          <div key={index} style={{ paddingLeft: '16px', margin: '4px 0' }}>
            • {renderInlineMarkdown(line.slice(2))}
          </div>
        );
        return;
      }

      // Numbered list
      const numberedMatch = line.match(/^(\d+)\.\s/);
      if (numberedMatch) {
        elements.push(
          <div key={index} style={{ paddingLeft: '16px', margin: '4px 0' }}>
            {numberedMatch[1]}. {renderInlineMarkdown(line.slice(numberedMatch[0].length))}
          </div>
        );
        return;
      }

      // Regular paragraph
      elements.push(<p key={index} style={{ margin: '6px 0', lineHeight: '1.5' }}>{renderInlineMarkdown(line)}</p>);
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
              backgroundColor: '#f0f0f0',
              padding: '2px 6px',
              borderRadius: '3px',
              fontSize: '11px',
              fontFamily: 'monospace',
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

  return <div style={{ fontFamily: 'sans-serif', fontSize: '13px' }}>{renderMarkdown(content)}</div>;
};

// Recursive TreeView Component
interface TreeViewProps {
  data: any;
  level?: number;
  renderMode?: 'raw' | 'markdown';
}

const TreeView = ({ data, level = 0, renderMode = 'raw' }: TreeViewProps) => {
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
            Image ({data.split(',')[0].split('/')[1].split(';')[0]})
          </div>
        </div>
      );
    }

    // Render based on mode
    if (renderMode === 'markdown') {
      return <SimpleMarkdown content={data} />;
    }

    return <span style={{ color: "#22863a" }}>"{data}"</span>;
  }

  if (Array.isArray(data)) {
    if (data.length === 0) {
      return <span style={{ color: "#6a737d" }}>[]</span>;
    }

    const key = `array-${level}`;
    const isExpanded = expanded[key];

    return (
      <div style={{ marginLeft: `${indent}px` }}>
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
                <TreeView data={item} level={level + 1} />
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

    const key = `object-${level}`;
    const isExpanded = expanded[key];

    return (
      <div style={{ marginLeft: `${indent}px` }}>
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
                <TreeView data={data[k]} level={level + 1} />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return <span>{String(data)}</span>;
};

const ViewNode = ({ data }: NodeProps<NodeData>) => {
  const [renderMode, setRenderMode] = useState<'raw' | 'markdown'>('raw');
  
  const hasValue = data.value !== undefined && data.value !== null;
  const isPrimitiveOrEmpty =
    !hasValue ||
    typeof data.value === "string" ||
    typeof data.value === "number" ||
    typeof data.value === "boolean";

  // Check if the value is a string (for showing render mode toggle)
  const isStringValue = hasValue && typeof data.value === "string";
  // Check if it's an image string (auto-render as image, no toggle needed)
  const isImageString = isStringValue && isBase64Image(data.value as string);

  // Determine border color based on execution status
  const getBorderColor = () => {
    if (data.executionStatus === "executing") {
      return "#ffc107"; // Yellow for executing
    } else if (data.executionStatus === "completed") {
      return "#28a745"; // Green for completed
    } else if (data.executionStatus === "error") {
      return "#dc3545"; // Red for error
    }
    return "#50c878"; // Default green
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
        background: "#f0fdf4",
        minWidth: "200px",
        maxWidth: "400px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
        transition: "border-color 0.3s ease, border-width 0.3s ease",
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        id="input"
        style={{
          background: "#50c878",
          width: "10px",
          height: "10px",
        }}
      />
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
            color: "#166534",
            fontSize: "14px",
          }}
        >
          View
        </div>
        {/* Render mode toggle - only show for non-image strings */}
        {isStringValue && !isImageString && (
          <div
            style={{
              display: "flex",
              gap: "4px",
              fontSize: "10px",
            }}
          >
            <button
              onClick={() => setRenderMode('raw')}
              style={{
                padding: "2px 8px",
                border: "1px solid #50c878",
                borderRadius: "4px 0 0 4px",
                background: renderMode === 'raw' ? "#50c878" : "#ffffff",
                color: renderMode === 'raw' ? "#ffffff" : "#166534",
                cursor: "pointer",
                fontWeight: renderMode === 'raw' ? "bold" : "normal",
              }}
            >
              Raw
            </button>
            <button
              onClick={() => setRenderMode('markdown')}
              style={{
                padding: "2px 8px",
                border: "1px solid #50c878",
                borderLeft: "none",
                borderRadius: "0 4px 4px 0",
                background: renderMode === 'markdown' ? "#50c878" : "#ffffff",
                color: renderMode === 'markdown' ? "#ffffff" : "#166534",
                cursor: "pointer",
                fontWeight: renderMode === 'markdown' ? "bold" : "normal",
              }}
            >
              Markdown
            </button>
          </div>
        )}
      </div>
      <div
        style={{
          padding: "8px",
          background: "#ffffff",
          border: "1px solid #50c878",
          borderRadius: "4px",
          fontSize: "12px",
          color: "#333",
          fontFamily: renderMode === 'markdown' ? "sans-serif" : "monospace",
          minHeight: "24px",
          maxHeight: "300px",
          overflowY: "auto",
          wordBreak: isPrimitiveOrEmpty ? "break-all" : "normal",
        }}
      >
        {!hasValue ? (
          <span style={{ color: "#999", fontStyle: "italic" }}>No value</span>
        ) : (
          <TreeView data={data.value} renderMode={renderMode} />
        )}
      </div>
    </div>
  );
};

export default memo(ViewNode);
