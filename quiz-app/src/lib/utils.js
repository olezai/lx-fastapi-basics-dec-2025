const API_QUIZ_BASE = 'http://localhost:8001';

/**
 * Helper function to create error messages from API responses
 * @param {Response} res - The fetch response object
 * @param {string} defaultMessage - Default error message if no detail is available
 * @returns {Promise<string>} - The error message
 */
async function getErrorMessage(res, defaultMessage) {
  try {
    const data = await res.json();
    return data.detail || defaultMessage;
  } catch {
    return defaultMessage;
  }
}

/**
 * Fetch quizzes and extract unique topics from them
 * @returns {Promise<{quizzes: Array, topics: Array}>}
 */
export async function fetchQuizzesData() {
  const quizzesRes = await fetch(`${API_QUIZ_BASE}/quizzes/`);

  if (!quizzesRes.ok) {
    const errorMsg = await getErrorMessage(quizzesRes, 'Failed to fetch quizzes');
    throw new Error(errorMsg);
  }

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

/**
 * Start a new quiz session
 * @param {string} quizId - The ID of the quiz to start
 * @returns {Promise<Object>} - The new quiz session object
 */
export async function postStartQuiz(quizId) {
  const res = await fetch(`${API_QUIZ_BASE}/quizzes/${quizId}/start`, {
    method: 'POST'
  });

  if (!res.ok) {
    const errorMsg = await getErrorMessage(res, 'Failed to start quiz');
    throw new Error(errorMsg);
  }

  const newSession = await res.json();
  return newSession;
}

/**
 * Get quiz session statistics and details
 * @param {string} quizSessionId - The quiz session ID
 * @returns {Promise<Object>} - Session stats with answers array
 */
export async function getQuizSessionStats(quizSessionId) {
  const res = await fetch(`${API_QUIZ_BASE}/sessions/${quizSessionId}`, {
    method: 'GET'
  });

  if (!res.ok) {
    const errorMsg = await getErrorMessage(res, 'Failed to get quiz session details');
    throw new Error(errorMsg);
  }

  const sessionStats = await res.json();
  return sessionStats;
}

/**
 * Submit or update an answer for a quiz question
 * @param {string} quizSessionId - The quiz session ID
 * @param {string} quizQuestionId - The quiz question ID
 * @param {number} selectedAnswer - The selected option number
 * @returns {Promise<Object>} - The selected option confirmation
 */
export async function putSubmitAnswer(quizSessionId, quizQuestionId, selectedAnswer) {
  const res = await fetch(
    `${API_QUIZ_BASE}/sessions/${quizSessionId}/answers/${quizQuestionId}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ selected_option: selectedAnswer })
    }
  );

  if (!res.ok) {
    const errorMsg = await getErrorMessage(res, 'Failed to submit answer');
    throw new Error(errorMsg);
  }

  const selectedOption = await res.json();
  return selectedOption;
}

/**
 * Fetch the next unanswered question in the quiz session
 * @param {string} sessionId - The quiz session ID
 * @returns {Promise<Object|null>} - The next question object, or null if no more questions
 */
export async function fetchNextQuestion(sessionId) {
  const res = await fetch(`${API_QUIZ_BASE}/sessions/${sessionId}/questions/next`);

  // Status 204 means no more questions
  if (res.status === 204) {
    return null;
  }

  if (!res.ok) {
    const errorMsg = await getErrorMessage(res, 'Failed to fetch question');
    throw new Error(errorMsg);
  }

  const currentQuestion = await res.json();
  return currentQuestion;
}

/**
 * Fetch a specific question by ID (for review)
 * @param {string} questionId - The quiz question ID
 * @returns {Promise<Object>} - The question object with options
 */
export async function fetchQuestionByID(questionId) {
  const res = await fetch(`${API_QUIZ_BASE}/quiz-questions/${questionId}`);

  if (!res.ok) {
    const errorMsg = await getErrorMessage(res, 'Failed to fetch question');
    throw new Error(errorMsg);
  }

  const currentQuestion = await res.json();
  return currentQuestion;
}

/**
 * Fetch quiz details including all questions with their order_index
 * @param {string} quizId - The quiz ID
 * @returns {Promise<Object>} - The quiz details with questions array
 */
export async function fetchQuizDetails(quizId) {
  const res = await fetch(`${API_QUIZ_BASE}/quizzes/${quizId}`);

  if (!res.ok) {
    const errorMsg = await getErrorMessage(res, 'Failed to fetch quiz details');
    throw new Error(errorMsg);
  }

  const quizDetails = await res.json();
  return quizDetails;
}

/**
 * @param {string} sessionId - The quiz session ID to submit
 * @returns {Promise<Object>} - The quiz session summary with results
 */
export async function postSubmitQuiz(sessionId) {
  const res = await fetch(`${API_QUIZ_BASE}/sessions/${sessionId}/submit`, {
    method: 'POST'
  });

  if (!res.ok) {
    const errorMsg = await getErrorMessage(res, 'Failed to submit quiz');
    throw new Error(errorMsg);
  }

  const sessionSummary = await res.json();
  return sessionSummary;
}