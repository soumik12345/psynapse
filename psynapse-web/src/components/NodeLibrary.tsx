import React from 'react';
import { NodeSchema } from '../types';

interface NodeLibraryProps {
  schemas: NodeSchema[];
  onDragStart: (event: React.DragEvent, schema: NodeSchema | null, isViewNode: boolean) => void;
}

const NodeLibrary: React.FC<NodeLibraryProps> = ({ schemas, onDragStart }) => {
  return (
    <div className="node-library">
      <h3>Node Library</h3>
      
      <div className="node-category">
        <h4>Built-in Nodes</h4>
        <div
          className="node-library-item"
          draggable
          onDragStart={(e) => onDragStart(e, null, true)}
        >
          <div className="node-icon">👁️</div>
          <div className="node-info">
            <div className="node-name">View</div>
            <div className="node-description">Display a value</div>
          </div>
        </div>
      </div>

      <div className="node-category">
        <h4>Basic Operations</h4>
        {schemas.map((schema) => (
          <div
            key={schema.name}
            className="node-library-item"
            draggable
            onDragStart={(e) => onDragStart(e, schema, false)}
          >
            <div className="node-icon">⚙️</div>
            <div className="node-info">
              <div className="node-name">{schema.name}</div>
              <div className="node-description">{schema.description}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NodeLibrary;

