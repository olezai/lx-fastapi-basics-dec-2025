<script>
  let {
    sessionSummary,
    getQuizNameById
  } = $props();
</script>

<div class="results-container">
  <h1>Quiz Results</h1>

  <div class="results-summary">
    <h2>{getQuizNameById(sessionSummary.quiz_id)}</h2>

    {#if sessionSummary.score !== undefined}
      <div class="score">
        <strong>Score:</strong>
        {sessionSummary.score} / {sessionSummary.question_count}
        ({Math.round((sessionSummary.score / sessionSummary.question_count) * 100)}%)
      </div>
    {/if}

    {#if sessionSummary.passed !== undefined}
      <div class="pass-status" class:passed={sessionSummary.passed}>
        {sessionSummary.passed ? "✅ PASSED" : "❌ FAILED"}
      </div>
    {/if}

  </div>

</div>

<style>
  .results-container {
    max-width: 600px;
    margin: 0 auto;
    padding: 40px;
    text-align: center;
  }

  .results-summary {
    background-color: light-dark(#f9f9f9, #2a2a2a);
    border: 1px solid light-dark(#ddd, #444);
    border-radius: 8px;
    padding: 30px;
    margin: 30px 0;
  }

  .score {
    font-size: 1.5rem;
    margin: 20px 0;
    color: light-dark(#333, #fff);
  }

  .pass-status {
    font-size: 1rem;
    font-weight: bold;
    margin: 20px 0;
    padding: 20px;
    border-radius: 8px;
  }

  .pass-status.passed {
    background-color: light-dark(#e8f5e9, #2d4a2f);
    color: light-dark(#2e7d32, #81c784);
  }

  .pass-status:not(.passed) {
    background-color: light-dark(#ffebee, #4a2d2d);
    color: light-dark(#c62828, #ef5350);
  }
</style>
