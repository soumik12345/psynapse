import { useState, useEffect } from "react";

interface EnvironmentVariable {
  key: string;
  value: string;
}

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const STORAGE_KEY = "psynapse_env_vars";

const SettingsModal = ({ isOpen, onClose }: SettingsModalProps) => {
  const [selectedSection, setSelectedSection] = useState<string>("env-vars");
  const [envVars, setEnvVars] = useState<EnvironmentVariable[]>([]);

  // Load environment variables from sessionStorage on mount
  useEffect(() => {
    if (isOpen) {
      const stored = sessionStorage.getItem(STORAGE_KEY);
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          const vars = Object.entries(parsed).map(([key, value]) => ({
            key,
            value: String(value),
          }));
          setEnvVars(vars.length > 0 ? vars : [{ key: "", value: "" }]);
        } catch (e) {
          setEnvVars([{ key: "", value: "" }]);
        }
      } else {
        setEnvVars([{ key: "", value: "" }]);
      }
    }
  }, [isOpen]);

  // Save environment variables to sessionStorage whenever they change
  const saveToStorage = (vars: EnvironmentVariable[]) => {
    const filtered = vars.filter((v) => v.key.trim() !== "");
    const obj: Record<string, string> = {};
    filtered.forEach((v) => {
      obj[v.key] = v.value;
    });
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(obj));
  };

  const handleAddVariable = () => {
    const newVars = [...envVars, { key: "", value: "" }];
    setEnvVars(newVars);
  };

  const handleDeleteVariable = (index: number) => {
    const newVars = envVars.filter((_, i) => i !== index);
    setEnvVars(newVars);
    saveToStorage(newVars);
  };

  const handleKeyChange = (index: number, newKey: string) => {
    const newVars = [...envVars];
    newVars[index].key = newKey;
    setEnvVars(newVars);
    saveToStorage(newVars);
  };

  const handleValueChange = (index: number, newValue: string) => {
    const newVars = [...envVars];
    newVars[index].value = newValue;
    setEnvVars(newVars);
    saveToStorage(newVars);
  };

  if (!isOpen) return null;

  return (
    <div
      style={styles.overlay}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div style={styles.modal}>
        {/* Close Button */}
        <button onClick={onClose} style={styles.closeButton} title="Close">
          ✕
        </button>

        {/* Sidebar */}
        <div style={styles.sidebar}>
          <div style={styles.sidebarHeader}>
            <div style={styles.accountSection}>
              <div style={styles.avatar}>P</div>
              <div style={styles.accountInfo}>
                <div style={styles.accountName}>Psynapse</div>
                <div style={styles.accountRole}>Local Instance</div>
              </div>
            </div>
          </div>

          <div style={styles.sidebarSection}>
            <div style={styles.sidebarSectionTitle}>General</div>
            <button
              style={{
                ...styles.sidebarItem,
                ...(selectedSection === "env-vars"
                  ? styles.sidebarItemActive
                  : {}),
              }}
              onClick={() => setSelectedSection("env-vars")}
            >
              <span style={styles.sidebarItemIcon}>⚙</span>
              <span>Environment Variables</span>
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div style={styles.content}>
          {selectedSection === "env-vars" && (
            <>
              <h2 style={styles.contentTitle}>Environment Variables</h2>
              <p style={styles.contentDescription}>
                Manage environment variables that will be available during node
                graph execution. These variables are stored in your browser
                session.
              </p>

              <div style={styles.envVarsContainer}>
                <div style={styles.envVarsHeader}>
                  <div style={{ ...styles.envVarsHeaderCell, flex: 2 }}>
                    Variable Name
                  </div>
                  <div style={{ ...styles.envVarsHeaderCell, flex: 3 }}>
                    Value
                  </div>
                  <div style={{ ...styles.envVarsHeaderCell, width: "60px" }}>
                    Action
                  </div>
                </div>

                {envVars.map((envVar, index) => (
                  <div key={index} style={styles.envVarRow}>
                    <input
                      type="text"
                      value={envVar.key}
                      onChange={(e) => handleKeyChange(index, e.target.value)}
                      placeholder="VARIABLE_NAME"
                      style={{ ...styles.input, flex: 2 }}
                    />
                    <input
                      type="text"
                      value={envVar.value}
                      onChange={(e) => handleValueChange(index, e.target.value)}
                      placeholder="value"
                      style={{ ...styles.input, flex: 3 }}
                    />
                    <button
                      onClick={() => handleDeleteVariable(index)}
                      style={styles.deleteButton}
                      title="Delete variable"
                    >
                      🗑️
                    </button>
                  </div>
                ))}

                <button onClick={handleAddVariable} style={styles.addButton}>
                  + Add Variable
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  overlay: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 10000,
  },
  modal: {
    position: "relative",
    width: "900px",
    height: "600px",
    backgroundColor: "#ffffff",
    borderRadius: "12px",
    boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
    display: "flex",
    overflow: "hidden",
  },
  closeButton: {
    position: "absolute",
    top: "16px",
    right: "16px",
    width: "32px",
    height: "32px",
    border: "none",
    background: "transparent",
    fontSize: "24px",
    color: "#6c757d",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: "6px",
    transition: "background-color 0.2s",
    zIndex: 1,
  },
  sidebar: {
    width: "260px",
    backgroundColor: "#f8f9fa",
    borderRight: "1px solid #dee2e6",
    display: "flex",
    flexDirection: "column",
    padding: "20px 0",
  },
  sidebarHeader: {
    padding: "0 20px 20px 20px",
    borderBottom: "1px solid #dee2e6",
    marginBottom: "20px",
  },
  accountSection: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  avatar: {
    width: "40px",
    height: "40px",
    borderRadius: "50%",
    backgroundColor: "#007bff",
    color: "#ffffff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "18px",
    fontWeight: "600",
  },
  accountInfo: {
    flex: 1,
  },
  accountName: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#212529",
    marginBottom: "2px",
  },
  accountRole: {
    fontSize: "12px",
    color: "#6c757d",
  },
  sidebarSection: {
    padding: "0 12px",
  },
  sidebarSectionTitle: {
    fontSize: "12px",
    fontWeight: "600",
    color: "#6c757d",
    textTransform: "uppercase",
    padding: "8px 12px",
    letterSpacing: "0.5px",
  },
  sidebarItem: {
    width: "100%",
    padding: "10px 12px",
    border: "none",
    background: "transparent",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    fontSize: "14px",
    color: "#495057",
    cursor: "pointer",
    borderRadius: "6px",
    transition: "background-color 0.2s",
    textAlign: "left",
  },
  sidebarItemActive: {
    backgroundColor: "#e7f3ff",
    color: "#007bff",
    fontWeight: "500",
  },
  sidebarItemIcon: {
    fontSize: "16px",
  },
  content: {
    flex: 1,
    padding: "40px",
    overflowY: "auto",
  },
  contentTitle: {
    fontSize: "24px",
    fontWeight: "600",
    color: "#212529",
    marginBottom: "12px",
  },
  contentDescription: {
    fontSize: "14px",
    color: "#6c757d",
    marginBottom: "30px",
    lineHeight: "1.5",
  },
  envVarsContainer: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  envVarsHeader: {
    display: "flex",
    gap: "12px",
    padding: "12px",
    backgroundColor: "#f8f9fa",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: "600",
    color: "#495057",
  },
  envVarsHeaderCell: {
    display: "flex",
    alignItems: "center",
  },
  envVarRow: {
    display: "flex",
    gap: "12px",
    alignItems: "center",
  },
  input: {
    padding: "10px 12px",
    fontSize: "14px",
    border: "1px solid #dee2e6",
    borderRadius: "6px",
    outline: "none",
    transition: "border-color 0.2s",
  },
  deleteButton: {
    width: "60px",
    padding: "10px",
    border: "1px solid #dee2e6",
    borderRadius: "6px",
    backgroundColor: "#ffffff",
    cursor: "pointer",
    fontSize: "16px",
    transition: "all 0.2s",
  },
  addButton: {
    padding: "10px 20px",
    fontSize: "14px",
    fontWeight: "600",
    color: "#007bff",
    backgroundColor: "#ffffff",
    border: "2px dashed #007bff",
    borderRadius: "6px",
    cursor: "pointer",
    transition: "all 0.2s",
    marginTop: "12px",
  },
};

export default SettingsModal;
