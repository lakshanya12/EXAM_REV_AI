import { useState, useEffect } from "react";
import { getQuiz, getNotesStatus } from "../api";

export default function Quiz() {
  const [mode, setMode]           = useState("all");
  const [topic, setTopic]         = useState("");
  const [questions, setQuestions] = useState([]);
  const [selected, setSelected]   = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState("");
  const [notesStatus, setNotesStatus] = useState(null);
  const [checkingNotes, setCheckingNotes] = useState(true);
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

  async function handleGenerate(confirmedExternal = false) {
    if (mode === "specific" && !topic.trim()) return setError("Please enter a topic name.");

    setError("");
    setLoading(true);
    setQuestions([]);
    setSelected({});
    setSubmitted(false);
    setShowConfirm(false);

    try {
      const topicToSend  = mode === "all" ? "All topics" : topic;
      const useFullNotes = mode === "all";
      const data = await getQuiz(topicToSend, useFullNotes, confirmedExternal);

      if (data.status === "ok" && data.quiz?.length > 0) {
        setQuestions(data.quiz);
      } else if (data.status === "not_found") {
        setPendingTopic(topic);
        setShowConfirm(true);
      } else if (data.status === "no_notes") {
        setError("No notes uploaded yet. Go to 'Upload Notes' tab first.");
      } else {
        setError("Could not generate quiz. Please try again.");
      }
    } catch {
      setError("Failed to connect to backend. Make sure it's running on port 8000.");
    } finally {
      setLoading(false);
    }
  }

  function calcScore() { return questions.filter((q, i) => selected[i] === q.answer).length; }
  function getScoreColor() {
    const pct = calcScore() / questions.length;
    return pct >= 0.8 ? "#27ae60" : pct >= 0.5 ? "#e67e22" : "#e74c3c";
  }

  if (checkingNotes) return <div className="card"><h2>🧠 Quiz Me</h2><p style={{ color: "#888" }}>⏳ Checking notes...</p></div>;

  return (
    <div className="card">
      <h2>🧠 Quiz Me</h2>

      {/* Notes status */}
      <div style={{ padding: "12px 16px", borderRadius: "8px", marginBottom: "20px", background: notesStatus?.has_notes ? "#f0fff4" : "#fff5f5", border: `1.5px solid ${notesStatus?.has_notes ? "#27ae60" : "#e74c3c"}`, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "8px" }}>
        <span style={{ color: notesStatus?.has_notes ? "#1a5c30" : "#7b1a1a", fontWeight: "600", fontSize: "14px" }}>
          {notesStatus?.has_notes ? `Notes ready — ${notesStatus.chunks} chunks in memory` : "⚠️ No notes uploaded — go to 'Upload Notes' tab first"}
        </span>
        <button onClick={checkNotes} style={{ background: "none", border: "1px solid #ccc", borderRadius: "6px", padding: "4px 12px", cursor: "pointer", fontSize: "12px" }}>🔄 Refresh</button>
      </div>

      {/* No notes state */}
      {!notesStatus?.has_notes && (
        <div style={{ textAlign: "center", padding: "40px 20px", color: "#888" }}>
          <div style={{ fontSize: "48px", marginBottom: "12px" }}>📂</div>
          <p style={{ fontSize: "15px" }}>Upload your notes first.</p>
          <p style={{ fontSize: "13px", marginTop: "6px" }}>Go to <strong>Upload Notes</strong> → upload your file → come back here.</p>
        </div>
      )}

      {/* Not found confirmation dialog */}
      {showConfirm && (
        <div style={{ margin: "0 0 20px 0", padding: "24px", background: "#fff8e1", borderRadius: "12px", border: "2px solid #f39c12" }}>
          <div style={{ fontSize: "24px", marginBottom: "8px" }}>🔍</div>
          <h3 style={{ color: "#7d5a00", marginBottom: "8px" }}>"{pendingTopic}" not found in your notes</h3>
          <p style={{ color: "#7d5a00", fontSize: "14px", marginBottom: "20px" }}>
            This topic was not found in your uploaded notes. Do you want me to generate a quiz from <strong>general knowledge</strong> instead?
          </p>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <button onClick={() => handleGenerate(true)} className="btn-primary" style={{ background: "#e67e22" }}>
              Yes, generate from general knowledge
            </button>
            <button onClick={() => { setShowConfirm(false); setTopic(""); }} style={{ padding: "12px 24px", border: "1.5px solid #ccc", borderRadius: "8px", cursor: "pointer", background: "white", fontSize: "15px" }}>
               No, I'll search a different topic
            </button>
          </div>
        </div>
      )}

      {/* Mode selector */}
      {notesStatus?.has_notes && !questions.length && !showConfirm && (
        <>
          <div style={{ display: "flex", gap: "12px", marginBottom: "20px", flexWrap: "wrap" }}>
            <div onClick={() => { setMode("all"); setError(""); }} style={{ flex: 1, minWidth: "180px", padding: "16px", border: `2px solid ${mode === "all" ? "#3b4cca" : "#ddd"}`, borderRadius: "10px", cursor: "pointer", background: mode === "all" ? "#eef0ff" : "white", transition: "all 0.2s" }}>
              <div style={{ fontSize: "24px", marginBottom: "6px" }}>📄</div>
              <div style={{ fontWeight: "700", color: mode === "all" ? "#3b4cca" : "#333" }}>All Topics in My Notes</div>
              <div style={{ fontSize: "12px", color: "#888", marginTop: "4px" }}>Questions from every topic in your uploaded file</div>
              {mode === "all" && <div style={{ color: "#3b4cca", fontSize: "12px", marginTop: "6px", fontWeight: "600" }}>✓ Selected</div>}
            </div>
            <div onClick={() => { setMode("specific"); setError(""); }} style={{ flex: 1, minWidth: "180px", padding: "16px", border: `2px solid ${mode === "specific" ? "#3b4cca" : "#ddd"}`, borderRadius: "10px", cursor: "pointer", background: mode === "specific" ? "#eef0ff" : "white", transition: "all 0.2s" }}>
              <div style={{ fontSize: "24px", marginBottom: "6px" }}>🎯</div>
              <div style={{ fontWeight: "700", color: mode === "specific" ? "#3b4cca" : "#333" }}>Specific Topic</div>
              <div style={{ fontSize: "12px", color: "#888", marginTop: "4px" }}>Searches notes first. If not found, asks before using general knowledge</div>
              {mode === "specific" && <div style={{ color: "#3b4cca", fontSize: "12px", marginTop: "6px", fontWeight: "600" }}>✓ Selected</div>}
            </div>
          </div>

          {mode === "specific" && (
            <div style={{ marginBottom: "16px" }}>
              <input type="text" placeholder="e.g. Sorting Algorithms, Photosynthesis..." value={topic} onChange={(e) => setTopic(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleGenerate()} className="text-input" />
              <p style={{ fontSize: "12px", color: "#666", marginTop: "6px" }}>🔍 We'll search your notes first. If the topic isn't there, we'll ask before using general knowledge.</p>
            </div>
          )}

          {mode === "all" && (
            <div style={{ padding: "10px 14px", background: "#eef0ff", borderRadius: "8px", marginBottom: "16px", fontSize: "13px", color: "#3b4cca", border: "1px solid #c5caff" }}>
              ℹ️ Will generate quiz using <strong>only your uploaded notes</strong> — no external knowledge.
            </div>
          )}

          <button onClick={() => handleGenerate(false)} disabled={loading} className="btn-primary" style={{ width: "100%" }}>
            {loading ? "⏳ Searching notes and generating..." : "Start Quiz"}
          </button>
          {error && <p className="error" style={{ marginTop: "10px" }}>{error}</p>}
        </>
      )}

      {/* Questions */}
      {questions.length > 0 && (
        <div style={{ marginTop: "8px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <div>
              <span style={{ fontWeight: "600", color: "#3b4cca" }}>{questions.length} questions</span>
              <span style={{ color: "#888", fontSize: "13px", marginLeft: "8px" }}>
                — {questions[0]?.source === "notes" ? "📝 from your notes" : "🌐 from general knowledge"}
              </span>
            </div>
            {!submitted && (
              <button onClick={() => { setQuestions([]); setSelected({}); }} style={{ background: "none", border: "1px solid #ddd", borderRadius: "6px", padding: "4px 12px", cursor: "pointer", fontSize: "13px" }}>← Change Mode</button>
            )}
          </div>

          {questions.map((q, i) => (
            <div key={i} style={{ marginBottom: "24px", padding: "16px", background: "#f7f9ff", borderRadius: "10px", border: "1px solid #e0e4ff" }}>
              <div style={{ display: "flex", gap: "8px", marginBottom: "10px", flexWrap: "wrap" }}>
                {q.topic && <span style={{ background: "#3b4cca", color: "white", borderRadius: "12px", padding: "2px 12px", fontSize: "11px", fontWeight: "600" }}>{q.topic}</span>}
                {q.source && <span style={{ background: q.source === "notes" ? "#d4edda" : "#fdecea", color: q.source === "notes" ? "#1a5c30" : "#7b1a1a", borderRadius: "12px", padding: "2px 12px", fontSize: "11px", fontWeight: "600" }}>{q.source === "notes" ? "📝 From Notes" : "🌐 External Knowledge"}</span>}
              </div>
              <p style={{ fontWeight: "600", marginBottom: "12px", fontSize: "15px" }}>Q{i + 1}: {q.question}</p>
              {q.options.map((opt) => {
                const letter = opt[0];
                const isCorrect = letter === q.answer;
                const isSelected = selected[i] === letter;
                let bg = "white", borderColor = "#ddd", color = "#333";
                if (submitted) {
                  if (isCorrect) { bg = "#d4edda"; borderColor = "#27ae60"; color = "#1a5c30"; }
                  else if (isSelected) { bg = "#f8d7da"; borderColor = "#e74c3c"; color = "#7b1a1a"; }
                } else if (isSelected) { bg = "#eef0ff"; borderColor = "#3b4cca"; color = "#3b4cca"; }
                return (
                  <button key={opt} onClick={() => !submitted && setSelected({ ...selected, [i]: letter })} style={{ display: "block", width: "100%", textAlign: "left", padding: "10px 14px", margin: "6px 0", border: `1.5px solid ${borderColor}`, borderRadius: "8px", cursor: submitted ? "default" : "pointer", background: bg, color, fontSize: "14px", transition: "all 0.15s" }}>
                    {opt}
                  </button>
                );
              })}
              {submitted && <div style={{ marginTop: "10px", padding: "10px 14px", background: "#fff8e1", borderRadius: "8px", borderLeft: "3px solid #f39c12", fontSize: "13px", color: "#7d5a00" }}>💡 {q.explanation}</div>}
            </div>
          ))}

          {!submitted ? (
            <button className="btn-primary" style={{ width: "100%", padding: "14px", fontSize: "16px" }} onClick={() => setSubmitted(true)}>
              Submit Answers ({Object.keys(selected).length}/{questions.length} answered)
            </button>
          ) : (
            <div>
              <div style={{ padding: "24px", borderRadius: "12px", textAlign: "center", background: "#f0fff4", border: `2px solid ${getScoreColor()}` }}>
                <div style={{ fontSize: "48px", fontWeight: "bold", color: getScoreColor() }}>{calcScore()}/{questions.length}</div>
                <div style={{ fontSize: "18px", color: "#555", marginTop: "4px" }}>
                  {calcScore() === questions.length ? "🎉 Perfect score!" : calcScore() >= questions.length * 0.8 ? "🌟 Great job!" : calcScore() >= questions.length * 0.5 ? "👍 Keep revising!" : "📖 Review your notes and try again!"}
                </div>
              </div>
              <button className="btn-primary" style={{ width: "100%", marginTop: "16px" }} onClick={() => { setQuestions([]); setSelected({}); setSubmitted(false); }}>
                🔄Try Again / New Quiz
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}