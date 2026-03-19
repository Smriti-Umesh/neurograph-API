export default function DecayPanel({ onDecay, disabled }) {
  return (
    <div className="card-section">
      <h3>Decay</h3>
      <p className="muted">
        Reduce the weight of active edges. Weak edges are archived automatically when they cross the archive threshold.
      </p>
      <button type="button" onClick={onDecay} disabled={disabled}>
        Run decay
      </button>
    </div>
  );
}
