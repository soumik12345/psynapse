// Type definitions for Psynapse Web

export interface NodeSchema {
  name: string;
  description: string;
  params: Array<{
    name: string;
    type: string;
    description: string;
    default?: any;
  }>;
  returns: {
    type: string;
    description: string;
  };
  filepath: string;
}

export interface Socket {
  id: string;
  name: string;
  value?: any;
}

export interface GraphNode {
  id: string;
  type: string;
  input_sockets: Socket[];
  output_sockets: Socket[];
  position: [number, number];
  size: [number, number];
  params?: any;
  filepath?: string;
  source_nodepack?: string;
}

export interface GraphEdge {
  start_socket: string;
  end_socket: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ExecutionRequest {
  graph: GraphData;
  env_vars?: Record<string, string>;
}

export interface ExecutionResult {
  value: any;
  error: string | null;
}

export interface ExecutionResponse {
  results: Record<string, ExecutionResult>;
}

export interface NodesResponse {
  nodes: NodeSchema[];
}

// React Flow specific types
export interface NodeData {
  label: string;
  nodeType: string;
  schema?: NodeSchema;
  inputValues: Record<string, any>;
  outputValue?: any;
  error?: string;
}

