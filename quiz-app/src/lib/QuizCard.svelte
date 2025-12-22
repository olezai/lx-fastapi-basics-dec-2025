<script>
  let { quiz, topic } = $props();

  function formatTime(seconds) {
    if (!seconds) return 'Unlimited';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
</script>

<div class="quiz-card">
  <h2>{quiz.name}</h2>
  <p><strong>Topic:</strong> {topic}</p>
  <p><strong>Questions:</strong> {quiz.question_count}</p>
  {#if quiz.time_limit_seconds}
    <p><strong>Time Limit:</strong> {formatTime(quiz.time_limit_seconds)}</p>
  {:else}
    <p><strong>Time:</strong> Unlimited</p>
  {/if}
  {#if quiz.passing_ratio}
    <p><strong>Passing Score:</strong> {Math.round(quiz.passing_ratio * 100)}%</p>
  {/if}

  <!-- TODO: In Exercise 5.2, this button will be functional -->
  <button disabled>
    Start Quiz
  </button>
</div>

<style>
  .quiz-card {
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    font-size: 0.9rem;
    background-color: light-dark(#ffffff, #1a1a1a);
  }

  .quiz-card h2 {
    margin: 0 0 15px 0;
    color: light-dark(#333, #fff);
  }

  .quiz-card p {
    margin: 8px 0;
    color: light-dark(#666, #ccc);
  }

  button {
    margin-top: 15px;
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
