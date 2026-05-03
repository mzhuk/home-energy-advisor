<script setup lang="ts">
import { computed } from 'vue';
import ChatPanel from './ChatPanel.vue';
import { useAppState } from '../state/useAppState';

const state = useAppState();

const selectedAreaAdvice = computed(() =>
  state.selectedAdvice.value?.areas.find((area) => area.area_id === state.selectedArea.value) ?? null,
);

const focusedChatTitle = computed(() =>
  selectedAreaAdvice.value ? `Focused chat on ${selectedAreaAdvice.value.title}` : 'Focused chat',
);
</script>

<template>
  <section class="advice-panel">
    <header>
      <p>Home profile</p>
      <h2 v-if="selectedAreaAdvice">{{ selectedAreaAdvice.title }}</h2>
    </header>
    <p v-if="state.errorBySource.advice" class="error">{{ state.errorBySource.advice }}</p>
    <button
      v-if="state.selectedHome.value && !state.selectedAdvice.value"
      class="generate"
      type="button"
      :disabled="state.loading.advice"
      @click="state.generateSelectedAdvice"
    >
      {{ state.loading.advice ? 'Creating advice for your new home profile...' : 'Generate advice' }}
    </button>
    <template v-if="selectedAreaAdvice">
      <span class="priority">{{ selectedAreaAdvice.priority }} priority</span>
      <p>{{ selectedAreaAdvice.insight }}</p>
      <strong>{{ selectedAreaAdvice.first_step }}</strong>
      <div class="questions">
        <button
          v-for="question in selectedAreaAdvice.suggested_questions"
          :key="question"
          type="button"
          @click="state.sendChat(selectedAreaAdvice.area_id, question)"
        >
          {{ question }}
        </button>
      </div>
      <p class="disclaimer">{{ state.selectedAdvice.value?.disclaimer }}</p>
    </template>
    <ChatPanel v-if="selectedAreaAdvice" :source="selectedAreaAdvice.area_id" :title="focusedChatTitle" />
  </section>
</template>

<style scoped>
.advice-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  padding: 16px;
  overflow: hidden;
}

header p,
h2 {
  margin: 0;
}

header p {
  color: #5d7580;
  font-size: 12px;
}

h2 {
  margin-top: 3px;
  font-size: 18px;
}

.priority {
  align-self: flex-start;
  border-radius: 6px;
  padding: 4px 8px;
  color: #083139;
  background: #d7faf1;
  font-size: 12px;
  font-weight: 700;
}

p,
strong {
  margin: 0;
  font-size: 13px;
  line-height: 1.35;
}

button {
  min-height: 32px;
  border: 1px solid rgba(20, 69, 83, 0.16);
  border-radius: 7px;
  background: #f9fcff;
}

.generate {
  background: #67e8c9;
  font-size: 12px;
  font-weight: 700;
}

.questions {
  display: grid;
  gap: 6px;
}

.questions button {
  padding: 7px;
  text-align: left;
}

.disclaimer,
.error {
  color: #5d7580;
  font-size: 12px;
}

.error {
  color: #bd432d;
}

.advice-panel :deep(.chat-panel) {
  flex: 1;
  min-height: 260px;
}
</style>
