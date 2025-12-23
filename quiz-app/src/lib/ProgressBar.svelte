<script>
  let { current_q_index, question_count } = $props();
</script>

<div class="progress-bar">
  <div
    class="progress-fill"
    style={`width: ${((current_q_index + 1) / question_count) * 100}%`}
  />
</div>
<p class="progress-text">
  Question {current_q_index + 1} of {question_count}
</p>

<style>
  .progress-bar {
    width: 100%;
    height: 10px;
    background-color: #e0e0e0;
    border-radius: 5px;
    overflow: hidden;
    margin-bottom: 10px;
  }

  .progress-fill {
    height: 100%;
    background-color: #28a745;
    transition: width 0.3s ease;
  }

  .progress-text {
    text-align: center;
    margin-bottom: 20px;
    color: light-dark(#666, #aaa);
  }
</style>
