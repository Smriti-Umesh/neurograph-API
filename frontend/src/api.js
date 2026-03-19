const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function request(path, options = {}) {
  const headers = {
    ...(options.headers || {}),
  };

  // Only add Content-Type when there is a body
  if (options.body) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message = data?.detail || data?.message || 'Request failed';
    throw new Error(message);
  }

  return data;
}

export const api = {
  listNetworks() {
    return request('/networks/');
  },
  createNetwork(payload) {
    return request('/networks/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  listNodes(networkId) {
    return request(`/networks/${networkId}/nodes`);
  },
  createNode(networkId, payload) {
    return request(`/networks/${networkId}/nodes`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  listEdges(networkId) {
    return request(`/networks/${networkId}/edges`);
  },
  createEdge(networkId, payload) {
    return request(`/networks/${networkId}/edges`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  learn(networkId, payload) {
    return request(`/networks/${networkId}/learn`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  decay(networkId) {
    return request(`/networks/${networkId}/decay`, {
      method: 'POST',
    });
  },
};

export { API_BASE_URL };