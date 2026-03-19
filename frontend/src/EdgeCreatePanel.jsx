import { useMemo, useState } from 'react';

export default function EdgeCreatePanel({ nodes, onCreateEdge, disabled }) {
  const [sourceNodeId, setSourceNodeId] = useState('');
  const [targetNodeId, setTargetNodeId] = useState('');
  const [relationshipType, setRelationshipType] = useState('related_to');

  const canSubmit = useMemo(() => {
    return sourceNodeId && targetNodeId && sourceNodeId !== targetNodeId && relationshipType.trim();
  }, [sourceNodeId, targetNodeId, relationshipType]);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!canSubmit) return;

    await onCreateEdge({
      source_node_id: Number(sourceNodeId),
      target_node_id: Number(targetNodeId),
      relationship_type: relationshipType.trim(),
    });

    setSourceNodeId('');
    setTargetNodeId('');
    setRelationshipType('related_to');
  }

  return (
    <div className="card-section">
      <h3>Create edge</h3>
      <form onSubmit={handleSubmit} className="stack-form">
        <label>
          <span>Source node</span>
          <select
            value={sourceNodeId}
            onChange={(event) => setSourceNodeId(event.target.value)}
            disabled={disabled || nodes.length === 0}
          >
            <option value="">Select source</option>
            {nodes.map((node) => (
              <option key={node.id} value={node.id}>
                {node.label} (ID: {node.id})
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Target node</span>
          <select
            value={targetNodeId}
            onChange={(event) => setTargetNodeId(event.target.value)}
            disabled={disabled || nodes.length === 0}
          >
            <option value="">Select target</option>
            {nodes.map((node) => (
              <option key={node.id} value={node.id}>
                {node.label} (ID: {node.id})
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Relationship type</span>
          <input
            type="text"
            value={relationshipType}
            onChange={(event) => setRelationshipType(event.target.value)}
            disabled={disabled}
          />
        </label>

        <button type="submit" disabled={disabled || !canSubmit}>
          Add edge
        </button>
      </form>
    </div>
  );
}
