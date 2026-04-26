# test_agents.py — Basic tests to verify agents return expected output types

import sys
sys.path.insert(0, "..")

from agents.flashcard_agent import generate_flashcards
from agents.quiz_agent import generate_quiz
from agents.qa_agent import answer_question

# ---- Test 1: Flashcards return a list ----
def test_flashcards_returns_list():
    result = generate_flashcards("Machine Learning")
    assert isinstance(result, list), "Flashcards should return a list"
    print("✅ test_flashcards_returns_list passed")

# ---- Test 2: Each flashcard has question and answer ----
def test_flashcard_structure():
    result = generate_flashcards("Machine Learning")
    if result:
        card = result[0]
        assert "question" in card, "Flashcard must have 'question'"
        assert "answer" in card, "Flashcard must have 'answer'"
    print("✅ test_flashcard_structure passed")

# ---- Test 3: Quiz returns a list ----
def test_quiz_returns_list():
    result = generate_quiz("Data Structures")
    assert isinstance(result, list), "Quiz should return a list"
    print("✅ test_quiz_returns_list passed")

# ---- Test 4: QA agent returns a non-empty string ----
def test_qa_returns_string():
    result = answer_question("What is a linked list?")
    assert isinstance(result, str) and len(result) > 10
    print("✅ test_qa_returns_string passed")

if __name__ == "__main__":
    test_flashcards_returns_list()
    test_flashcard_structure()
    test_quiz_returns_list()
    test_qa_returns_string()
    print("\n🎉 All tests passed!")