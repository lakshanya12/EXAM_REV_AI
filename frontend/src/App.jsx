// App.jsx — Main app shell, revision plan is now inside Upload Notes tab

import { useState } from "react";
import Upload from "./components/Upload";
import Flashcards from "./components/Flashcards";
import Quiz from "./components/Quiz";
import QAChat from "./components/QAChat";
import "./App.css";

// Removed "Revision Plan" from tabs — it lives inside Upload Notes now
const TABS = ["Upload Notes", "Flashcards", "Quiz", "Ask a Question"];

export default function App() {
  const [activeTab, setActiveTab] = useState("Upload Notes");

  return (
    <div className="app">
      <header className="app-header">
        <h1>Exam Revision Assistant</h1>
        <p>Upload your notes, get a study plan, flashcards, quizzes, and more!</p>
      </header>

      {/* Tab navigation */}
      <nav className="tab-bar">
        {TABS.map((tab) => (
          <button
            key={tab}
            className={`tab-btn ${activeTab === tab ? "active" : ""}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </nav>

      {/* Tab content */}
      <main className="tab-content">
        {activeTab === "Upload Notes" && <Upload />}
        {activeTab === "Flashcards"   && <Flashcards />}
        {activeTab === "Quiz"         && <Quiz />}
        {activeTab === "Ask a Question" && <QAChat />}
      </main>
    </div>
  );
}