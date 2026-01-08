import { useState, useEffect } from "react";
import type { Node } from "reactflow";
import type { ParamSchema } from "../types/schema";
import Editor from "react-simple-code-editor";

interface NodePanelProps {
  selectedNode: Node | null;
  onClose: () => void;
  onUpdate: (nodeId: string, updates: any) => void;
}

interface ListItem {
  type: "String" | "Number" | "Boolean" | "Object";
  value: any;
}

const NodePanel = ({ selectedNode, onUpdate }: NodePanelProps) => {
  // Variable node state
  const [name, setName] = useState("");
  const [type, setType] = useState<
    "String" | "Number" | "Boolean" | "Object" | "List" | "Image"
  >("String");
  const [value, setValue] = useState<string | number | boolean>("");
  const [error, setError] = useState<string | null>(null);
  const [textContentFormat, setTextContentFormat] = useState(false);
  const [imageContentFormat, setImageContentFormat] = useState(false);
  const [llmMessageFormat, setLlmMessageFormat] = useState(false);
  const [llmMessageRole, setLlmMessageRole] = useState<"system" | "user" | "assistant">("user");

  // List editor state
  const [listItems, setListItems] = useState<ListItem[]>([]);

  // Function node state
  const [paramValues, setParamValues] = useState<Record<string, any>>({});

  // Update local state when selected node changes
  useEffect(() => {
    if (!selectedNode) {
      // Reset all state when no node is selected
      setName("");
      setType("String");
      setValue("");
      setError(null);
      setTextContentFormat(false);
      setImageContentFormat(false);
      setLlmMessageFormat(false);
      setLlmMessageRole("user");
      setListItems([]);
      setParamValues({});
      return;
    }

    if (selectedNode.type === "variableNode") {
      // Reset function node state
      setParamValues({});
      // Update variable node state
      setName(selectedNode.data.variableName || "");
      const nodeType = selectedNode.data.variableType || "String";
      setType(nodeType);
      setError(null);
      setTextContentFormat(selectedNode.data.textContentFormat || false);
      setImageContentFormat(selectedNode.data.imageContentFormat || false);
      setLlmMessageFormat(selectedNode.data.llmMessageFormat || false);
      setLlmMessageRole(selectedNode.data.llmMessageRole || "user");

      // Parse list values if type is List
      if (
        nodeType === "List" &&
        Array.isArray(selectedNode.data.variableValue)
      ) {
        const parsedItems: ListItem[] = selectedNode.data.variableValue.map(
          (item: any) => {
            if (typeof item === "string") {
              return { type: "String", value: item };
            } else if (typeof item === "number") {
              return { type: "Number", value: item };
            } else if (typeof item === "boolean") {
              return { type: "Boolean", value: item };
            } else {
              return { type: "Object", value: JSON.stringify(item) };
            }
          },
        );
        setListItems(parsedItems);
        setValue("");
      } else if (
        nodeType === "Object" &&
        typeof selectedNode.data.variableValue === "object" &&
        selectedNode.data.variableValue !== null
      ) {
        setValue(JSON.stringify(selectedNode.data.variableValue));
        setListItems([]);
      } else {
        setValue(selectedNode.data.variableValue ?? "");
        setListItems([]);
      }
    } else if (selectedNode.type === "functionNode") {
      // Reset variable node state
      setName("");
      setType("String");
      setValue("");
      setError(null);
      setTextContentFormat(false);
      setImageContentFormat(false);
      setListItems([]);
      // Initialize param values from node data
      const params = selectedNode.data.params || [];
      const initialValues: Record<string, any> = {};
      params.forEach((param: ParamSchema) => {
        const value =
          selectedNode.data[param.name] ??
          (param.default !== undefined ? param.default : "");
        // Convert object/dict values to JSON string for editing
        if (
          (param.type === "object" || param.type === "dict") &&
          typeof value === "object" &&
          value !== null
        ) {
          initialValues[param.name] = JSON.stringify(value, null, 2);
        } else {
          initialValues[param.name] = value;
        }
      });
      setParamValues(initialValues);
    }
  }, [selectedNode?.id, selectedNode?.type, selectedNode?.data]);

  const handleTypeChange = (
    newType: "String" | "Number" | "Boolean" | "Object" | "List" | "Image",
  ) => {
    setType(newType);
    setError(null);

    // Reset textContentFormat when switching away from String type
    if (newType !== "String") {
      setTextContentFormat(false);
    }

    // Reset imageContentFormat when switching away from Image type
    if (newType !== "Image") {
      setImageContentFormat(false);
    }

    // Reset llmMessageFormat when switching away from String or Image type
    if (newType !== "String" && newType !== "Image") {
      setLlmMessageFormat(false);
      setLlmMessageRole("user");
    }

    // Reset value to default for new type
    if (newType === "String") {
      setValue("");
      setListItems([]);
    } else if (newType === "Number") {
      setValue(0);
      setListItems([]);
    } else if (newType === "Boolean") {
      setValue(false);
      setListItems([]);
    } else if (newType === "Object") {
      setValue("");
      setListItems([]);
    } else if (newType === "List") {
      setValue("");
      setListItems([]);
    } else if (newType === "Image") {
      setValue("");
      setListItems([]);
    }
  };

  const handleValueChange = (newValue: string | boolean) => {
    setError(null);

    if (type === "Number" && typeof newValue === "string") {
      // Validate number input
      if (newValue === "" || newValue === "-") {
        setValue(newValue);
        return;
      }

      const num = Number(newValue);
      if (isNaN(num)) {
        setError("Invalid number format");
        setValue(newValue);
      } else {
        setValue(num);
      }
    } else if (type === "Boolean") {
      setValue(newValue);
    } else {
      setValue(newValue);
    }
  };

  const handleSave = () => {
    if (!selectedNode) return;

    if (selectedNode.type === "variableNode") {
      // Validate number before saving
      if (
        type === "Number" &&
        typeof value === "string" &&
        (value === "" || value === "-")
      ) {
        setError("Please enter a valid number");
        return;
      }

      if (error) {
        return;
      }

      // Convert value to appropriate type
      let finalValue: string | number | boolean | any[] | object = value;

      if (type === "Number" && typeof value === "number") {
        finalValue = value;
      } else if (type === "Number" && typeof value === "string") {
        finalValue = Number(value);
      } else if (type === "List") {
        // Convert list items to Python-compatible array
        finalValue = listItems.map((item) => {
          if (item.type === "String") {
            return String(item.value);
          } else if (item.type === "Number") {
            return Number(item.value);
          } else if (item.type === "Boolean") {
            return Boolean(item.value);
          } else if (item.type === "Object") {
            try {
              return JSON.parse(item.value);
            } catch {
              setError("Invalid JSON in Object value");
              return null;
            }
          }
          return item.value;
        });

        // Check for null values (invalid JSON)
        if (Array.isArray(finalValue) && finalValue.includes(null)) {
          return;
        }
      } else if (type === "Object") {
        // Validate and parse JSON
        try {
          if (typeof value === "string" && value.trim() !== "") {
            finalValue = JSON.parse(value as string);
          } else {
            finalValue = {};
          }
        } catch {
          setError("Invalid JSON format");
          return;
        }
      }

      onUpdate(selectedNode.id, {
        variableName: name,
        variableType: type,
        variableValue: finalValue,
        textContentFormat: type === "String" ? textContentFormat : undefined,
        imageContentFormat: type === "Image" ? imageContentFormat : undefined,
        llmMessageFormat: (type === "String" || type === "Image") ? llmMessageFormat : undefined,
        llmMessageRole: (type === "String" || type === "Image") && llmMessageFormat ? llmMessageRole : undefined,
      });
    } else if (selectedNode.type === "functionNode") {
      // For function nodes, update all parameter values
      // Parse JSON strings for object/dict parameters
      const params = selectedNode.data.params || [];
      const processedValues: Record<string, any> = {};

      for (const param of params) {
        const value = paramValues[param.name];
        if (
          (param.type === "object" || param.type === "dict") &&
          typeof value === "string"
        ) {
          try {
            if (value.trim() !== "") {
              processedValues[param.name] = JSON.parse(value);
            } else {
              processedValues[param.name] = {};
            }
          } catch (e) {
            setError(`Invalid JSON format for parameter ${param.name}`);
            return;
          }
        } else {
          processedValues[param.name] = value;
        }
      }

      if (error) {
        return;
      }

      onUpdate(selectedNode.id, processedValues);
    }
  };

  const handleParamChange = (paramName: string, value: any) => {
    setParamValues((prev) => ({
      ...prev,
      [paramName]: value,
    }));
  };

  // List editor functions
  const addListItem = () => {
    setListItems([...listItems, { type: "String", value: "" }]);
  };

  const removeListItem = (index: number) => {
    setListItems(listItems.filter((_, i) => i !== index));
  };

  const updateListItemType = (
    index: number,
    newType: "String" | "Number" | "Boolean" | "Object",
  ) => {
    const newItems = [...listItems];
    newItems[index] = {
      type: newType,
      value: newType === "Number" ? 0 : newType === "Boolean" ? false : "",
    };
    setListItems(newItems);
  };

  const updateListItemValue = (index: number, newValue: any) => {
    const newItems = [...listItems];
    newItems[index] = { ...newItems[index], value: newValue };
    setListItems(newItems);
  };

  if (
    !selectedNode ||
    (selectedNode.type !== "variableNode" &&
      selectedNode.type !== "functionNode")
  ) {
    return null;
  }

  // Handle image file upload
  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith("image/")) {
      setError("Please select a valid image file");
      return;
    }

    // Read file and convert to base64
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      setValue(result); // Store the data URL (data:image/...;base64,...)
      setError(null);
    };
    reader.onerror = () => {
      setError("Failed to read image file");
    };
    reader.readAsDataURL(file);
  };

  // Render Variable Node Panel
  if (selectedNode.type === "variableNode") {
    const types: Array<
      "String" | "Number" | "Boolean" | "Object" | "List" | "Image"
    > = ["String", "Number", "Boolean", "Object", "List", "Image"];

    return (
      <div
        style={{
          width: "350px",
          backgroundColor: "#ffffff",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          borderRadius: "8px",
          boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
          border: "1px solid #dee2e6",
        }}
      >
        {/* Type Tabs */}
        <div
          style={{
            display: "flex",
            borderBottom: "1px solid #dee2e6",
            backgroundColor: "#f8f9fa",
          }}
        >
          {types.map((typeOption) => (
            <button
              key={typeOption}
              onClick={() => handleTypeChange(typeOption)}
              style={{
                flex: 1,
                padding: "12px 8px",
                background: "none",
                border: "none",
                borderBottom:
                  type === typeOption
                    ? "2px solid #9333ea"
                    : "2px solid transparent",
                color: type === typeOption ? "#9333ea" : "#6c757d",
                fontSize: "13px",
                fontWeight: type === typeOption ? "600" : "400",
                cursor: "pointer",
                transition: "all 0.2s",
              }}
              onMouseEnter={(e) => {
                if (type !== typeOption) {
                  e.currentTarget.style.color = "#495057";
                }
              }}
              onMouseLeave={(e) => {
                if (type !== typeOption) {
                  e.currentTarget.style.color = "#6c757d";
                }
              }}
            >
              {typeOption}
            </button>
          ))}
        </div>

        {/* Form Content */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "20px",
            backgroundColor: "#ffffff",
          }}
        >
          {/* Variable Name */}
          <div style={{ marginBottom: "20px" }}>
            <label
              htmlFor="varName"
              style={{
                display: "block",
                fontSize: "13px",
                fontWeight: "600",
                color: "#495057",
                marginBottom: "8px",
              }}
            >
              Name
            </label>
            <input
              id="varName"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter the variable name"
              style={{
                width: "100%",
                padding: "10px 12px",
                border: "1px solid #ced4da",
                borderRadius: "6px",
                fontSize: "14px",
                boxSizing: "border-box",
                outline: "none",
                transition: "border-color 0.2s",
                backgroundColor: "#ffffff",
                color: "#495057",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "#80bdff";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "#ced4da";
              }}
            />
          </div>

          {/* Default Value */}
          <div style={{ marginBottom: "20px" }}>
            {type !== "List" && type !== "Image" && (
              <label
                htmlFor="varValue"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  fontSize: "13px",
                  fontWeight: "600",
                  color: "#495057",
                  marginBottom: "8px",
                }}
              >
                <span>Default value</span>
                <span
                  style={{
                    fontSize: "12px",
                    fontWeight: "400",
                    color: "#6c757d",
                  }}
                >
                  Optional
                </span>
              </label>
            )}

            {type === "String" && (
              <>
                <input
                  id="varValue"
                  type="text"
                  value={value as string}
                  onChange={(e) => handleValueChange(e.target.value)}
                  placeholder="New variable"
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    border: `1px solid ${error ? "#dc3545" : "#ced4da"}`,
                    borderRadius: "6px",
                    fontSize: "14px",
                    boxSizing: "border-box",
                    outline: "none",
                    transition: "border-color 0.2s",
                    backgroundColor: "#ffffff",
                    color: "#495057",
                  }}
                  onFocus={(e) => {
                    if (!error) e.currentTarget.style.borderColor = "#80bdff";
                  }}
                  onBlur={(e) => {
                    if (!error) e.currentTarget.style.borderColor = "#ced4da";
                  }}
                />
                {/* LLM Message Switch */}
                <div style={{ marginTop: "16px" }}>
                  <label
                    style={{
                      display: "block",
                      fontSize: "13px",
                      fontWeight: "600",
                      color: "#495057",
                      marginBottom: "8px",
                    }}
                  >
                    LLM Message
                  </label>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "12px",
                    }}
                  >
                    <label
                      style={{
                        position: "relative",
                        display: "inline-block",
                        width: "48px",
                        height: "24px",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={llmMessageFormat}
                        onChange={(e) => setLlmMessageFormat(e.target.checked)}
                        style={{
                          opacity: 0,
                          width: 0,
                          height: 0,
                        }}
                      />
                      <span
                        style={{
                          position: "absolute",
                          cursor: "pointer",
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundColor: llmMessageFormat ? "#9333ea" : "#ccc",
                          transition: "0.3s",
                          borderRadius: "24px",
                        }}
                      >
                        <span
                          style={{
                            position: "absolute",
                            content: "",
                            height: "18px",
                            width: "18px",
                            left: llmMessageFormat ? "27px" : "3px",
                            bottom: "3px",
                            backgroundColor: "white",
                            transition: "0.3s",
                            borderRadius: "50%",
                          }}
                        />
                      </span>
                    </label>
                    <span
                      style={{
                        fontSize: "13px",
                        color: "#6c757d",
                      }}
                    >
                      {llmMessageFormat ? "Enabled" : "Disabled"}
                    </span>
                  </div>
                  {/* Role Dropdown - shown when LLM Message is enabled */}
                  {llmMessageFormat && (
                    <div style={{ marginTop: "12px" }}>
                      <label
                        style={{
                          display: "block",
                          fontSize: "12px",
                          fontWeight: "500",
                          color: "#495057",
                          marginBottom: "6px",
                        }}
                      >
                        Role
                      </label>
                      <select
                        value={llmMessageRole}
                        onChange={(e) => setLlmMessageRole(e.target.value as "system" | "user" | "assistant")}
                        style={{
                          width: "100%",
                          padding: "8px 12px",
                          border: "1px solid #ced4da",
                          borderRadius: "6px",
                          fontSize: "14px",
                          boxSizing: "border-box",
                          outline: "none",
                          backgroundColor: "#ffffff",
                          color: "#495057",
                          cursor: "pointer",
                        }}
                      >
                        <option value="system">system</option>
                        <option value="user">user</option>
                        <option value="assistant">assistant</option>
                      </select>
                    </div>
                  )}
                  <div
                    style={{
                      marginTop: "8px",
                      fontSize: "12px",
                      color: "#6c757d",
                      fontStyle: "italic",
                      lineHeight: "1.4",
                    }}
                  >
                    When enabled, outputs {`{role: "...", content: "..."}`} for LLM compatibility
                  </div>
                </div>
              </>
            )}

            {type === "Object" && (
              <div
                style={{
                  width: "100%",
                  border: `1px solid ${error ? "#dc3545" : "#ced4da"}`,
                  borderRadius: "6px",
                  overflow: "hidden",
                  backgroundColor: "#ffffff",
                  minHeight: "150px",
                  maxHeight: "300px",
                }}
              >
                <Editor
                  value={typeof value === "string" ? value : ""}
                  onValueChange={(code) => handleValueChange(code)}
                  placeholder='{"key": "value"}'
                  highlight={(code) => code}
                  padding={10}
                  style={{
                    fontFamily: '"Fira code", "Fira Mono", monospace',
                    fontSize: 14,
                    minHeight: "150px",
                    maxHeight: "300px",
                    overflow: "auto",
                    color: "#495057",
                    backgroundColor: "#ffffff",
                  }}
                  textareaClassName="json-editor-textarea"
                  preClassName="json-editor-pre"
                />
                <style>{`
                  .json-editor-textarea {
                    outline: none;
                    border: none;
                    resize: none;
                    font-family: "Fira code", "Fira Mono", monospace;
                    font-size: 14px;
                    color: #495057;
                    background-color: #ffffff;
                  }
                  .json-editor-pre {
                    margin: 0;
                    padding: 0;
                    font-family: "Fira code", "Fira Mono", monospace;
                    font-size: 14px;
                    color: #495057;
                    background-color: #ffffff;
                  }
                `}</style>
              </div>
            )}

            {type === "Number" && (
              <input
                id="varValue"
                type="number"
                value={
                  typeof value === "number"
                    ? value
                    : typeof value === "string"
                      ? value
                      : ""
                }
                onChange={(e) => handleValueChange(e.target.value)}
                placeholder="New variable"
                step="any"
                style={{
                  width: "100%",
                  padding: "10px 12px",
                  border: `1px solid ${error ? "#dc3545" : "#ced4da"}`,
                  borderRadius: "6px",
                  fontSize: "14px",
                  boxSizing: "border-box",
                  outline: "none",
                  transition: "border-color 0.2s",
                  backgroundColor: "#ffffff",
                  color: "#495057",
                }}
                onFocus={(e) => {
                  if (!error) e.currentTarget.style.borderColor = "#80bdff";
                }}
                onBlur={(e) => {
                  if (!error) e.currentTarget.style.borderColor = "#ced4da";
                }}
              />
            )}

            {type === "Boolean" && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <input
                  id="varValue"
                  type="checkbox"
                  checked={value as boolean}
                  onChange={(e) => handleValueChange(e.target.checked)}
                  style={{
                    width: "18px",
                    height: "18px",
                    cursor: "pointer",
                    accentColor: "#9333ea",
                  }}
                />
                <label
                  htmlFor="varValue"
                  style={{
                    fontSize: "14px",
                    color: "#495057",
                    cursor: "pointer",
                    userSelect: "none",
                  }}
                >
                  {value ? "True" : "False"}
                </label>
              </div>
            )}

            {type === "Image" && (
              <div>
                <label
                  htmlFor="imageUpload"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    fontSize: "13px",
                    fontWeight: "600",
                    color: "#495057",
                    marginBottom: "8px",
                  }}
                >
                  <span>Upload Image</span>
                  <span
                    style={{
                      fontSize: "12px",
                      fontWeight: "400",
                      color: "#6c757d",
                    }}
                  >
                    Optional
                  </span>
                </label>
                <input
                  id="imageUpload"
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    border: `1px solid ${error ? "#dc3545" : "#ced4da"}`,
                    borderRadius: "6px",
                    fontSize: "14px",
                    boxSizing: "border-box",
                    outline: "none",
                    transition: "border-color 0.2s",
                    backgroundColor: "#ffffff",
                    color: "#495057",
                    cursor: "pointer",
                  }}
                />
                {value && typeof value === "string" && value.startsWith("data:image") && (
                  <div
                    style={{
                      marginTop: "12px",
                      padding: "8px",
                      border: "1px solid #ced4da",
                      borderRadius: "6px",
                      backgroundColor: "#f8f9fa",
                      textAlign: "center",
                    }}
                  >
                    <img
                      src={value}
                      alt="Preview"
                      style={{
                        maxWidth: "100%",
                        maxHeight: "200px",
                        borderRadius: "4px",
                      }}
                    />
                    <div
                      style={{
                        marginTop: "8px",
                        fontSize: "11px",
                        color: "#6c757d",
                      }}
                    >
                      Image uploaded
                    </div>
                  </div>
                )}
                {/* LLM Message Switch for Image */}
                <div style={{ marginTop: "16px" }}>
                  <label
                    style={{
                      display: "block",
                      fontSize: "13px",
                      fontWeight: "600",
                      color: "#495057",
                      marginBottom: "8px",
                    }}
                  >
                    LLM Message
                  </label>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "12px",
                    }}
                  >
                    <label
                      style={{
                        position: "relative",
                        display: "inline-block",
                        width: "48px",
                        height: "24px",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={llmMessageFormat}
                        onChange={(e) => setLlmMessageFormat(e.target.checked)}
                        style={{
                          opacity: 0,
                          width: 0,
                          height: 0,
                        }}
                      />
                      <span
                        style={{
                          position: "absolute",
                          cursor: "pointer",
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundColor: llmMessageFormat ? "#9333ea" : "#ccc",
                          transition: "0.3s",
                          borderRadius: "24px",
                        }}
                      >
                        <span
                          style={{
                            position: "absolute",
                            content: "",
                            height: "18px",
                            width: "18px",
                            left: llmMessageFormat ? "27px" : "3px",
                            bottom: "3px",
                            backgroundColor: "white",
                            transition: "0.3s",
                            borderRadius: "50%",
                          }}
                        />
                      </span>
                    </label>
                    <span
                      style={{
                        fontSize: "13px",
                        color: "#6c757d",
                      }}
                    >
                      {llmMessageFormat ? "Enabled" : "Disabled"}
                    </span>
                  </div>
                  {/* Role Dropdown - shown when LLM Message is enabled */}
                  {llmMessageFormat && (
                    <div style={{ marginTop: "12px" }}>
                      <label
                        style={{
                          display: "block",
                          fontSize: "12px",
                          fontWeight: "500",
                          color: "#495057",
                          marginBottom: "6px",
                        }}
                      >
                        Role
                      </label>
                      <select
                        value={llmMessageRole}
                        onChange={(e) => setLlmMessageRole(e.target.value as "system" | "user" | "assistant")}
                        style={{
                          width: "100%",
                          padding: "8px 12px",
                          border: "1px solid #ced4da",
                          borderRadius: "6px",
                          fontSize: "14px",
                          boxSizing: "border-box",
                          outline: "none",
                          backgroundColor: "#ffffff",
                          color: "#495057",
                          cursor: "pointer",
                        }}
                      >
                        <option value="system">system</option>
                        <option value="user">user</option>
                        <option value="assistant">assistant</option>
                      </select>
                    </div>
                  )}
                  <div
                    style={{
                      marginTop: "8px",
                      fontSize: "12px",
                      color: "#6c757d",
                      fontStyle: "italic",
                      lineHeight: "1.4",
                    }}
                  >
                    {llmMessageFormat 
                      ? `Outputs {role: "...", content: [{type: "image_url", ...}]}` 
                      : `Outputs raw image data URL`}
                  </div>
                </div>
              </div>
            )}

            {type === "List" && (
              <div>
                <label
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    fontSize: "13px",
                    fontWeight: "600",
                    color: "#495057",
                    marginBottom: "8px",
                  }}
                >
                  <span>List Items</span>
                  <span
                    style={{
                      fontSize: "12px",
                      fontWeight: "400",
                      color: "#6c757d",
                    }}
                  >
                    Optional
                  </span>
                </label>
                {/* List Editor Table */}
                <div
                  style={{
                    border: "1px solid #ced4da",
                    borderRadius: "6px",
                    overflow: "hidden",
                  }}
                >
                  {listItems.length > 0 && (
                    <table
                      style={{
                        width: "100%",
                        borderCollapse: "collapse",
                      }}
                    >
                      <thead>
                        <tr style={{ backgroundColor: "#f8f9fa" }}>
                          <th
                            style={{
                              padding: "8px",
                              textAlign: "center",
                              fontSize: "12px",
                              fontWeight: "600",
                              color: "#495057",
                              width: "40px",
                            }}
                          ></th>
                          <th
                            style={{
                              padding: "8px",
                              textAlign: "left",
                              fontSize: "12px",
                              fontWeight: "600",
                              color: "#495057",
                              borderLeft: "1px solid #dee2e6",
                              width: "90px",
                            }}
                          >
                            Type
                          </th>
                          <th
                            style={{
                              padding: "8px",
                              textAlign: "left",
                              fontSize: "12px",
                              fontWeight: "600",
                              color: "#495057",
                              borderLeft: "1px solid #dee2e6",
                            }}
                          >
                            Value
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {listItems.map((item, index) => (
                          <tr
                            key={index}
                            style={{
                              borderTop: "1px solid #dee2e6",
                            }}
                          >
                            <td
                              style={{
                                padding: "8px",
                                textAlign: "center",
                              }}
                            >
                              <button
                                onClick={() => removeListItem(index)}
                                title="Delete item"
                                style={{
                                  padding: "4px 8px",
                                  backgroundColor: "transparent",
                                  color: "#495057",
                                  border: "1px solid #dee2e6",
                                  borderRadius: "3px",
                                  fontSize: "14px",
                                  cursor: "pointer",
                                  fontWeight: "400",
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  transition: "all 0.2s",
                                }}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.backgroundColor =
                                    "#f8f9fa";
                                  e.currentTarget.style.borderColor = "#adb5bd";
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.backgroundColor =
                                    "transparent";
                                  e.currentTarget.style.borderColor = "#dee2e6";
                                }}
                              >
                                🗑️
                              </button>
                            </td>
                            <td
                              style={{
                                padding: "8px",
                                borderLeft: "1px solid #dee2e6",
                              }}
                            >
                              <select
                                value={item.type}
                                onChange={(e) =>
                                  updateListItemType(
                                    index,
                                    e.target.value as
                                      | "String"
                                      | "Number"
                                      | "Boolean"
                                      | "Object",
                                  )
                                }
                                style={{
                                  width: "100%",
                                  padding: "4px 8px",
                                  border: "1px solid #ced4da",
                                  borderRadius: "4px",
                                  fontSize: "13px",
                                  backgroundColor: "#ffffff",
                                }}
                              >
                                <option value="String">String</option>
                                <option value="Number">Number</option>
                                <option value="Boolean">Boolean</option>
                                <option value="Object">Object</option>
                              </select>
                            </td>
                            <td
                              style={{
                                padding: "8px",
                                borderLeft: "1px solid #dee2e6",
                              }}
                            >
                              {item.type === "String" && (
                                <input
                                  type="text"
                                  value={item.value}
                                  onChange={(e) =>
                                    updateListItemValue(index, e.target.value)
                                  }
                                  style={{
                                    width: "100%",
                                    padding: "4px 8px",
                                    border: "1px solid #ced4da",
                                    borderRadius: "4px",
                                    fontSize: "13px",
                                  }}
                                />
                              )}
                              {item.type === "Number" && (
                                <input
                                  type="number"
                                  value={item.value}
                                  onChange={(e) =>
                                    updateListItemValue(index, e.target.value)
                                  }
                                  step="any"
                                  style={{
                                    width: "100%",
                                    padding: "4px 8px",
                                    border: "1px solid #ced4da",
                                    borderRadius: "4px",
                                    fontSize: "13px",
                                  }}
                                />
                              )}
                              {item.type === "Boolean" && (
                                <input
                                  type="checkbox"
                                  checked={item.value}
                                  onChange={(e) =>
                                    updateListItemValue(index, e.target.checked)
                                  }
                                  style={{
                                    width: "18px",
                                    height: "18px",
                                    cursor: "pointer",
                                    accentColor: "#9333ea",
                                  }}
                                />
                              )}
                              {item.type === "Object" && (
                                <input
                                  type="text"
                                  value={item.value}
                                  onChange={(e) =>
                                    updateListItemValue(index, e.target.value)
                                  }
                                  placeholder='{"key": "value"}'
                                  style={{
                                    width: "100%",
                                    padding: "4px 8px",
                                    border: "1px solid #ced4da",
                                    borderRadius: "4px",
                                    fontSize: "13px",
                                  }}
                                />
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                  {/* Add Item Button */}
                  <div
                    style={{
                      padding: "8px",
                      borderTop:
                        listItems.length > 0 ? "1px solid #dee2e6" : "none",
                      textAlign: "center",
                      backgroundColor: "#f8f9fa",
                    }}
                  >
                    <button
                      onClick={addListItem}
                      style={{
                        padding: "6px 16px",
                        backgroundColor: "#9333ea",
                        color: "#ffffff",
                        border: "none",
                        borderRadius: "4px",
                        fontSize: "13px",
                        cursor: "pointer",
                        fontWeight: "600",
                        transition: "background-color 0.2s",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = "#7c3aed";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = "#9333ea";
                      }}
                    >
                      + Add Item
                    </button>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div
                style={{
                  marginTop: "4px",
                  fontSize: "12px",
                  color: "#dc3545",
                }}
              >
                {error}
              </div>
            )}
          </div>

          {/* Save Button */}
          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button
              onClick={handleSave}
              disabled={!!error}
              style={{
                padding: "8px 20px",
                backgroundColor: error ? "#6c757d" : "#9333ea",
                color: "#ffffff",
                border: "none",
                borderRadius: "6px",
                fontSize: "14px",
                fontWeight: "600",
                cursor: error ? "not-allowed" : "pointer",
                transition: "background-color 0.2s",
                opacity: error ? 0.6 : 1,
              }}
              onMouseEnter={(e) => {
                if (!error) e.currentTarget.style.backgroundColor = "#7c3aed";
              }}
              onMouseLeave={(e) => {
                if (!error) e.currentTarget.style.backgroundColor = "#9333ea";
              }}
            >
              Save
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Render Function Node Panel
  if (selectedNode.type === "functionNode") {
    const functionName =
      selectedNode.data.functionName || selectedNode.data.label;
    const docstring =
      selectedNode.data.docstring || "No documentation available.";
    const params: ParamSchema[] = selectedNode.data.params || [];

    return (
      <div
        style={{
          width: "400px",
          backgroundColor: "#ffffff",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          borderRadius: "8px",
          boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
          border: "1px solid #dee2e6",
          maxHeight: "80vh",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid #dee2e6",
            backgroundColor: "#f8f9fa",
          }}
        >
          <h3
            style={{
              margin: "0 0 8px 0",
              fontSize: "16px",
              fontWeight: "600",
              color: "#495057",
            }}
          >
            {functionName}
          </h3>
          <div
            style={{
              fontSize: "12px",
              color: "#6c757d",
              fontStyle: "italic",
            }}
          >
            Function Properties
          </div>
        </div>

        {/* Docstring Section */}
        <div
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid #dee2e6",
            backgroundColor: "#f8f9fa",
          }}
        >
          <label
            style={{
              display: "block",
              fontSize: "13px",
              fontWeight: "600",
              color: "#495057",
              marginBottom: "8px",
            }}
          >
            Documentation
          </label>
          <div
            style={{
              fontSize: "13px",
              color: "#6c757d",
              lineHeight: "1.5",
              whiteSpace: "pre-wrap",
              fontFamily: "monospace",
              backgroundColor: "#ffffff",
              padding: "10px 12px",
              borderRadius: "6px",
              border: "1px solid #dee2e6",
              maxHeight: "150px",
              overflowY: "auto",
            }}
          >
            {docstring}
          </div>
        </div>

        {/* Parameters Section */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "20px",
            backgroundColor: "#ffffff",
          }}
        >
          <label
            style={{
              display: "block",
              fontSize: "13px",
              fontWeight: "600",
              color: "#495057",
              marginBottom: "16px",
            }}
          >
            Parameters
          </label>

          {params.length === 0 ? (
            <div
              style={{
                fontSize: "13px",
                color: "#6c757d",
                fontStyle: "italic",
                textAlign: "center",
                padding: "20px",
              }}
            >
              No parameters
            </div>
          ) : (
            params.map((param: ParamSchema) => (
              <div key={param.name} style={{ marginBottom: "20px" }}>
                <label
                  htmlFor={`param-${param.name}`}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    fontSize: "13px",
                    fontWeight: "600",
                    color: "#495057",
                    marginBottom: "8px",
                  }}
                >
                  <span>{param.name}</span>
                  <span
                    style={{
                      fontSize: "11px",
                      fontWeight: "400",
                      color: "#6c757d",
                      backgroundColor: "#e9ecef",
                      padding: "2px 6px",
                      borderRadius: "3px",
                    }}
                  >
                    {param.type}
                  </span>
                  {param.default !== undefined && (
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: "400",
                        color: "#28a745",
                        backgroundColor: "#d4edda",
                        padding: "2px 6px",
                        borderRadius: "3px",
                      }}
                    >
                      default: {String(param.default)}
                    </span>
                  )}
                </label>

                {/* Input field based on type */}
                {param.literal_values && param.literal_values.length > 0 ? (
                  <select
                    id={`param-${param.name}`}
                    value={paramValues[param.name] ?? param.literal_values[0]}
                    onChange={(e) =>
                      handleParamChange(param.name, e.target.value)
                    }
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      border: "1px solid #ced4da",
                      borderRadius: "6px",
                      fontSize: "14px",
                      boxSizing: "border-box",
                      outline: "none",
                      transition: "border-color 0.2s",
                      backgroundColor: "#ffffff",
                      color: "#495057",
                      cursor: "pointer",
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = "#80bdff";
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = "#ced4da";
                    }}
                  >
                    {param.literal_values.map((value) => (
                      <option key={value} value={value}>
                        {value}
                      </option>
                    ))}
                  </select>
                ) : param.type === "bool" ? (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                    }}
                  >
                    <input
                      id={`param-${param.name}`}
                      type="checkbox"
                      checked={
                        paramValues[param.name] === true ||
                        paramValues[param.name] === "true"
                      }
                      onChange={(e) =>
                        handleParamChange(param.name, e.target.checked)
                      }
                      style={{
                        width: "18px",
                        height: "18px",
                        cursor: "pointer",
                        accentColor: "#4a90e2",
                      }}
                    />
                    <label
                      htmlFor={`param-${param.name}`}
                      style={{
                        fontSize: "14px",
                        color: "#495057",
                        cursor: "pointer",
                        userSelect: "none",
                      }}
                    >
                      {paramValues[param.name] === true ||
                      paramValues[param.name] === "true"
                        ? "True"
                        : "False"}
                    </label>
                  </div>
                ) : param.type === "int" || param.type === "float" ? (
                  <input
                    id={`param-${param.name}`}
                    type="number"
                    value={paramValues[param.name] ?? ""}
                    onChange={(e) =>
                      handleParamChange(param.name, e.target.value)
                    }
                    placeholder={
                      param.default !== undefined
                        ? `Default: ${param.default}`
                        : `Enter ${param.type}`
                    }
                    step={param.type === "float" ? "any" : "1"}
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      border: "1px solid #ced4da",
                      borderRadius: "6px",
                      fontSize: "14px",
                      boxSizing: "border-box",
                      outline: "none",
                      transition: "border-color 0.2s",
                      backgroundColor: "#ffffff",
                      color: "#495057",
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = "#80bdff";
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = "#ced4da";
                    }}
                  />
                ) : param.type === "object" || param.type === "dict" ? (
                  <div
                    style={{
                      width: "100%",
                      border: `1px solid ${error ? "#dc3545" : "#ced4da"}`,
                      borderRadius: "6px",
                      overflow: "hidden",
                      backgroundColor: "#ffffff",
                      minHeight: "150px",
                      maxHeight: "300px",
                    }}
                  >
                    <Editor
                      value={
                        typeof paramValues[param.name] === "string"
                          ? paramValues[param.name]
                          : typeof paramValues[param.name] === "object" &&
                              paramValues[param.name] !== null
                            ? JSON.stringify(paramValues[param.name], null, 2)
                            : ""
                      }
                      onValueChange={(code) =>
                        handleParamChange(param.name, code)
                      }
                      placeholder='{"key": "value"}'
                      highlight={(code) => code}
                      padding={10}
                      style={{
                        fontFamily: '"Fira code", "Fira Mono", monospace',
                        fontSize: 14,
                        minHeight: "150px",
                        maxHeight: "300px",
                        overflow: "auto",
                        color: "#495057",
                        backgroundColor: "#ffffff",
                      }}
                      textareaClassName="json-editor-textarea"
                      preClassName="json-editor-pre"
                    />
                  </div>
                ) : (
                  <input
                    id={`param-${param.name}`}
                    type="text"
                    value={paramValues[param.name] ?? ""}
                    onChange={(e) =>
                      handleParamChange(param.name, e.target.value)
                    }
                    placeholder={
                      param.default !== undefined
                        ? `Default: ${param.default}`
                        : `Enter ${param.type}`
                    }
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      border: "1px solid #ced4da",
                      borderRadius: "6px",
                      fontSize: "14px",
                      boxSizing: "border-box",
                      outline: "none",
                      transition: "border-color 0.2s",
                      backgroundColor: "#ffffff",
                      color: "#495057",
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = "#80bdff";
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = "#ced4da";
                    }}
                  />
                )}
              </div>
            ))
          )}

          {/* Save Button */}
          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              marginTop: "20px",
            }}
          >
            <button
              onClick={handleSave}
              style={{
                padding: "8px 20px",
                backgroundColor: "#4a90e2",
                color: "#ffffff",
                border: "none",
                borderRadius: "6px",
                fontSize: "14px",
                fontWeight: "600",
                cursor: "pointer",
                transition: "background-color 0.2s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "#357abd";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "#4a90e2";
              }}
            >
              Save
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default NodePanel;
