import { useState } from 'react';

export default function NetworkPanel({
  networks,
  selectedNetworkId,
  onSelectNetwork,
  onCreateNetwork,
  loading,
}) {
  const [name, setName] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) return;

    await onCreateNetwork(trimmedName);
    setName('');
  }

  return (
    <div>
      <h2>Networks</h2>
      <form onSubmit={handleSubmit} className="stack-form">
        <label>
          <span>New network name</span>
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="e.g. Brain Knowledge Graph"
            disabled={loading}
          />
        </label>
        <button type="submit" disabled={loading || !name.trim()}>
          Create network
        </button>
      </form>

      <div className="list-block">
        <label htmlFor="networkSelect">Select network</label>
        <select
          id="networkSelect"
          value={selectedNetworkId}
          onChange={(event) => onSelectNetwork(event.target.value)}
          disabled={loading || networks.length === 0}
        >
          {networks.length === 0 ? (
            <option value="">No networks yet</option>
          ) : null}
          {networks.map((network) => (
            <option key={network.id} value={network.id}>
              {network.name} (ID: {network.id})
            </option>
          ))}
        </select>
      </div>

      <div className="simple-list">
        {networks.length === 0 ? (
          <p className="muted">No networks created yet.</p>
        ) : (
          networks.map((network) => (
            <button
              key={network.id}
              type="button"
              className={`list-item-button ${String(selectedNetworkId) === String(network.id) ? 'selected' : ''}`}
              onClick={() => onSelectNetwork(String(network.id))}
            >
              <strong>{network.name}</strong>
              <span>ID: {network.id}</span>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
