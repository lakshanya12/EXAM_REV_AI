const BASE_URL = "http://localhost:8000";

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/upload`, { method: "POST", body: formData });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function getNotesStatus() {
  const res = await fetch(`${BASE_URL}/notes-status`);
  if (!res.ok) throw new Error("Failed to check notes status");
  return res.json();
}

export async function getRevisionPlan(topic, daysUntilExam, useFullNotes) {
  const formData = new FormData();
  formData.append("topic", topic);
  formData.append("days_until_exam", daysUntilExam);
  formData.append("use_full_notes", useFullNotes ? "true" : "false");
  const res = await fetch(`${BASE_URL}/revision-plan`, { method: "POST", body: formData });
  if (!res.ok) throw new Error("Failed to get revision plan");
  return res.json();
}

// confirmedExternal = true means user clicked "Yes, generate from general knowledge"
export async function getFlashcards(topic, useFullNotes, confirmedExternal = false) {
  const formData = new FormData();
  formData.append("topic", topic);
  formData.append("use_full_notes", useFullNotes ? "true" : "false");
  formData.append("confirmed_external", confirmedExternal ? "true" : "false");
  const res = await fetch(`${BASE_URL}/flashcards`, { method: "POST", body: formData });
  if (!res.ok) throw new Error("Failed to get flashcards");
  return res.json();
}

export async function getQuiz(topic, useFullNotes, confirmedExternal = false) {
  const formData = new FormData();
  formData.append("topic", topic);
  formData.append("use_full_notes", useFullNotes ? "true" : "false");
  formData.append("confirmed_external", confirmedExternal ? "true" : "false");
  const res = await fetch(`${BASE_URL}/quiz`, { method: "POST", body: formData });
  if (!res.ok) throw new Error("Failed to get quiz");
  return res.json();
}

export async function askQuestion(question) {
  const formData = new FormData();
  formData.append("question", question);
  const res = await fetch(`${BASE_URL}/ask`, { method: "POST", body: formData });
  if (!res.ok) throw new Error("Failed to get answer");
  return res.json();
}