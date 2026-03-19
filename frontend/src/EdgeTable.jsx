function getNodeLabel(nodes, nodeId) {
  return nodes.find((node) => node.id === nodeId)?.label || `Node ${nodeId}`;
}

export default function EdgeTable({ edges, nodes, loading }) {
  if (loading) {
    return <div className="empty-state">Loading edges...</div>;
  }

  if (edges.length === 0) {
    return <div className="empty-state">No edges to display.</div>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Source</th>
            <th>Target</th>
            <th>Relationship</th>
            <th>Weight</th>
            <th>Activations</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {edges.map((edge) => (
            <tr key={edge.id}>
              <td>{edge.id}</td>
              <td>
                {getNodeLabel(nodes, edge.source_node_id)}
                <div className="table-subtext">ID: {edge.source_node_id}</div>
              </td>
              <td>
                {getNodeLabel(nodes, edge.target_node_id)}
                <div className="table-subtext">ID: {edge.target_node_id}</div>
              </td>
              <td>{edge.relationship_type}</td>
              <td>{edge.weight}</td>
              <td>{edge.activation_count}</td>
              <td>
                <span className={`badge ${edge.is_active ? 'badge-active' : 'badge-archived'}`}>
                  {edge.is_active ? 'Active' : 'Archived'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
