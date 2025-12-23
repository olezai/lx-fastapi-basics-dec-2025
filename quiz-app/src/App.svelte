<script>
  import { onMount } from "svelte";
  import TopicFilter from "./lib/TopicFilter.svelte";
  import QuizCard from "./lib/QuizCard.svelte";
  import QuizTakingScreen from "./lib/QuizTakingScreen.svelte";
  import ResultsScreen from "./lib/ResultsScreen.svelte";
  import Timer from "./lib/Timer.svelte";
  import Navigation from "./lib/Navigation.svelte";
  import { fetchQuizzesData, postStartQuiz, getQuizSessionStats, fetchNextQuestion, postSubmitQuiz  } from "./lib/utils.js";

  // Grouped state management
  let ui = $state({
    screen: "quiz-list", // quiz-list, quiz-taking, results
    loading: false,
    error: null
  });

  let quizData = $state({
    quizzes: [],
    topics: [],
    selectedTopicFilter: null
  });

  let session = $state({
    current: null,
    summary: null,
    currentQuestion: null,
    review: false
  });

  let timer = $state({
    timeLeft: null
  });

  // Auto-fetch next question when entering quiz-taking screen with active session
  $effect(() => {
    if ( ui.screen === "quiz-taking" && session.current && !session.summary && !session.currentQuestion && !ui.loading && !session.review) {
      // Check if there are still unanswered questions
      const answeredCount = session.current.answers?.length || 0;
      const hasUnansweredQuestions = answeredCount < session.current.question_count;

      // Session is in progress but no current question loaded
      if (hasUnansweredQuestions) {
        // Fetch the next question
        (async () => {
          try {
            ui.loading = true;
            ui.error = null;
            session.currentQuestion = await fetchNextQuestion(session.current.id);
          } catch (err) {
            ui.error = err.message;
          } finally {
            ui.loading = false;
          }
        })();
      }
    }
  });

  // Fetch data on component mount
  onMount(async () => {
    try {
      ui.loading = true;
      ui.error = null;
      const data = await fetchQuizzesData();
      quizData.quizzes = data.quizzes;
      quizData.topics = data.topics;
    } catch (err) {
      ui.error = err.message;
    } finally {
      ui.loading = false;
    }
  });


  // filtered quizzes computed prop
  let filteredQuizzes = $derived(
    quizData.selectedTopicFilter === null
      ? quizData.quizzes
      : quizData.quizzes.filter((q) => q.topic_id === quizData.selectedTopicFilter)
  );

  // Helper: get topic name by ID
  function getTopicName(topicId) {
    return quizData.topics.find((t) => t.id === topicId)?.name || "Unknown";
  }

  // Helper: get quiz name by ID
  function getQuizNameById(quizId) {
    return quizData.quizzes.find((q) => q.id === quizId)?.name || "Unknown Quiz";
  }

  // Handler: topic filter change
  function handleFilterChange(topicId) {
    quizData.selectedTopicFilter = topicId;
  }

  async function handleStartQuiz(quizId) {
    try {
      ui.loading = true;
      ui.error = null;

      // Step 1: Start new quiz session
      session.summary = null;
      session.current = await postStartQuiz(quizId);

      // Step 2: Fetch first question
      session.currentQuestion = await fetchNextQuestion(session.current.id);

      // Step 3: Set timer if there's a time limit
      timer.timeLeft = session.current.time_limit_seconds || null;

      // Step 4: Navigate to quiz-taking screen
      ui.screen = "quiz-taking";
    } catch (err) {
      ui.error = err.message;
    } finally {
      ui.loading = false;
    }
  }

  // Refresh session data
  async function refreshSession(sessionId) {
    try {
      ui.loading = true;
      session.current = await getQuizSessionStats(sessionId);
    } catch (err) {
      ui.error = err.message;
    } finally {
      ui.loading = false;
    }
    return session.current;
  }

  // Handle timer expiration
  async function handleTimeExpired() {
    ui.error = "Time's up! Submitting quiz...";
    try {
      // Try to submit quiz
      const summary = await postSubmitQuiz(session.current.id);
      handleQuizComplete(summary);
    } catch (err) {
      // If postSubmitQuiz not implemented, show message
      ui.error = "Time's up! Please implement postSubmitQuiz() to auto-submit.";
    }
  }

  // Handle quiz completion
  function handleQuizComplete(summary) {
    ui.screen = "results";
    session.summary = summary;
    timer.timeLeft = null; // Stop timer
  }
