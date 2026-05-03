<script setup lang="ts">
import HomeConfigurator from './HomeConfigurator.vue';
import { useAppState } from '../state/useAppState';

const state = useAppState();
</script>

<template>
  <aside class="profile-sidebar" aria-label="Home profiles">
    <div class="brand">
      <p>Home Energy Advisor</p>
    </div>
    <p v-if="state.errorBySource.app" class="error">{{ state.errorBySource.app }}</p>
    <HomeConfigurator />
    <section class="profiles-section" aria-label="Saved home profiles">
      <div class="profiles-heading">
        <h2>Saved homes</h2>
        <span>{{ state.homes.value.length }}</span>
      </div>
      <div class="profile-list">
        <button
          v-for="home in state.homes.value"
          :key="home.id"
          class="profile-button"
          :class="{ selected: home.id === state.selectedHomeId.value }"
          type="button"
          @click="state.selectHome(home.id)"
        >
          <span>{{ home.name }}</span>
          <small>{{ home.has_ev ? 'EV owner' : 'No EV' }}</small>
        </button>
      </div>
    </section>
  </aside>
</template>

<style scoped>
.profile-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  padding: 18px;
  border-right: 1px solid rgba(255, 255, 255, 0.16);
  background: #103642;
  color: #f7fbff;
}

.brand p {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.profiles-section {
  display: grid;
  gap: 10px;
  margin-top: 6px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.18);
  min-height: 0;
}

.profiles-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.profiles-heading h2 {
  margin: 0;
  color: #cae7ec;
  font-size: 13px;
  font-weight: 700;
}

.profiles-heading span {
  min-width: 24px;
  border-radius: 999px;
  padding: 2px 7px;
  color: #083139;
  background: #67e8c9;
  font-size: 12px;
  font-weight: 700;
  text-align: center;
}

.profile-list {
  display: grid;
  gap: 8px;
  overflow: auto;
}

.profile-button {
  display: grid;
  gap: 4px;
  width: 100%;
  padding: 10px 12px;
  color: inherit;
  text-align: left;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.08);
}

.profile-button.selected {
  border-color: #67e8c9;
  background: rgba(103, 232, 201, 0.18);
}

.profile-button small {
  color: #b7d7df;
}

.error {
  margin: 0;
  color: #ffd5c8;
  font-size: 13px;
}
</style>
