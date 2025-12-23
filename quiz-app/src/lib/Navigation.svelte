<script>
  let {
    appScreen = $bindable(),
    currentSession,
    sessionSummary,
    onRefreshSession
  } = $props();
</script>

<div class="debug-navigation">
  <p> [===== {appScreen} =====]</p>
  <button onclick={() => (appScreen = "quiz-list")} style="margin-right: 8px;">
    Go to Quiz List
  </button>
  <button
    onclick={async () => {
      if (sessionSummary && currentSession) {
        await onRefreshSession(currentSession.id);
      }
      appScreen = "quiz-taking";
    }}
    style="margin-right: 8px;"
    disabled={currentSession == null}
  >
    Go to Quiz
  </button>
  <button onclick={() => (appScreen = "results")} disabled={sessionSummary == null}>
    Go to Results
  </button>
</div>

<style>
  .debug-navigation {
    margin-bottom: 10px;
  }

  button {
    border-radius: 8px;
    border: 1px solid transparent;
    padding: 0.6em 1.2em;
    font-size: 1em;
    font-weight: 500;
    font-family: inherit;
    background-color: light-dark(#f9f9f9, #1a1a1a);
    color: light-dark(#000, white);
    cursor: pointer;
    transition: border-color 0.25s;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 8px;
  }

  button:not(:disabled):hover {
    border-color: #646cff;
  }

  button:disabled {
    background-color: light-dark(#e0e0e0, #444);
    color: light-dark(#999, #666);
    cursor: not-allowed;
    opacity: 0.6;
  }

  button:focus,
  button:focus-visible {
    outline: 4px auto -webkit-focus-ring-color;
  }
</style>
