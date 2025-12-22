<script>
  let { topics, selectedTopicFilter, onFilterChange } = $props();
</script>

{#if topics.length > 0}
  <div class="topic-filters">
    <!-- TODO: Implement "All Topics" button -->
    <!-- HINT:
      - Add onclick handler that calls onFilterChange(null)
      - Add class "active" when selectedTopicFilter === null
      - Use template: class="topic-button {condition ? 'active' : ''}"
    -->
    <button class="topic-button">
      All Topics
    </button>

    <!-- TODO: Implement topic filter buttons -->
    <!-- HINT:
      - Use {#each topics as topic (topic.id)}
      - Add onclick handler that calls onFilterChange(topic.id)
      - Add class "active" when selectedTopicFilter === topic.id
      - Display topic.name as button text
    -->
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
