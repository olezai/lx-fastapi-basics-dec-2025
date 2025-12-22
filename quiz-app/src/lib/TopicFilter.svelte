<script>
  let { topics, selectedTopicFilter, onFilterChange } = $props();
</script>

{#if topics.length > 0}
  <div class="topic-filters">
    <!-- All Topics button -->
    <button
      class="topic-button {selectedTopicFilter === null ? 'active' : ''}"
      onclick={() => onFilterChange(null)}
    >
      All Topics
    </button>

    <!-- Topic filter buttons -->
    {#each topics as topic (topic.id)}
      <button
        class="topic-button {selectedTopicFilter === topic.id ? 'active' : ''}"
        onclick={() => onFilterChange(topic.id)}
      >
        {topic.name}
      </button>
    {/each}
  </div>
{/if}

<style>
  .topic-filters {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 20px;
    align-items: center;
    min-height: 40px;
  }

  .topic-button {
    padding: 8px 16px;
    border: 2px solid #ddd;
    border-radius: 4px;
    background-color: light-dark(#fff, #2a2a2a);
    color: light-dark(#333, #fff);
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s;
  }

  .topic-button:hover {
    border-color: #646cff;
  }

  .topic-button.active {
    background-color: #646cff;
    color: white;
    border-color: #646cff;
  }
</style>
