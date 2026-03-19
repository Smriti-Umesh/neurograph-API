import { useState } from "react";
import { api } from "../api";

export default function AuthPanel({ currentUser, onLoginSuccess, onLogout }) {
  const [mode, setMode] = useState("login"); // "login" or "register"
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [email, setEmail] = useState("");
  const [registerUsername, setRegisterUsername] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function handleLogin(e) {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      await api.login({ username, password });
      const me = await api.me();
      onLoginSuccess(me);
      setMessage("Logged in successfully.");
      setUsername("");
      setPassword("");
    } catch (err) {
      setMessage(err.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      await api.register({
        email,
        username: registerUsername,
        password: registerPassword,
      });

      setMessage("Registration successful. You can now log in.");
      setEmail("");
      setRegisterUsername("");
      setRegisterPassword("");
      setMode("login");
    } catch (err) {
      setMessage(err.message || "Registration failed.");
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    api.logout();
    onLogout();
    setMessage("Logged out.");
  }

  return (
    <div className="panel">
      <h2>Authentication</h2>

      {currentUser ? (
        <div>
          <p>
            Logged in as <strong>{currentUser.username}</strong> ({currentUser.email})
          </p>
          <button onClick={handleLogout}>Logout</button>
          {message && <p>{message}</p>}
        </div>
      ) : (
        <div>
          <div style={{ marginBottom: "1rem" }}>
            <button
              onClick={() => setMode("login")}
              disabled={mode === "login"}
              style={{ marginRight: "0.5rem" }}
            >
              Login
            </button>
            <button
              onClick={() => setMode("register")}
              disabled={mode === "register"}
            >
              Register
            </button>
          </div>

          {mode === "login" ? (
            <form onSubmit={handleLogin}>
              <div style={{ marginBottom: "0.75rem" }}>
                <label>Username or Email</label>
                <br />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>

              <div style={{ marginBottom: "0.75rem" }}>
                <label>Password</label>
                <br />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              <button type="submit" disabled={loading}>
                {loading ? "Logging in..." : "Login"}
              </button>
            </form>
          ) : (
            <form onSubmit={handleRegister}>
              <div style={{ marginBottom: "0.75rem" }}>
                <label>Email</label>
                <br />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div style={{ marginBottom: "0.75rem" }}>
                <label>Username</label>
                <br />
                <input
                  type="text"
                  value={registerUsername}
                  onChange={(e) => setRegisterUsername(e.target.value)}
                  required
                />
              </div>

              <div style={{ marginBottom: "0.75rem" }}>
                <label>Password</label>
                <br />
                <input
                  type="password"
                  value={registerPassword}
                  onChange={(e) => setRegisterPassword(e.target.value)}
                  required
                />
              </div>

              <button type="submit" disabled={loading}>
                {loading ? "Registering..." : "Register"}
              </button>
            </form>
          )}

          {message && <p style={{ marginTop: "1rem" }}>{message}</p>}
        </div>
      )}
    </div>
  );
}