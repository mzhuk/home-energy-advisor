<script setup lang="ts">
import { onMounted } from 'vue';
import AdvicePanel from './components/AdvicePanel.vue';
import ChatPanel from './components/ChatPanel.vue';
import HouseScene from './components/HouseScene.vue';
import ProfileSidebar from './components/ProfileSidebar.vue';
import { useAppState } from './state/useAppState';

const state = useAppState();

onMounted(() => {
  void state.initialize();
});
</script>

<template>
  <main class="app-frame" aria-label="Home Energy Advisor">
    <ProfileSidebar class="sidebar" />
    <section class="scene-region" aria-label="House energy scene">
      <HouseScene />
    </section>
    <aside class="right-panel" aria-label="Selected advice and focused chat">
      <AdvicePanel />
    </aside>
    <section class="bottom-panel" aria-label="Global advisor chat">
      <ChatPanel source="global" title="Home Energy Advisor" />
    </section>
  </main>
</template>
