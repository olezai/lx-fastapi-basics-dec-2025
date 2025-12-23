<script>
  import { onDestroy } from "svelte";

  let {
    timeLeft = $bindable(null),
    onTimeExpired
  } = $props();

  let timerInterval = null;

  // Start timer when timeLeft is set
  $effect(() => {
    if (timeLeft !== null && timeLeft > 0) {
      // Start the countdown
      startCountdown();
    } else if (timeLeft !== null && timeLeft <= 0) {
      // Timer expired
      clearInterval(timerInterval);
      timerInterval = null;
      if (onTimeExpired) {
        onTimeExpired();
      }
    }

    return () => {
      if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
      }
    };
  });

  function startCountdown() {
    // Clear existing interval
    if (timerInterval) {
      clearInterval(timerInterval);
    }

    // Create new interval
    timerInterval = setInterval(() => {
      if (timeLeft > 0) {
        timeLeft -= 1;
      }
    }, 1000);
  }

  onDestroy(() => {
    if (timerInterval) {
      clearInterval(timerInterval);
    }
  });

  // Format time display (MM:SS)
  function formatTime(seconds) {
    if (!seconds && seconds !== 0) return "Unlimited";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  }
</script>

{#if timeLeft !== null}
  <div class="timer-display">
    <strong>⏱️ Timer</strong>
    <div class="time" class:warning={timeLeft < 60}>
      {formatTime(timeLeft)}
    </div>
  </div>
{/if}

<style>
  .timer-display {
    padding: 10px;
    margin-bottom: 10px;
    background-color: light-dark(#f0f0f0, #2a2a2a);
    border: 1px solid light-dark(#ddd, #444);
    border-radius: 4px;
  }

  .timer-display strong {
    display: block;
    margin-bottom: 5px;
    font-size: 0.9rem;
  }

  .time {
    font-size: 1.3rem;
    font-weight: bold;
    color: light-dark(#2e7d32, #81c784);
    font-family: monospace;
  }

  .time.warning {
    color: light-dark(#e65100, #ffb74d);
    animation: pulse 1s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
</style>
