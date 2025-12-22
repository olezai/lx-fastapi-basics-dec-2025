<script>
  import { onMount } from "svelte";
  import TopicFilter from "./lib/TopicFilter.svelte";
  import QuizCard from "./lib/QuizCard.svelte";
  import { fetchQuizzesData } from "./lib/utils.js";

  // Reactive state
  let loading = $state(false);
  let error = $state(null);
  let quizzes = $state([]);
  let topics = $state([]);
  let selectedTopicFilter = $state(null);

  // Fetch data on component mount
  onMount(async () => {
    try {
      loading = true;
      error = null;
      const data = await fetchQuizzesData();
      quizzes = data.quizzes;
      topics = data.topics;
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });

  // Derived value: filtered quizzes based on selected topic
  let filteredQuizzes = $derived(
    selectedTopicFilter === null
      ? quizzes
      : quizzes.filter((q) => q.topic_id === selectedTopicFilter)
  );

  // Helper function to get topic name by ID
  function getTopicName(topicId) {
    return topics.find((t) => t.id === topicId)?.name || "Unknown";
  }

  // Handler for topic filter changes
  function handleFilterChange(topicId) {
    selectedTopicFilter = topicId;
  }
</script>

<main>
  <h1>Welcome to Quiz App!</h1>

  {#if error}
    <div class="error">
      <strong>Error:</strong> {error}
    </div>
  {/if}

  {#if loading}
    <div class="loading">Loading quizzes...</div>
  {:else if topics.length > 0}
    <!-- Topic Filter Component -->
    <TopicFilter
      {topics}
      {selectedTopicFilter}
      onFilterChange={handleFilterChange}
    />

    <!-- Quiz List -->
    {#if filteredQuizzes.length > 0}
      <div class="quiz-list">
        {#each filteredQuizzes as quiz (quiz.id)}
          <QuizCard {quiz} topic={getTopicName(quiz.topic_id)} />
        {/each}
      </div>
    {:else}
      <p class="no-quizzes">No quizzes available for this topic.</p>
    {/if}
  {:else}
    <p class="no-data">No topics or quizzes available.</p>
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
</style>
