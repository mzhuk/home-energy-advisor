<script setup lang="ts">
import { computed } from 'vue';
import type { ChatSource } from '../types/api';
import { useAppState } from '../state/useAppState';

interface FormattedLine {
  key: string;
  bullet: boolean;
  parts: FormattedPart[];
}

interface FormattedPart {
  key: string;
  text: string;
  bold: boolean;
}

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

function formatMessage(content: string): FormattedLine[] {
  return normalizeAdvisorText(content)
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line && line !== '-' && line !== '*')
    .map((line, lineIndex) => {
      const bullet = /^[-*]\s+/.test(line);
      const text = bullet ? line.slice(2).trim() : line;
      return {
        key: `${lineIndex}-${text}`,
        bullet,
        parts: formatInlineParts(text, lineIndex),
      };
    });
}

function normalizeAdvisorText(content: string): string {
  return content
    .replace(/^\s*[-*]\s*$/gm, '')
    .replace(/\s+\*\s+(?=\S)/g, '\n- ')
    .replace(/\s+(?=\*\*(?:Priority|First Step|Next Step|Why|Assumption|Recommendation)\b)/g, '\n\n')
    .replace(/\s+(?=\*(?:Priority|First Step|Next Step|Why|Assumption|Recommendation):\*)/g, '\n\n')
    .replace(/\s+(?=\*\*[A-Z][^*]{2,80}\*\*)/g, '\n\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function formatInlineParts(text: string, lineIndex: number): FormattedPart[] {
  return text
    .split(/(\*\*[^*]+\*\*|\*[^*\n]+\*)/g)
    .filter(Boolean)
    .map((part, partIndex) => {
      const bold =
        (part.startsWith('**') && part.endsWith('**')) ||
        (part.startsWith('*') && part.endsWith('*'));
      return {
        key: `${lineIndex}-${partIndex}`,
        text: stripEmphasis(part, bold),
        bold,
      };
    });
}

function stripEmphasis(part: string, bold: boolean): string {
  if (!bold) {
    return part;
  }
  if (part.startsWith('**') && part.endsWith('**')) {
    return part.slice(2, -2);
  }
  return part.slice(1, -1);
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
        <div class="message-body">
          <p
            v-for="line in formatMessage(message.content)"
            :key="line.key"
            :class="{ bullet: line.bullet }"
          >
            <template v-for="part in line.parts" :key="part.key">
              <strong v-if="part.bold" class="inline-strong">{{ part.text }}</strong>
              <span v-else>{{ part.text }}</span>
            </template>
          </p>
        </div>
      </article>
      <div v-if="state.sendingSource.value === source" class="waiting" role="status">
        <span aria-hidden="true"></span>
        Waiting for advisor response
      </div>
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

.message-body {
  display: grid;
  gap: 6px;
}

.message-body p,
.error {
  font-size: 13px;
  line-height: 1.35;
}

.message-body .bullet {
  position: relative;
  padding-left: 14px;
}

.message-body .bullet::before {
  position: absolute;
  left: 2px;
  content: "•";
}

.inline-strong {
  display: inline;
  margin: 0;
  font-size: inherit;
}

.error {
  color: #bd432d;
}

.waiting {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #5d7580;
  font-size: 13px;
}

.waiting span {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(15, 159, 143, 0.24);
  border-top-color: #0f9f8f;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
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
