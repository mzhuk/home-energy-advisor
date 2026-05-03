<script setup lang="ts">
import { computed } from 'vue';
import type { ChatSource } from '../types/api';
import { useAppState } from '../state/useAppState';

const props = defineProps<{
  source: ChatSource;
  title: string;
}>();

const state = useAppState();

const messages = computed(() =>
  state.selectedChatHistory.value.filter((message) => message.source === props.source),
);

function submit(): void {
  void state.sendChat(props.source);
}
</script>

<template>
  <section class="chat-panel" :aria-label="title">
    <header>
      <h2>{{ title }}</h2>
    </header>
    <div class="messages" aria-live="polite">
      <article v-for="message in messages" :key="message.id" :class="message.role">
        <strong>{{ message.role === 'user' ? 'You' : 'Advisor' }}</strong>
        <p>{{ message.content }}</p>
      </article>
    </div>
    <p v-if="state.errorBySource[source]" class="error">{{ state.errorBySource[source] }}</p>
    <form @submit.prevent="submit">
      <textarea
        v-model="state.draftBySource[source]"
        :placeholder="source === 'global' ? 'Ask about your home energy setup' : 'Ask about this system'"
        :disabled="!state.selectedHome.value || state.sendingSource.value === source"
        rows="2"
      />
      <button
        type="submit"
        :disabled="!state.selectedHome.value || state.sendingSource.value === source"
      >
        {{ state.sendingSource.value === source ? 'Sending...' : 'Send' }}
      </button>
    </form>
  </section>
</template>

<style scoped>
.chat-panel {
  display: grid;
  grid-template-rows: auto minmax(0, max-content) auto auto 1fr;
  gap: 8px;
  min-height: 0;
  height: 100%;
}

header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

h2,
p {
  margin: 0;
}

h2 {
  font-size: 15px;
}

.messages {
  display: grid;
  align-content: start;
  gap: 8px;
  max-height: 260px;
  min-height: 0;
  overflow: auto;
}

article {
  border-radius: 8px;
  padding: 8px;
  background: #edf8fb;
}

article.user {
  background: #e2fbf4;
}

article strong {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
}

article p,
.error {
  font-size: 13px;
  line-height: 1.35;
}

.error {
  color: #bd432d;
}

form {
  display: grid;
  grid-template-columns: 1fr 88px;
  gap: 8px;
}

textarea {
  resize: none;
  min-height: 48px;
  border: 1px solid rgba(20, 69, 83, 0.18);
  border-radius: 7px;
  padding: 8px;
}

button {
  border: 0;
  border-radius: 7px;
  color: #083139;
  background: #67e8c9;
  font-weight: 700;
}

button:disabled,
textarea:disabled {
  cursor: default;
  opacity: 0.55;
}
</style>
