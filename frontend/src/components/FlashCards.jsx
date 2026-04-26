import { useState, useEffect } from "react";
import { getFlashcards, getNotesStatus } from "../api";

export default function Flashcards() {
  const [mode, setMode]               = useState("all");
  const [topic, setTopic]             = useState("");
  const [cards, setCards]             = useState([]);
  const [flipped, setFlipped]         = useState({});
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState("");
  const [notesStatus, setNotesStatus] = useState(null);
  const [checkingNotes, setCheckingNotes] = useState(true);

  // "not_found" dialog state
  const [showConfirm, setShowConfirm] = useState(false);
  const [pendingTopic, setPendingTopic] = useState("");

  useEffect(() => { checkNotes(); }, []);

  async function checkNotes() {
    setCheckingNotes(true);
    try {
      const status = await getNotesStatus();
      setNotesStatus(status);
    } catch {
      setNotesStatus({ has_notes: false, chunks: 0 });
    } finally {
      setCheckingNotes(false);
    }
  }

  // ── Main generate function ──
  async function handleGenerate(confirmedExternal = false) {
    if (mode === "specific" && !topic.trim()) {
      return setError("Please enter a topic name.");
    }

    setError("");
    setLoading(true);
    setCards([]);
    setFlipped({});
    setShowConfirm(false);

    try {
      const topicToSend  = mode === "all" ? "All topics" : topic;
      const useFullNotes = mode === "all";

      const data = await getFlashcards(topicToSend, useFullNotes, confirmedExternal);

      if (data.status === "ok" && data.flashcards?.length > 0) {
        // Success — show the cards
        setCards(data.flashcards);

      } else if (data.status === "not_found") {
        // Topic not in notes — show confirmation dialog
        setPendingTopic(topic);
        setShowConfirm(true);

      } else if (data.status === "no_notes") {
        setError("No notes uploaded yet. Go to 'Upload Notes' tab and upload your file first.");

      } else {
        setError("Could not generate flashcards. Please try again.");
      }

    } catch (err) {
      setError("Failed to connect to backend. Make sure it's running on port 8000.");
    } finally {
      setLoading(false);
    }
  }

  if (checkingNotes) {
    return (
      <div className="card">
        <h2>🃏 Flashcards</h2>
        <p style={{ color: "#888" }}>⏳ Checking notes...</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>🃏 Flashcards</h2>

      {/* ── Notes status banner ── */}
      <div style={{
        padding: "12px 16px", borderRadius: "8px", marginBottom: "20px",
        background: notesStatus?.has_notes ? "#f0fff4" : "#fff5f5",
        border: `1.5px solid ${notesStatus?.has_notes ? "#27ae60" : "#e74c3c"}`,
        display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "8px"
      }}>
        <span style={{ color: notesStatus?.has_notes ? "#1a5c30" : "#7b1a1a", fontWeight: "600", fontSize: "14px" }}>
          {notesStatus?.has_notes
            ? `✅ Notes ready — ${notesStatus.chunks} chunks in memory`
            : "⚠️ No notes uploaded — go to 'Upload Notes' tab first"}
        </span>
        <button onClick={checkNotes} style={{ background: "none", border: "1px solid #ccc", borderRadius: "6px", padding: "4px 12px", cursor: "pointer", fontSize: "12px" }}>
          🔄 Refresh
        </button>
      </div>

      {/* ── No notes state ── */}
      {!notesStatus?.has_notes && (
        <div style={{ textAlign: "center", padding: "40px 20px", color: "#888" }}>
          <div style={{ fontSize: "48px", marginBottom: "12px" }}>📂</div>
          <p style={{ fontSize: "15px" }}>Upload your notes first.</p>
          <p style={{ fontSize: "13px", marginTop: "6px" }}>Go to <strong>Upload Notes</strong> → upload your PDF or image → come back here.</p>
        </div>
      )}

      {/* ── Topic Not Found Confirmation Dialog ── */}
      {showConfirm && (
        <div style={{
          margin: "0 0 20px 0", padding: "24px",
          background: "#fff8e1", borderRadius: "12px",
          border: "2px solid #f39c12"
        }}>
          <div style={{ fontSize: "24px", marginBottom: "8px" }}>🔍</div>
          <h3 style={{ color: "#7d5a00", marginBottom: "8px" }}>
            "{pendingTopic}" not found in your notes
          </h3>
          <p style={{ color: "#7d5a00", fontSize: "14px", marginBottom: "20px" }}>
            This topic was not found in your uploaded notes.
            Do you want me to generate flashcards from <strong>general knowledge</strong> instead?
          </p>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <button
              onClick={() => handleGenerate(true)}
              className="btn-primary"
              style={{ background: "#e67e22" }}
            >
              ✅ Yes, generate from general knowledge
            </button>
            <button
              onClick={() => { setShowConfirm(false); setTopic(""); }}
              style={{
                padding: "12px 24px", border: "1.5px solid #ccc",
                borderRadius: "8px", cursor: "pointer",
                background: "white", fontSize: "15px"
              }}
            >
              ❌ No, I'll search a different topic
            </button>
          </div>
        </div>
      )}

      {/* ── Mode selector & generate form (hide after cards are generated) ── */}
      {notesStatus?.has_notes && !cards.length && !showConfirm && (
        <>
          <div style={{ display: "flex", gap: "12px", marginBottom: "20px", flexWrap: "wrap" }}>

            {/* All Topics */}
            <div
              onClick={() => { setMode("all"); setError(""); }}
              style={{
                flex: 1, minWidth: "180px", padding: "16px",
                border: `2px solid ${mode === "all" ? "#3b4cca" : "#ddd"}`,
                borderRadius: "10px", cursor: "pointer",
                background: mode === "all" ? "#eef0ff" : "white", transition: "all 0.2s"
              }}
            >
              <div style={{ fontSize: "24px", marginBottom: "6px" }}>📄</div>
              <div style={{ fontWeight: "700", color: mode === "all" ? "#3b4cca" : "#333" }}>All Topics in My Notes</div>
              <div style={{ fontSize: "12px", color: "#888", marginTop: "4px" }}>
                Flashcards covering every topic found in your uploaded file — from notes only
              </div>
              {mode === "all" && <div style={{ color: "#3b4cca", fontSize: "12px", marginTop: "6px", fontWeight: "600" }}>✓ Selected</div>}
            </div>

            {/* Specific Topic */}
            <div
              onClick={() => { setMode("specific"); setError(""); }}
              style={{
                flex: 1, minWidth: "180px", padding: "16px",
                border: `2px solid ${mode === "specific" ? "#3b4cca" : "#ddd"}`,
                borderRadius: "10px", cursor: "pointer",
                background: mode === "specific" ? "#eef0ff" : "white", transition: "all 0.2s"
              }}
            >
              <div style={{ fontSize: "24px", marginBottom: "6px" }}>🎯</div>
              <div style={{ fontWeight: "700", color: mode === "specific" ? "#3b4cca" : "#333" }}>Specific Topic</div>
              <div style={{ fontSize: "12px", color: "#888", marginTop: "4px" }}>
                Searches notes first. If not found, asks you before using general knowledge
              </div>
              {mode === "specific" && <div style={{ color: "#3b4cca", fontSize: "12px", marginTop: "6px", fontWeight: "600" }}>✓ Selected</div>}
            </div>
          </div>

          {/* Topic input */}
          {mode === "specific" && (
            <div style={{ marginBottom: "16px" }}>
              <input
                type="text"
                placeholder="e.g. Neural Networks, Linked Lists, Photosynthesis..."
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
                className="text-input"
              />
              <p style={{ fontSize: "12px", color: "#666", marginTop: "6px" }}>
                🔍 We'll search your notes first. If the topic isn't there, we'll ask before using general knowledge.
              </p>
            </div>
          )}

          {mode === "all" && (
            <div style={{ padding: "10px 14px", background: "#eef0ff", borderRadius: "8px", marginBottom: "16px", fontSize: "13px", color: "#3b4cca", border: "1px solid #c5caff" }}>
              ℹ️ Will generate flashcards using <strong>only your uploaded notes</strong> — no external knowledge.
            </div>
          )}

          <button onClick={() => handleGenerate(false)} disabled={loading} className="btn-primary" style={{ width: "100%" }}>
            {loading ? "⏳ Searching notes and generating..." : "Generate Flashcards"}
          </button>

          {error && <p className="error" style={{ marginTop: "10px" }}>{error}</p>}
        </>
      )}

      {/* ── Flashcard Grid ── */}
      {cards.length > 0 && (
        <div style={{ marginTop: "8px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "8px" }}>
            <div>
              <span style={{ fontWeight: "600", color: "#3b4cca" }}>{cards.length} flashcards</span>
              <span style={{ color: "#888", fontSize: "13px", marginLeft: "8px" }}>
                — {cards[0]?.source === "notes" ? "📝 from your notes" : "🌐 from general knowledge"}
              </span>
            </div>
            <button
              onClick={() => { setCards([]); setFlipped({}); setShowConfirm(false); }}
              style={{ background: "none", border: "1px solid #ddd", borderRadius: "6px", padding: "4px 12px", cursor: "pointer", fontSize: "13px" }}
            >
              ← Generate New
            </button>
          </div>

          <div className="flashcard-grid">
            {cards.map((card, i) => (
              <div key={i} className={`flashcard ${flipped[i] ? "flipped" : ""}`} onClick={() => toggleFlip(i)}>
                <div className="flashcard-inner">

                  <div className="flashcard-front">
                    {card.topic && (
                      <div style={{ position: "absolute", top: "10px", left: "10px", background: "rgba(255,255,255,0.25)", borderRadius: "12px", padding: "2px 10px", fontSize: "11px", fontWeight: "600" }}>
                        {card.topic}
                      </div>
                    )}
                    <div style={{ position: "absolute", top: "10px", right: "10px", background: card.source === "notes" ? "rgba(39,174,96,0.85)" : "rgba(231,76,60,0.85)", borderRadius: "12px", padding: "2px 10px", fontSize: "10px", fontWeight: "600", color: "white" }}>
                      {card.source === "notes" ? "📝 Notes" : "🌐 External"}
                    </div>
                    <p style={{ marginTop: "30px", fontWeight: "600", padding: "0 8px", textAlign: "center" }}>❓ {card.question}</p>
                    <small style={{ opacity: 0.8, marginTop: "8px" }}>Click to reveal answer</small>
                  </div>

                  <div className="flashcard-back">
                    {card.topic && (
                      <div style={{ position: "absolute", top: "10px", left: "10px", background: "rgba(255,255,255,0.25)", borderRadius: "12px", padding: "2px 10px", fontSize: "11px", fontWeight: "600" }}>
                        {card.topic}
                      </div>
                    )}
                    <div style={{ position: "absolute", top: "10px", right: "10px", background: card.source === "notes" ? "rgba(39,174,96,0.85)" : "rgba(231,76,60,0.85)", borderRadius: "12px", padding: "2px 10px", fontSize: "10px", fontWeight: "600", color: "white" }}>
                      {card.source === "notes" ? "📝 Notes" : "🌐 External"}
                    </div>
                    <p style={{ marginTop: "30px", padding: "0 8px", textAlign: "center" }}>✅ {card.answer}</p>
                  </div>

                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  function toggleFlip(index) {
    setFlipped(prev => ({ ...prev, [index]: !prev[index] }));
  }
}