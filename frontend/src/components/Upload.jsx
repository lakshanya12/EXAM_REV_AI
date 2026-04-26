// Upload.jsx — Upload notes, exam countdown, smart revision plan with mode selector

import { useState } from "react";
import { uploadFile, getRevisionPlan } from "../api";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [fullText, setFullText] = useState("");
  const [examDate, setExamDate] = useState("");
  const [daysLeft, setDaysLeft] = useState(null);
  const [topic, setTopic] = useState("");
  const [plan, setPlan] = useState("");
  const [uploadLoading, setUploadLoading] = useState(false);
  const [planLoading, setPlanLoading] = useState(false);
  const [error, setError] = useState("");
  const [uploadDone, setUploadDone] = useState(false);

  // "all" = cover everything in notes, "specific" = only the typed topic
  const [planMode, setPlanMode] = useState("all");

  // ── Calculate days left when exam date is picked ──
  function handleExamDateChange(e) {
    const selected = e.target.value;
    setExamDate(selected);

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const exam = new Date(selected);
    exam.setHours(0, 0, 0, 0);

    const diff = Math.ceil((exam - today) / (1000 * 60 * 60 * 24));
    setDaysLeft(diff > 0 ? diff : 0);
  }

  // ── Upload and extract full text ──
  async function handleUpload() {
    if (!file) return setError("Please select a file first.");
    setError("");
    setUploadLoading(true);
    setFullText("");
    setUploadDone(false);
    setPlan("");

    try {
      const data = await uploadFile(file);
      setFullText(data.full_text || data.preview || "No text extracted.");
      setUploadDone(true);
    } catch (err) {
      setError("Upload failed. Make sure the backend is running on port 8000.");
    } finally {
      setUploadLoading(false);
    }
  }

  // ── Generate the revision plan ──
  async function handleGeneratePlan() {
    // Validate inputs
    if (planMode === "specific" && !topic.trim()) {
      return setError("Please enter a specific topic name.");
    }
    if (!daysLeft || daysLeft <= 0) {
      return setError("Please set a valid future exam date.");
    }

    setError("");
    setPlanLoading(true);
    setPlan("");

    try {
      // If mode is "all", we pass the filename as topic (just a label)
      // If mode is "specific", we pass the typed topic
      const topicToSend = planMode === "all" ? "All topics from my notes" : topic;
      const useFullNotes = planMode === "all";

      const data = await getRevisionPlan(topicToSend, daysLeft, useFullNotes);
      setPlan(data.plan);
    } catch (err) {
      setError("Failed to generate plan. Check backend terminal for details.");
    } finally {
      setPlanLoading(false);
    }
  }

  // ── Urgency color based on days left ──
  function getUrgencyColor() {
    if (daysLeft === null) return "#3b4cca";
    if (daysLeft <= 3) return "#e74c3c";
    if (daysLeft <= 7) return "#e67e22";
    return "#27ae60";
  }

  function getUrgencyMessage() {
    if (daysLeft === null) return "";
    if (daysLeft === 0) return "⚠️ Exam is TODAY! Focus on key topics only.";
    if (daysLeft <= 3) return "🔴 Very little time! Prioritize hardest topics NOW.";
    if (daysLeft <= 7) return "🟡 One week left — follow the plan strictly.";
    if (daysLeft <= 14) return "🟢 Good time — steady and consistent study wins.";
    return "✅ Plenty of time — build a strong foundation first.";
  }

  // ── Render markdown-like plan with basic formatting ──
  function renderPlan(text) {
    return text.split("\n").map((line, i) => {
      // Section headers like ## 📅 ...
      if (line.startsWith("## ")) {
        return (
          <h3 key={i} style={{ color: "#3b4cca", marginTop: "20px", marginBottom: "8px", fontSize: "17px" }}>
            {line.replace("## ", "")}
          </h3>
        );
      }
      // Day headers like **Day 1 — ...**
      if (line.startsWith("**Day") || line.startsWith("**day")) {
        return (
          <div key={i} style={{
            background: "#3b4cca", color: "white",
            padding: "10px 16px", borderRadius: "8px",
            marginTop: "16px", marginBottom: "6px",
            fontWeight: "bold", fontSize: "15px"
          }}>
            {line.replace(/\*\*/g, "")}
          </div>
        );
      }
      // Table rows
      if (line.startsWith("|")) {
        return (
          <div key={i} style={{
            fontFamily: "monospace", fontSize: "13px",
            padding: "4px 8px", borderBottom: "1px solid #eee"
          }}>
            {line}
          </div>
        );
      }
      // Bullet points
      if (line.startsWith("- ")) {
        return (
          <div key={i} style={{ padding: "3px 0 3px 16px", fontSize: "14px", color: "#444" }}>
            {line}
          </div>
        );
      }
      // Tip lines
      if (line.includes("💡")) {
        return (
          <div key={i} style={{
            background: "#fff8e1", borderLeft: "3px solid #f39c12",
            padding: "6px 12px", margin: "4px 0",
            fontSize: "13px", color: "#7d5a00", borderRadius: "0 6px 6px 0"
          }}>
            {line}
          </div>
        );
      }
      // Empty lines
      if (!line.trim()) return <div key={i} style={{ height: "6px" }} />;
      // Normal lines
      return <div key={i} style={{ fontSize: "14px", padding: "2px 0", color: "#333" }}>{line}</div>;
    });
  }

  return (
    <div>

      {/* ════════════════════════════════════════
          SECTION 1 — File Upload
      ════════════════════════════════════════ */}
      <div className="card">
        <h2>📤 Upload Your Notes</h2>
        <p style={{ color: "#666", marginBottom: "16px" }}>
          Supports PDF, PNG, JPG — handwritten or typed. Full text will be extracted below.
        </p>

        <input
          type="file"
          accept=".pdf,.png,.jpg,.jpeg"
          onChange={(e) => {
            setFile(e.target.files[0]);
            setUploadDone(false);
            setFullText("");
            setPlan("");
          }}
          className="file-input"
        />

        <button onClick={handleUpload} disabled={uploadLoading} className="btn-primary">
          {uploadLoading ? "⏳ Extracting Text..." : "Upload & Extract Text"}
        </button>

        {error && <p className="error" style={{ marginTop: "10px" }}>{error}</p>}

        {/* Full extracted text */}
        {fullText && (
          <div style={{ marginTop: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ color: "#27ae60" }}>✅ Extracted Text</h3>
              <span style={{ fontSize: "12px", color: "#888", background: "#f0f0f0", padding: "4px 10px", borderRadius: "20px" }}>
                {fullText.split(" ").filter(Boolean).length} words · {fullText.length} chars
              </span>
            </div>
            <div style={{
              marginTop: "12px", background: "#f7f9ff",
              border: "1.5px solid #dde3ff", borderRadius: "10px",
              padding: "16px", maxHeight: "300px", overflowY: "auto",
              fontFamily: "monospace", fontSize: "13px",
              lineHeight: "1.8", whiteSpace: "pre-wrap", wordBreak: "break-word"
            }}>
              {fullText}
            </div>
          </div>
        )}
      </div>

      {/* ════════════════════════════════════════
          SECTION 2 — Exam Countdown
      ════════════════════════════════════════ */}
      {uploadDone && (
        <div className="card" style={{ marginTop: "20px" }}>
          <h2>⏳ When is Your Exam?</h2>
          <p style={{ color: "#666", marginBottom: "16px" }}>
            Pick your exam date and we'll build a plan that fits your timeline.
          </p>

          <input
            type="date"
            value={examDate}
            onChange={handleExamDateChange}
            min={new Date().toISOString().split("T")[0]}
            className="text-input"
            style={{ maxWidth: "240px" }}
          />

          {/* Days left counter */}
          {daysLeft !== null && (
            <div style={{
              marginTop: "16px", padding: "20px",
              background: daysLeft <= 3 ? "#fff5f5" : daysLeft <= 7 ? "#fff8f0" : "#f0fff4",
              borderRadius: "12px",
              border: `2px solid ${getUrgencyColor()}`,
              textAlign: "center"
            }}>
              <div style={{ fontSize: "56px", fontWeight: "bold", color: getUrgencyColor() }}>
                {daysLeft}
              </div>
              <div style={{ fontSize: "18px", color: "#555" }}>
                {daysLeft === 1 ? "day" : "days"} until your exam
              </div>
              <div style={{ marginTop: "8px", fontSize: "14px", color: getUrgencyColor(), fontWeight: "600" }}>
                {getUrgencyMessage()}
              </div>
            </div>
          )}

          {/* ── Plan Mode Selector ── */}
          {daysLeft !== null && daysLeft > 0 && (
            <div style={{ marginTop: "24px" }}>
              <label style={{ fontWeight: "700", fontSize: "15px", display: "block", marginBottom: "12px" }}>
                📚 What should the revision plan cover?
              </label>

              {/* Mode toggle buttons */}
              <div style={{ display: "flex", gap: "12px", marginBottom: "20px", flexWrap: "wrap" }}>

                {/* Option 1 — Everything in the file */}
                <div
                  onClick={() => { setPlanMode("all"); setError(""); }}
                  style={{
                    flex: 1, minWidth: "200px", padding: "16px",
                    border: `2px solid ${planMode === "all" ? "#3b4cca" : "#ddd"}`,
                    borderRadius: "10px", cursor: "pointer",
                    background: planMode === "all" ? "#eef0ff" : "white",
                    transition: "all 0.2s"
                  }}
                >
                  <div style={{ fontSize: "24px", marginBottom: "6px" }}>📄</div>
                  <div style={{ fontWeight: "700", color: planMode === "all" ? "#3b4cca" : "#333" }}>
                    Everything in My Notes
                  </div>
                  <div style={{ fontSize: "13px", color: "#888", marginTop: "4px" }}>
                    The AI reads all your uploaded notes and builds a plan covering every topic it finds
                  </div>
                  {planMode === "all" && (
                    <div style={{ marginTop: "8px", color: "#3b4cca", fontSize: "13px", fontWeight: "600" }}>
                      ✓ Selected
                    </div>
                  )}
                </div>

                {/* Option 2 — Specific topic */}
                <div
                  onClick={() => { setPlanMode("specific"); setError(""); }}
                  style={{
                    flex: 1, minWidth: "200px", padding: "16px",
                    border: `2px solid ${planMode === "specific" ? "#3b4cca" : "#ddd"}`,
                    borderRadius: "10px", cursor: "pointer",
                    background: planMode === "specific" ? "#eef0ff" : "white",
                    transition: "all 0.2s"
                  }}
                >
                  <div style={{ fontSize: "24px", marginBottom: "6px" }}>🎯</div>
                  <div style={{ fontWeight: "700", color: planMode === "specific" ? "#3b4cca" : "#333" }}>
                    Specific Topic
                  </div>
                  <div style={{ fontSize: "13px", color: "#888", marginTop: "4px" }}>
                    Focus the plan on one particular topic or chapter you want to revise
                  </div>
                  {planMode === "specific" && (
                    <div style={{ marginTop: "8px", color: "#3b4cca", fontSize: "13px", fontWeight: "600" }}>
                      ✓ Selected
                    </div>
                  )}
                </div>
              </div>

              {/* Topic input — only shows when specific mode is selected */}
              {planMode === "specific" && (
                <div style={{ marginBottom: "16px" }}>
                  <label style={{ fontWeight: "600", display: "block", marginBottom: "8px", fontSize: "14px" }}>
                    Enter the topic you want to focus on:
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Neural Networks, Linked Lists, Thermodynamics..."
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    className="text-input"
                  />
                </div>
              )}

              {/* Info banner for "all" mode */}
              {planMode === "all" && (
                <div style={{
                  padding: "12px 16px", background: "#eef0ff",
                  borderRadius: "8px", marginBottom: "16px",
                  fontSize: "13px", color: "#3b4cca",
                  border: "1px solid #c5caff"
                }}>
                  ℹ️ The AI will read your uploaded notes, find all topics automatically, 
                  rate their difficulty, and spread them across your {daysLeft} days — giving 
                  harder topics more time.
                </div>
              )}

              {/* Generate button */}
              <button
                onClick={handleGeneratePlan}
                disabled={planLoading}
                className="btn-primary"
                style={{ width: "100%", padding: "14px", fontSize: "16px" }}
              >
                {planLoading
                  ? "⏳ Building your personalised plan..."
                  : `🗓️ Generate My ${daysLeft}-Day Revision Plan`}
              </button>

              {error && <p className="error" style={{ marginTop: "10px" }}>{error}</p>}
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════
          SECTION 3 — Revision Plan Output
      ════════════════════════════════════════ */}
      {plan && (
        <div className="card" style={{ marginTop: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "8px" }}>
            <h2 style={{ margin: 0 }}>
              📅 Your {daysLeft}-Day Plan
              {planMode === "specific" && ` — ${topic}`}
            </h2>
            <span style={{
              background: planMode === "all" ? "#3b4cca" : "#27ae60",
              color: "white", padding: "4px 14px",
              borderRadius: "20px", fontSize: "12px", fontWeight: "600"
            }}>
              {planMode === "all" ? "📄 Full Notes Coverage" : "🎯 Specific Topic"}
            </span>
          </div>

          {/* Rendered plan */}
          <div style={{
            background: "#f7f9ff", borderRadius: "10px",
            padding: "20px", lineHeight: "1.8"
          }}>
            {renderPlan(plan)}
          </div>

          {/* Bottom tip */}
          <div style={{
            marginTop: "16px", padding: "12px 16px",
            background: "#fff8e1", borderRadius: "8px",
            borderLeft: "4px solid #f39c12",
            fontSize: "13px", color: "#7d5a00"
          }}>
            💡 <strong>Next steps:</strong> Use the <strong>Flashcards</strong> tab to memorise key concepts 
            and the <strong>Quiz</strong> tab to test yourself on each day's topic!
          </div>
        </div>
      )}

    </div>
  );
}