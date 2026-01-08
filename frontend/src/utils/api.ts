import axios from "axios";
import type {
  FunctionSchema,
  ExecuteRequest,
  ExecuteResponse,
  ExecutionStatus,
} from "../types/schema";

const API_BASE_URL = "http://localhost:8000";
const ENV_VARS_STORAGE_KEY = "psynapse_env_vars";

// Helper function to get environment variables from sessionStorage
const getEnvVars = (): Record<string, string> | undefined => {
  try {
    const stored = sessionStorage.getItem(ENV_VARS_STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      return Object.keys(parsed).length > 0 ? parsed : undefined;
    }
  } catch (e) {
    console.error("Error reading environment variables:", e);
  }
  return undefined;
};

export const api = {
  async getSchemas(): Promise<FunctionSchema[]> {
    const response = await axios.get<FunctionSchema[]>(
      `${API_BASE_URL}/get_schema`,
    );
    return response.data;
  },

  async executeGraph(request: ExecuteRequest): Promise<ExecuteResponse> {
    const env_vars = getEnvVars();
    const requestWithEnv = { ...request, env_vars };
    const response = await axios.post<ExecuteResponse>(
      `${API_BASE_URL}/execute`,
      requestWithEnv,
    );
    return response.data;
  },

  executeGraphStreaming(
    request: ExecuteRequest,
    onStatus: (status: ExecutionStatus) => void,
    onComplete: (results: { [nodeId: string]: any }) => void,
    onError: (error: string) => void,
  ): () => void {
    // Use fetch for SSE instead of EventSource to support POST requests
    const controller = new AbortController();
    const env_vars = getEnvVars();
    const requestWithEnv = { ...request, env_vars };

    fetch(`${API_BASE_URL}/execute/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestWithEnv),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error("Response body is null");
        }

        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });

          // Process complete SSE messages
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6); // Remove 'data: ' prefix
              try {
                const statusUpdate = JSON.parse(data);

                if (statusUpdate.status === "done") {
                  // Execution complete
                  onComplete(statusUpdate.results || {});
                } else if (
                  statusUpdate.status === "error" &&
                  !statusUpdate.node_id
                ) {
                  // Global error
                  onError(statusUpdate.error || "Unknown error");
                } else {
                  // Node status update
                  onStatus(statusUpdate as ExecutionStatus);
                }
              } catch (e) {
                console.error("Error parsing SSE data:", e);
              }
            }
          }
        }
      })
      .catch((error) => {
        if (error.name !== "AbortError") {
          onError(error.message || "Network error");
        }
      });

    // Return cleanup function
    return () => {
      controller.abort();
    };
  },
};
