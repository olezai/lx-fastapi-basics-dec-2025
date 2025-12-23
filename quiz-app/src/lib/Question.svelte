<script>
  import { onMount } from "svelte";
  import { fetchNextQuestion, putSubmitAnswer } from "./utils.js";
  import ProgressBar from "./ProgressBar.svelte";

  let {
    currentQuestion = $bindable(),
    currentSession,
    sessionSummary,
    review = $bindable(),
    loading = $bindable(),
    error = $bindable(),
    onSessionUpdate
  } = $props();

  let selectedAnswer = $state(null);

  onMount(() => {
    // Load previously selected answer if reviewing
    const answer = getAnswerByQuestionId(currentQuestion.id);
    if (answer) {
      selectedAnswer = answer.selected_option;
    }
  });

  function getAnswerByQuestionId(questionId) {
    if (!currentSession.answers || currentSession.answers.length === 0) {
      return null;
    }
    return currentSession.answers.find(
      (answer) => answer.quiz_question_id === questionId
    );
  }

  async function submitAnswer() {
    if (selectedAnswer === null) {
      error = "Please select an answer";
      return;
    }

    try {
      loading = true;
      error = null;

      // Submit the answer
      await putSubmitAnswer(
        currentSession.id,
        currentQuestion.id,
        selectedAnswer
      );

      // Refresh session data
      currentSession = await onSessionUpdate(currentSession.id);

      // Check if session is still active
      if (!currentSession.is_active) {
        error = currentSession.completion_details || "Quiz session ended";
        return;
      }

      // Fetch next question
      currentQuestion = await fetchNextQuestion(currentSession.id);
      selectedAnswer = null;
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }
</script>

{#if currentQuestion}
  <ProgressBar
    current_q_index={currentQuestion.order_index}
    question_count={currentSession.question_count}
  />

  <div class="question-container">
    <h2>{currentQuestion.question}</h2>

    <div class="options">
      {#each currentQuestion.options as option (option.num)}
        <label class="option-label">
          <input
            type="radio"
            name="answer"
            value={option.num}
            bind:group={selectedAnswer}
          />
          <span>{option.num}. {option.text}</span>
        </label>
      {/each}
    </div>

    {#if review}
      <button
        onclick={() => {
          review = false;
          currentQuestion = null;
        }}
        disabled={selectedAnswer === null || loading}
      >
        Cancel
      </button>
    {/if}

    {#if !sessionSummary}
      <button onclick={submitAnswer} disabled={selectedAnswer === null || loading}>
        {loading ? "Submitting..." : review ? "Update Answer" : "Submit Answer"}
      </button>
    {/if}
  </div>
{/if}

<style>
  .question-container {
    border: 1px solid light-dark(#ddd, #444);
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    background-color: light-dark(#fff, #1a1a1a);
  }

  .question-container h2 {
    margin-top: 0;
    color: light-dark(#333, #fff);
  }

  .options {
    margin: 20px 0;
    display: flex;
    flex-direction: column;
    gap: 15px;
  }

  .option-label {
    display: flex;
    align-items: center;
    padding: 12px;
    border: 1px solid light-dark(#ddd, #444);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
    background-color: light-dark(#fff, #2a2a2a);
  }

  .option-label:hover {
    border-color: #646cff;
  }

  .option-label input {
    margin-right: 10px;
    cursor: pointer;
  }

  button {
    margin-top: 20px;
    margin-right: 10px;
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
