// API client for communicating with Psynapse backend

import {
  NodesResponse,
  ExecutionRequest,
  ExecutionResponse,
} from '../types';

const BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export class BackendClient {
  private baseUrl: string;

  constructor(baseUrl: string = BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async getNodeSchemas(): Promise<NodesResponse> {
    const response = await fetch(`${this.baseUrl}/nodes`);
    if (!response.ok) {
      throw new Error(`Failed to fetch node schemas: ${response.status}`);
    }
    return await response.json();
  }

  async executeGraph(request: ExecutionRequest): Promise<ExecutionResponse> {
    const response = await fetch(`${this.baseUrl}/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to execute graph: ${response.status} - ${errorText}`);
    }

    return await response.json();
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        signal: AbortSignal.timeout(2000),
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

export const backendClient = new BackendClient();

