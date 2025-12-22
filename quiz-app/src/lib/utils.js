const API_QUIZ_BASE = 'http://localhost:8001';

/**
 * Fetch quizzes and extract unique topics from them
 * @returns {Promise<{quizzes: Array, topics: Array}>}
 */
export async function fetchQuizzesData() {
  console.log("Loading quizzes...");

  const quizzesRes = await fetch(`${API_QUIZ_BASE}/quizzes/`);

  if (!quizzesRes.ok) throw new Error('Failed to fetch quizzes: ${quizzesRes.status}');

  const quizzes = await quizzesRes.json();

  // Extract unique topics from quizzes
  const topicMap = new Map();
  quizzes.forEach(quiz => {
    if (!topicMap.has(quiz.topic_id)) {
      topicMap.set(quiz.topic_id, {
        id: quiz.topic_id,
        name: quiz.topic_name
      });
    }
  });

  const topics = Array.from(topicMap.values());

  return { quizzes, topics };
}