</script>

<!-- Navigation [debug] -->
<div class="nav-panel">
  <strong>NAVIGATION</strong>
  <Navigation bind:appScreen={ui.screen} currentSession={session.current} sessionSummary={session.summary} onRefreshSession={refreshSession}/>
  <Timer bind:timeLeft={timer.timeLeft} onTimeExpired={handleTimeExpired}/>
</div>

<main>
  {#if ui.error}
    <div class="error">
      <strong>Error:</strong> {ui.error}
    </div>
  {/if}

  <!-- Quiz List Screen -->
  {#if ui.screen === "quiz-list"}
    <h1>Welcome to Quiz App!</h1>

    {#if ui.loading}
      <div class="loading">Loading quizzes...</div>
    {:else if quizData.topics.length > 0}
      <TopicFilter
        topics={quizData.topics}
        selectedTopicFilter={quizData.selectedTopicFilter}
        onFilterChange={handleFilterChange}
      />

      {#if filteredQuizzes.length > 0}
        <div class="quiz-list">
          {#each filteredQuizzes as quiz (quiz.id)}
            <QuizCard
              {quiz}
              topic={getTopicName(quiz.topic_id)}
              onStart={() => handleStartQuiz(quiz.id)}
              loading={ui.loading}
            />
          {/each}
        </div>
      {:else}
        <p class="no-quizzes">No quizzes available for this topic.</p>
      {/if}
    {:else}
      <p class="no-data">No topics or quizzes available.</p>
    {/if}
  {/if}

  <!-- Quiz Taking Screen -->
  {#if ui.screen === "quiz-taking" && session.current}
    <QuizTakingScreen bind:session bind:ui {getQuizNameById} {refreshSession} onQuizComplete={handleQuizComplete}/>
  {/if}

  <!-- Results Screen -->
  {#if ui.screen === "results" && session.summary}
    <ResultsScreen sessionSummary={session.summary} {getQuizNameById}/>
  {/if}
</main>

<style>
  main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  h1 {
    text-align: center;
    color: light-dark(#333, #fff);
    margin-bottom: 30px;
    padding-top: 7vh;
  }

  .error {
    padding: 12px;
    margin-bottom: 20px;
    background-color: #fee;
    border: 1px solid #fcc;
    color: #c33;
    border-radius: 4px;
  }

  .loading {
    text-align: center;
    padding: 40px;
    color: light-dark(#666, #ccc);
    font-size: 1.2rem;
  }

  .quiz-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    margin-top: 20px;
  }

  .no-quizzes,
  .no-data {
    text-align: center;
    padding: 40px;
    color: light-dark(#999, #666);
    font-size: 1.1rem;
  }

  .nav-panel {
    /* Positioning properties */
    position: fixed; /* Fixes it to the viewport */
    top: 20px; /* 20px down from the top edge */
    right: 20px; /* 20px in from the right edge */

    /* Appearance properties */
    background-color: #f9f9f9;
    border: 1px solid #ccc;
    padding: 15px;
    z-index: 1000; /* Ensures it sits above other page content */
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    width: 250px; /* Optional: Set a fixed width */

    /* Optional: Add dark mode styles for the panel itself */
    color-scheme: light dark;
    background-color: light-dark(#f9f9f9, #333);
    color: light-dark(#000, #fff);
  }
</style>
