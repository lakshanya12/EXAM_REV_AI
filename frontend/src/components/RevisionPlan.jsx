// RevisionPlan.jsx — Generates and displays a structured study plan

import { useState } from "react";
import { getRevisionPlan } from "../api";

export default function RevisionPlan() {
  const [topic, setTopic] = useState("");
  const [plan, setPlan] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleGenerate() {
    if (!topic.trim()) return;
    setLoading(true);
    try {
      const data = await getRevisionPlan(topic);
      setPlan(data.plan);
    } catch {
      setPlan("Error generating plan. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h2>📅 Revision Plan</h2>
      <input
        type="text"
        placeholder="Enter topic (e.g. Machine Learning)"
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        className="text-input"
      />
      <button onClick={handleGenerate} disabled={loading} className="btn-primary">
        {loading ? "Generating..." : "Generate Plan"}
      </button>

      {plan && (
        <div className="output-box">
          <pre>{plan}</pre>
        </div>
      )}
    </div>
  );
}