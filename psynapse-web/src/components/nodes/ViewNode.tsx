import React, { useEffect } from 'react';
import { Handle, Position } from 'reactflow';
import { NodeData } from '../../types';

interface ViewNodeProps {
  data: NodeData;
  id: string;
}

const ViewNode: React.FC<ViewNodeProps> = ({ data, id }) => {
  useEffect(() => {
    console.log(`ViewNode ${id} data updated:`, data);
  }, [data, id]);

  const renderValue = () => {
    if (data.error) {
      return <div className="view-error">{data.error}</div>;
    }

    if (data.outputValue === undefined || data.outputValue === null) {
      return <div className="view-placeholder">No value</div>;
    }

    const value = data.outputValue;

    // Handle different types of values
    if (typeof value === 'object' && !Array.isArray(value)) {
      // Display objects as formatted JSON
      return (
        <pre className="view-json">
          {JSON.stringify(value, null, 2)}
        </pre>
      );
    } else if (Array.isArray(value)) {
      // Display arrays
      return (
        <pre className="view-json">
          {JSON.stringify(value, null, 2)}
        </pre>
      );
    } else if (typeof value === 'number') {
      // Format numbers nicely
      return <div className="view-value">{value.toFixed(4)}</div>;
    } else {
      // Display as string
      return <div className="view-value">{String(value)}</div>;
    }
  };

  return (
    <div className="view-node">
      <div className="node-header">
        <span className="node-title">View</span>
      </div>
      <div className="node-body">
        <div className="socket-row">
          <Handle
            type="target"
            position={Position.Left}
            id="input_0"
            className="socket-handle input-handle"
          />
          <span className="socket-label">Value</span>
        </div>
      </div>
      <div className="view-content">
        {renderValue()}
      </div>
    </div>
  );
};

export default ViewNode;

