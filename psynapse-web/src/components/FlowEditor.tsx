import React, { useState, useCallback, useRef, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  NodeTypes,
  OnConnect,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { BasicOpNode, ViewNode } from './nodes';
import NodeLibrary from './NodeLibrary';
import { backendClient } from '../api/client';
import { NodeSchema, NodeData, GraphData, GraphNode, GraphEdge } from '../types';

const nodeTypes: NodeTypes = {
  basicOp: BasicOpNode,
  view: ViewNode,
};

const FlowEditor: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [schemas, setSchemas] = useState<NodeSchema[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionError, setExecutionError] = useState<string | null>(null);
  
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);
  const nodeIdCounter = useRef(0);

  // Load node schemas on mount
  useEffect(() => {
    const loadSchemas = async () => {
      try {
        const response = await backendClient.getNodeSchemas();
        setSchemas(response.nodes);
      } catch (error) {
        console.error('Failed to load node schemas:', error);
      }
    };
    loadSchemas();
  }, []);

  const onConnect: OnConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => addEdge(connection, eds));
    },
    [setEdges]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      if (!reactFlowBounds || !reactFlowInstance) return;

      const schemaData = event.dataTransfer.getData('application/reactflow-schema');
      const isViewNode = event.dataTransfer.getData('application/reactflow-viewnode') === 'true';

      if (!schemaData && !isViewNode) return;

      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const newNodeId = `node_${nodeIdCounter.current++}`;

      if (isViewNode) {
        // Create View node
        const newNode: Node<NodeData> = {
          id: newNodeId,
          type: 'view',
          position,
          data: {
            label: 'View',
            nodeType: 'view',
            inputValues: {},
          },
        };
        setNodes((nds) => nds.concat(newNode));
      } else {
        // Create operation node
        const schema: NodeSchema = JSON.parse(schemaData);
        const newNode: Node<NodeData> = {
          id: newNodeId,
          type: 'basicOp',
          position,
          data: {
            label: schema.name,
            nodeType: schema.name,
            schema,
            inputValues: {},
          },
        };
        setNodes((nds) => nds.concat(newNode));
      }
    },
    [reactFlowInstance, setNodes]
  );

  const onDragStart = (
    event: React.DragEvent,
    schema: NodeSchema | null,
    isViewNode: boolean
  ) => {
    if (isViewNode) {
      event.dataTransfer.setData('application/reactflow-viewnode', 'true');
    } else if (schema) {
      event.dataTransfer.setData('application/reactflow-schema', JSON.stringify(schema));
    }
    event.dataTransfer.effectAllowed = 'move';
  };

  const serializeGraph = (): GraphData => {
    const graphNodes: GraphNode[] = nodes.map((node) => {
      const data = node.data as NodeData;
      const nodeType = data.nodeType;

      // Build input sockets
      const inputSockets = [];
      if (nodeType === 'view') {
        inputSockets.push({
          id: `${node.id}_input_0`,
          name: 'value',
          value: null,
        });
      } else if (data.schema) {
        data.schema.params.forEach((param, index) => {
          inputSockets.push({
            id: `${node.id}_input_${index}`,
            name: param.name.toLowerCase(),
            value: data.inputValues[param.name] ?? param.default ?? 0,
          });
        });
      }

      // Build output sockets
      const outputSockets = [];
      if (nodeType !== 'view') {
        outputSockets.push({
          id: `${node.id}_output_0`,
          name: 'result',
        });
      }

      return {
        id: node.id,
        type: nodeType,
        input_sockets: inputSockets,
        output_sockets: outputSockets,
        position: [node.position.x, node.position.y],
        size: [200, 100],
        filepath: data.schema?.filepath,
      };
    });

    const graphEdges: GraphEdge[] = edges.map((edge) => ({
      start_socket: `${edge.source}_${edge.sourceHandle}`,
      end_socket: `${edge.target}_${edge.targetHandle}`,
    }));

    return {
      nodes: graphNodes,
      edges: graphEdges,
    };
  };

  const executeGraph = async () => {
    setIsExecuting(true);
    setExecutionError(null);

    try {
      const graphData = serializeGraph();
      console.log('Serialized graph:', graphData);
      
      const response = await backendClient.executeGraph({ graph: graphData });
      console.log('Execution response:', response);

      // Update view nodes with results
      setNodes((nds) =>
        nds.map((node) => {
          if (node.data.nodeType === 'view') {
            const result = response.results[node.id];
            console.log(`Updating view node ${node.id} with result:`, result);
            
            if (result) {
              // Create completely new node object to ensure React Flow detects the change
              return {
                ...node,
                data: {
                  label: node.data.label,
                  nodeType: node.data.nodeType,
                  schema: node.data.schema,
                  inputValues: { ...node.data.inputValues },
                  outputValue: result.value,
                  error: result.error,
                },
              };
            }
          }
          return node;
        })
      );
    } catch (error) {
      console.error('Execution error:', error);
      setExecutionError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="flow-editor-container">
      <div className="toolbar">
        <h1>Psynapse Web</h1>
        <button
          className="execute-button"
          onClick={executeGraph}
          disabled={isExecuting}
        >
          {isExecuting ? 'Executing...' : 'Execute'}
        </button>
        {executionError && (
          <div className="error-message">{executionError}</div>
        )}
      </div>
      <div className="editor-content">
        <NodeLibrary schemas={schemas} onDragStart={onDragStart} />
        <div className="flow-wrapper" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
};

export default FlowEditor;

