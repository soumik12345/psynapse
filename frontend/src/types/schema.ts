export interface ParamSchema {
  name: string;
  type: string;
  default?: any;
  literal_values?: string[];
}

export interface ReturnSchema {
  name: string;
  type: string;
}

export interface FunctionSchema {
  name: string;
  params: ParamSchema[];
  returns: ReturnSchema[];
  docstring: string;
  filepath: string;
  is_progress_node?: boolean;
}

export interface NodeData {
  label: string;
  functionName?: string;
  params?: ParamSchema[];
  docstring?: string;
  executionStatus?: "executing" | "completed" | "error";
  variableName?: string;
  variableType?: "String" | "Number" | "Boolean" | "Object" | "List" | "Image";
  variableValue?: string | number | boolean | any[] | object;
  textContentFormat?: boolean;
  imageContentFormat?: boolean;
  llmMessageFormat?: boolean;
  llmMessageRole?: "system" | "user" | "assistant";
  inputCount?: number;
  [key: string]: any;
}

export interface ExecuteRequest {
  nodes: any[];
  edges: any[];
  env_vars?: Record<string, string>;
}

export interface ExecuteResponse {
  results: { [nodeId: string]: any };
}

export interface ExecutionStatus {
  node_id: string;
  node_number: number;
  node_name: string;
  status: "executing" | "completed" | "error" | "progress";
  inputs?: Record<string, any>;
  output?: any;
  error?: string;
  progress?: number;
  progress_message?: string;
}
