<script>
  import { onMount } from "svelte";
  import { fetchQuestionByID, postSubmitQuiz, fetchQuizDetails } from "./utils.js";

  let {
    currentQuestion = $bindable(),
    currentSession,
    answers = [],
    review = $bindable(),
    loading = $bindable(),
    error = $bindable(),
    onQuizComplete
  } = $props();

  let questionOrderMap = $state({});

  onMount(async () => {
    try {
      // Fetch quiz details to get question order indices
      const quizDetails = await fetchQuizDetails(currentSession.quiz_id);

      // Create a mapping of quiz_question_id to order_index
      const orderMap = {};
      quizDetails.questions.forEach(q => {
        orderMap[q.id] = q.order_index;
      });
      questionOrderMap = orderMap;
    } catch (err) {
      console.error('Failed to fetch quiz details:', err);
      error = err.message;
    }
  });

  // Reactively sort answers whenever answers or questionOrderMap changes
  let sortedAnswers = $derived(
    [...answers].sort((a, b) => {
      const orderA = questionOrderMap[a.quiz_question_id] ?? Infinity;
      const orderB = questionOrderMap[b.quiz_question_id] ?? Infinity;
      return orderA - orderB;
    })
  );

  function formatTime(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    }).format(date);
  }

  async function handleReview(questionId) {
    try {
      currentQuestion = await fetchQuestionByID(questionId);
      review = true;
    } catch (err) {
      console.error('Failed to fetch question:', err);
      error = err.message;
    }
  }

async function handleSubmitQuiz() {
  try {
    loading = true;
    error = null;

    // Submit the quiz
    const sessionSummary = await postSubmitQuiz(currentSession.id);

    // Notify parent that quiz is complete
    onQuizComplete(sessionSummary);
  } catch (err) {
    error = err.message;
  } finally {
    loading = false;
  }
}
</script>

<div class="answers-review">
  <h3>Answer Review</h3>

  {#if sortedAnswers.length === 0}
    <p>No answers submitted yet.</p>
  {:else}
    <div class="answers-list">
      {#each sortedAnswers as answer, index (answer.id)}
        <div class="answer-item">
          <div class="answer-header">
            <span class="answer-number">Question {index + 1}.</span>
            <span class="answered-time {answer.answered_at ? '' : 'unanswered'}">
              {answer.answered_at ? formatTime(answer.answered_at) : 'Unanswered'}
            </span>
          </div>
          <div class="answer-row">
            <div class="answer-content">
              <span>
                {answer.is_correct === null ? '🔵': answer.is_correct ? '✅': '❌'}
              </span>
              <span>
                <strong>Option selected:</strong>
                {answer.selected_option || 'None'}
              </span>
            </div>
            <button class="review-btn" onclick={() => {handleReview(answer.quiz_question_id);}}>Review </button>
          </div>
        </div>
      {/each}
    </div>

    <div class="submit-section">
        <button onclick={handleSubmitQuiz} disabled={loading || currentSession.completed_at} class="submit-btn">
          {loading ? 'Submitting...' : 'Submit Quiz'}
        </button>
    </div>
  {/if}
</div>

<style>
  .answers-review {
    margin-top: 30px;
  }

  .answers-list {
    display: flex;
    flex-direction: column;
    gap: 15px;
    margin-bottom: 20px;
  }

  .answer-item {
    padding: 15px;
    border: 1px solid light-dark(#ddd, #444);
    border-radius: 4px;
    background-color: light-dark(#fff, #2a2a2a);
  }

  .answer-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
  }

  .answer-number {
    font-weight: bold;
    color: light-dark(#333, #fff);
  }

  .answered-time {
    margin-left: auto;
    font-size: 12px;
    color: light-dark(#999, #666);
  }

  .answered-time.unanswered {
    color: #dc3545;
    font-weight: 500;
  }

  .answer-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 15px;
  }

  .answer-content {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 14px;
    color: light-dark(#666, #ccc);
  }

  .review-btn {
    margin-top: 0;
    font-size: 12px;
    padding: 6px 12px;
    border-radius: 8px;
    border: 1px solid transparent;
    background-color: light-dark(#f9f9f9, #1a1a1a);
    color: light-dark(#000, white);
    cursor: pointer;
    transition: border-color 0.25s;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .review-btn:not(:disabled):hover {
    border-color: #646cff;
    background-color: light-dark(#f9f9f9, #1a1a1a);
  }

  .submit-section {
    margin-top: 30px;
    padding-top: 20px;
    border-top: 2px solid light-dark(#ddd, #444);
    text-align: center;
  }

  button {
    padding: 10px 20px;
    background-color: #646cff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
  }

  button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }

  button:not(:disabled):hover {
    background-color: #535bf2;
  }
</style>
