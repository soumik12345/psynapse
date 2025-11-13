import React, { useCallback } from 'react';
import { Handle, Position } from 'reactflow';
import { NodeData } from '../../types';

interface BasicOpNodeProps {
  data: NodeData;
  id: string;
}

const BasicOpNode: React.FC<BasicOpNodeProps> = ({ data, id }) => {
  const schema = data.schema;

  const handleInputChange = useCallback((paramName: string, value: string) => {
    const numValue = parseFloat(value);
    data.inputValues[paramName] = isNaN(numValue) ? (value === '' ? 0 : 0) : numValue;
    console.log(`Node ${id} input ${paramName} changed to:`, data.inputValues[paramName]);
  }, [data, id]);

  if (!schema) {
    return (
      <div className="basic-op-node">
        <div className="node-header">
          <span className="node-title">{data.label}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="basic-op-node">
      <div className="node-header">
        <span className="node-title">{data.label}</span>
      </div>
      <div className="node-body">
        {/* Input handles and fields */}
        {schema.params.map((param, index) => {
          const defaultValue = param.default !== undefined ? param.default : 0;
          // Initialize input value if not already set
          if (data.inputValues[param.name] === undefined) {
            data.inputValues[param.name] = defaultValue;
          }
          
          return (
            <div key={`input-${index}`} className="socket-row">
              <Handle
                type="target"
                position={Position.Left}
                id={`input_${index}`}
                className="socket-handle input-handle"
              />
              <input
                type="number"
                className="socket-input"
                placeholder={param.name}
                defaultValue={defaultValue}
                onChange={(e) => handleInputChange(param.name, e.target.value)}
              />
            </div>
          );
        })}
      </div>
      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Right}
        id="output_0"
        className="socket-handle output-handle"
      />
    </div>
  );
};

export default BasicOpNode;

