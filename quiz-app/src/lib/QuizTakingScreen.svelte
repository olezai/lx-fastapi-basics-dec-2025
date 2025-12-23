<script>
  import Question from "./Question.svelte";
  import AnswerReview from "./AnswerReview.svelte";

  let {
    session = $bindable(),
    ui = $bindable(),
    getQuizNameById,
    refreshSession,
    onQuizComplete
  } = $props();
</script>

<h1>{getQuizNameById(session.current.quiz_id)}</h1>

{#if session.currentQuestion}
  <Question bind:currentQuestion={session.currentQuestion} currentSession={session.current} sessionSummary={session.summary} bind:review={session.review} bind:loading={ui.loading} bind:error={ui.error} onSessionUpdate={refreshSession}/>
{:else}
  <AnswerReview bind:currentQuestion={session.currentQuestion} currentSession={session.current} answers={session.current.answers} bind:review={session.review} bind:loading={ui.loading} bind:error={ui.error} {onQuizComplete}/>
{/if}

<style>
  h1 {
    text-align: center;
    color: light-dark(#333, #fff);
    margin-bottom: 30px;
  }
</style>
