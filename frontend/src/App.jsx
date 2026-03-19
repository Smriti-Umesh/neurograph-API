import { useEffect, useMemo, useState } from 'react';
import { api, API_BASE_URL } from './api';
import AuthPanel from './components/AuthPanel';
import NetworkPanel from './components/NetworkPanel';
import NodePanel from './components/NodePanel';
import EdgeCreatePanel from './components/EdgeCreatePanel';
import LearningPanel from './components/LearningPanel';
import DecayPanel from './components/DecayPanel';
import EdgeTable from './components/EdgeTable';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);

  const [networks, setNetworks] = useState([]);
  const [selectedNetworkId, setSelectedNetworkId] = useState('');
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loadingNetworks, setLoadingNetworks] = useState(false);
  const [loadingGraphData, setLoadingGraphData] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [edgeFilter, setEdgeFilter] = useState('all');

  const selectedNetwork = useMemo(
    () =>
      networks.find(
        (network) => String(network.id) === String(selectedNetworkId)
      ) || null,
    [networks, selectedNetworkId]
  );

  async function loadNetworks(preserveSelection = true) {
    try {
      setLoadingNetworks(true);
      setError('');
      const data = await api.listNetworks();
      setNetworks(data);

      if (!preserveSelection) {
        setSelectedNetworkId(data[0]?.id ? String(data[0].id) : '');
        return;
      }

      if (data.length === 0) {
        setSelectedNetworkId('');
        return;
      }

      const stillExists = data.some(
        (network) => String(network.id) === String(selectedNetworkId)
      );

      if (!selectedNetworkId || !stillExists) {
        setSelectedNetworkId(String(data[0].id));
      }
    } catch (err) {
      setError(err.message || 'Failed to load networks.');
      setNetworks([]);
      setSelectedNetworkId('');
    } finally {
      setLoadingNetworks(false);
    }
  }

  async function loadNetworkData(networkId) {
    if (!networkId) {
      setNodes([]);
      setEdges([]);
      return;
    }

    try {
      setLoadingGraphData(true);
      setError('');
      const [nodeData, edgeData] = await Promise.all([
        api.listNodes(networkId),
        api.listEdges(networkId),
      ]);
      setNodes(nodeData);
      setEdges(edgeData);
    } catch (err) {
      setError(err.message || 'Failed to load graph data.');
      setNodes([]);
      setEdges([]);
    } finally {
      setLoadingGraphData(false);
    }
  }

  useEffect(() => {
    async function checkAuth() {
      const token = api.getStoredToken();

      if (!token) {
        setAuthChecked(true);
        return;
      }

      try {
        const me = await api.me();
        setCurrentUser(me);
      } catch {
        api.logout();
        setCurrentUser(null);
      } finally {
        setAuthChecked(true);
      }
    }

    checkAuth();
  }, []);

  useEffect(() => {
    if (!currentUser) {
      setNetworks([]);
      setSelectedNetworkId('');
      setNodes([]);
      setEdges([]);
      return;
    }

    loadNetworks(false);
  }, [currentUser]);

  useEffect(() => {
    if (!currentUser) {
      setNodes([]);
      setEdges([]);
      return;
    }

    if (selectedNetworkId) {
      loadNetworkData(selectedNetworkId);
    } else {
      setNodes([]);
      setEdges([]);
    }
  }, [currentUser, selectedNetworkId]);

  function resetMessages() {
    setError('');
    setSuccess('');
  }

  function handleLoginSuccess(user) {
    setCurrentUser(user);
    setError('');
    setSuccess(`Logged in as ${user.username}.`);
  }

  function handleLogout() {
    api.logout();
    setCurrentUser(null);
    setNetworks([]);
    setSelectedNetworkId('');
    setNodes([]);
    setEdges([]);
    setError('');
    setSuccess('Logged out successfully.');
  }

  async function handleCreateNetwork(name) {
    try {
      setSubmitting(true);
      resetMessages();
      const created = await api.createNetwork({ name });
      await loadNetworks(true);
      setSelectedNetworkId(String(created.id));
      setSuccess(`Network "${created.name}" created successfully.`);
    } catch (err) {
      setError(err.message || 'Failed to create network.');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreateNode(payload) {
    if (!selectedNetworkId) return;

    try {
      setSubmitting(true);
      resetMessages();
      const created = await api.createNode(selectedNetworkId, payload);
      await loadNetworkData(selectedNetworkId);
      setSuccess(`Node "${created.label}" created successfully.`);
    } catch (err) {
      setError(err.message || 'Failed to create node.');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreateEdge(payload) {
    if (!selectedNetworkId) return;

    try {
      setSubmitting(true);
      resetMessages();
      await api.createEdge(selectedNetworkId, payload);
      await loadNetworkData(selectedNetworkId);
      setSuccess('Edge created successfully.');
    } catch (err) {
      setError(err.message || 'Failed to create edge.');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleLearn(payload) {
    if (!selectedNetworkId) return;

    try {
      setSubmitting(true);
      resetMessages();
      const result = await api.learn(selectedNetworkId, payload);
      await loadNetworkData(selectedNetworkId);
      setSuccess(result.message || 'Learning applied successfully.');
    } catch (err) {
      setError(err.message || 'Failed to apply learning.');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDecay() {
    if (!selectedNetworkId) return;

    try {
      setSubmitting(true);
      resetMessages();
      const result = await api.decay(selectedNetworkId);
      await loadNetworkData(selectedNetworkId);
      const count = result?.decayed_edges?.length ?? 0;
      setSuccess(
        `${result.message || 'Decay applied successfully.'} ${count} edge(s) updated.`
      );
    } catch (err) {
      setError(err.message || 'Failed to apply decay.');
    } finally {
      setSubmitting(false);
    }
  }

  const filteredEdges = useMemo(() => {
    if (edgeFilter === 'active') {
      return edges.filter((edge) => edge.is_active);
    }
    if (edgeFilter === 'archived') {
      return edges.filter((edge) => !edge.is_active);
    }
    return edges;
  }, [edges, edgeFilter]);

  const activeEdgeCount = edges.filter((edge) => edge.is_active).length;
  const archivedEdgeCount = edges.filter((edge) => !edge.is_active).length;

  if (!authChecked) {
    return (
      <div className="app-shell">
        <header className="page-header">
          <div>
            <h1>NeuroGraph Frontend</h1>
            <p className="muted">
              FastAPI base URL: <code>{API_BASE_URL}</code>
            </p>
          </div>
        </header>
        <div className="panel">Checking authentication...</div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="page-header">
        <div>
          <h1>NeuroGraph Frontend</h1>
          <p className="muted">
            FastAPI base URL: <code>{API_BASE_URL}</code>
          </p>
        </div>
      </header>

      <section className="panel">
        <AuthPanel
          currentUser={currentUser}
          onLoginSuccess={handleLoginSuccess}
          onLogout={handleLogout}
        />
      </section>

      {error ? <div className="alert alert-error">{error}</div> : null}
      {success ? <div className="alert alert-success">{success}</div> : null}

      {!currentUser ? (
        <section className="panel">
          <p>Please log in to use the application.</p>
        </section>
      ) : (
        <div className="layout-grid">
          <section className="panel">
            <NetworkPanel
              networks={networks}
              selectedNetworkId={selectedNetworkId}
              onSelectNetwork={setSelectedNetworkId}
              onCreateNetwork={handleCreateNetwork}
              loading={loadingNetworks || submitting}
            />
          </section>

          <section className="panel span-2">
            <div className="section-header">
              <div>
                <h2>Selected Network</h2>
                <p className="muted">
                  {selectedNetwork
                    ? `${selectedNetwork.name} (ID: ${selectedNetwork.id})`
                    : 'Create or select a network to begin.'}
                </p>
              </div>
              <button
                type="button"
                className="secondary-button"
                onClick={() => loadNetworkData(selectedNetworkId)}
                disabled={!selectedNetworkId || loadingGraphData || submitting}
              >
                Refresh
              </button>
            </div>

            {!selectedNetworkId ? (
              <div className="empty-state">No network selected yet.</div>
            ) : (
              <>
                <div className="stats-row">
                  <div className="stat-card">
                    <span className="stat-label">Nodes</span>
                    <strong>{nodes.length}</strong>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label">Edges</span>
                    <strong>{edges.length}</strong>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label">Active edges</span>
                    <strong>{activeEdgeCount}</strong>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label">Archived edges</span>
                    <strong>{archivedEdgeCount}</strong>
                  </div>
                </div>

                <div className="subgrid">
                  <NodePanel
                    nodes={nodes}
                    onCreateNode={handleCreateNode}
                    disabled={loadingGraphData || submitting}
                  />
                  <EdgeCreatePanel
                    nodes={nodes}
                    onCreateEdge={handleCreateEdge}
                    disabled={loadingGraphData || submitting}
                  />
                  <LearningPanel
                    nodes={nodes}
                    onLearn={handleLearn}
                    disabled={loadingGraphData || submitting}
                  />
                  <DecayPanel
                    onDecay={handleDecay}
                    disabled={loadingGraphData || submitting || edges.length === 0}
                  />
                </div>

                <div className="section-header edges-toolbar">
                  <div>
                    <h2>Edges</h2>
                    <p className="muted">
                      View active and archived edges after learning and decay.
                    </p>
                  </div>

                  <div className="filter-group">
                    <label htmlFor="edgeFilter">Show</label>
                    <select
                      id="edgeFilter"
                      value={edgeFilter}
                      onChange={(event) => setEdgeFilter(event.target.value)}
                    >
                      <option value="all">All edges</option>
                      <option value="active">Active only</option>
                      <option value="archived">Archived only</option>
                    </select>
                  </div>
                </div>

                <EdgeTable
                  edges={filteredEdges}
                  nodes={nodes}
                  loading={loadingGraphData}
                />
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}