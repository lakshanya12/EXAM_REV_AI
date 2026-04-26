import { useState } from "react";
import { askQuestion } from "../api";

export default function QAChat() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  async function handleAsk() {
    if (!question.trim()) return;

    const userMsg = { role: "user", text: question };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setLoading(true);

    try {
      const data = await askQuestion(question);
      setMessages((prev) => [...prev, { role: "ai", text: data.answer }]);
    } catch {
      setMessages((prev) => [...prev, { role: "ai", text: "Error getting answer." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h2>💬 Ask a Question</h2>
      <p>I'll answer from your notes first, then from my knowledge if needed.</p>

      <div className="chat-window">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-msg ${msg.role}`}>
            <strong>{msg.role === "user" ? "You" : "Assistant"}:</strong>
            <p>{msg.text}</p>
          </div>
        ))}
        {loading && <p className="loading-text">Thinking...</p>}
      </div>

      <div className="chat-input-row">
        <input
          type="text"
          placeholder="Ask anything about your notes..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAsk()}
          className="text-input"
        />
        <button onClick={handleAsk} disabled={loading} className="btn-primary">
          Ask
        </button>
      </div>
    </div>
  );
}