const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const TOKEN_KEY = "access_token";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request(path, options = {}) {
  const headers = {
    ...(options.headers || {}),
  };

  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Only add Content-Type when there is a body and it's not form data
  if (options.body && !(options.body instanceof URLSearchParams)) {
    headers["Content-Type"] = "application/json";
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
    const message = data?.detail || data?.message || "Request failed";
    throw new Error(message);
  }

  return data;
}

export const api = {
  // -------------------------
  // Auth
  // -------------------------
  async register(payload) {
    return request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async login({ username, password }) {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    const response = await request("/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    });

    if (response?.access_token) {
      setToken(response.access_token);
    }

    return response;
  },

  me() {
    return request("/auth/me");
  },

  logout() {
    clearToken();
  },

  getStoredToken() {
    return getToken();
  },

  // -------------------------
  // Networks
  // -------------------------
  listNetworks() {
    return request("/networks/");
  },

  createNetwork(payload) {
    return request("/networks/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateNetwork(networkId, payload) {
    return request(`/networks/${networkId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  deleteNetwork(networkId) {
    return request(`/networks/${networkId}`, {
      method: "DELETE",
    });
  },

  // -------------------------
  // Nodes
  // -------------------------
  listNodes(networkId) {
    return request(`/networks/${networkId}/nodes`);
  },

  createNode(networkId, payload) {
    return request(`/networks/${networkId}/nodes`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // -------------------------
  // Edges
  // -------------------------
  listEdges(networkId) {
    return request(`/networks/${networkId}/edges`);
  },

  createEdge(networkId, payload) {
    return request(`/networks/${networkId}/edges`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  learn(networkId, payload) {
    return request(`/networks/${networkId}/learn`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  decay(networkId) {
    return request(`/networks/${networkId}/decay`, {
      method: "POST",
    });
  },
};

export { API_BASE_URL };