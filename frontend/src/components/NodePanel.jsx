import { useState } from 'react';

export default function NodePanel({ nodes, onCreateNode, disabled }) {
  const [label, setLabel] = useState('');
  const [nodeType, setNodeType] = useState('concept');

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmedLabel = label.trim();
    if (!trimmedLabel) return;

    await onCreateNode({
      label: trimmedLabel,
      node_type: nodeType,
    });

    setLabel('');
    setNodeType('concept');
  }

  return (
    <div className="card-section">
      <h3>Create node</h3>
      <form onSubmit={handleSubmit} className="stack-form">
        <label>
          <span>Node label</span>
          <input
            type="text"
            value={label}
            onChange={(event) => setLabel(event.target.value)}
            placeholder="e.g. Hippocampus"
            disabled={disabled}
          />
        </label>

        <label>
          <span>Node type</span>
          <input
            type="text"
            value={nodeType}
            onChange={(event) => setNodeType(event.target.value)}
            placeholder="concept / paper / author"
            disabled={disabled}
          />
        </label>

        <button type="submit" disabled={disabled || !label.trim()}>
          Add node
        </button>
      </form>

      <div className="compact-list">
        <h4>Current nodes</h4>
        {nodes.length === 0 ? (
          <p className="muted">No nodes yet.</p>
        ) : (
          nodes.map((node) => (
            <div key={node.id} className="compact-list-item">
              <strong>{node.label}</strong>
              <span>
                ID: {node.id} · Type: {node.node_type}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
