<script setup lang="ts">
import { computed, reactive } from 'vue';
import type { HomeCreateRequest } from '../types/api';
import { useAppState } from '../state/useAppState';

const state = useAppState();

const form = reactive<HomeCreateRequest>({
  name: '',
  build_period: 'pre_1978',
  home_size: 'y100_200',
  residents: 'three_four',
  heating_system: 'gas',
  has_ev: true,
});

const canSubmit = computed(() => form.name.trim().length > 0 && !state.loading.profiles);

async function submit(): Promise<void> {
  if (!canSubmit.value) {
    return;
  }
  await state.createProfile({ ...form, name: form.name.trim() });
  form.name = '';
}
</script>

<template>
  <form class="configurator" aria-label="Create home profile" @submit.prevent="submit">
    <h2>Create profile</h2>
    <label>
      Profile name
      <input v-model="form.name" name="name" placeholder="Main house" />
    </label>
    <label>
      Built
      <select v-model="form.build_period" name="build_period">
        <option value="pre_1978">Before 1978</option>
        <option value="y1980_2000">1980-2000</option>
        <option value="post_2000">After 2000</option>
        <option value="in_progress">In progress</option>
      </select>
    </label>
    <label>
      Size
      <select v-model="form.home_size" name="home_size">
        <option value="under_100">Under 100 m2</option>
        <option value="y100_200">100-200 m2</option>
        <option value="over_200">Over 200 m2</option>
      </select>
    </label>
    <label>
      Residents
      <select v-model="form.residents" name="residents">
        <option value="one_two">1-2</option>
        <option value="three_four">3-4</option>
        <option value="five_plus">5+</option>
      </select>
    </label>
    <label>
      Heating
      <select v-model="form.heating_system" name="heating_system">
        <option value="gas">Gas</option>
        <option value="heat_pump">Heat pump</option>
        <option value="other_unknown">Other or unsure</option>
      </select>
    </label>
    <label class="checkbox">
      <input v-model="form.has_ev" type="checkbox" name="has_ev" />
      Owns an EV
    </label>
    <p v-if="state.errorBySource.profiles" class="error">{{ state.errorBySource.profiles }}</p>
    <button type="submit" :disabled="!canSubmit">
      {{ state.loading.profiles ? 'Creating...' : 'Create and advise' }}
    </button>
  </form>
</template>

<style scoped>
.configurator {
  display: grid;
  gap: 10px;
}

h2 {
  margin: 0;
  font-size: 15px;
}

label {
  display: grid;
  gap: 5px;
  font-size: 12px;
  color: #cae7ec;
}

input,
select {
  min-height: 34px;
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 7px;
  padding: 0 9px;
  color: #f7fbff;
  background: rgba(255, 255, 255, 0.1);
}

select option {
  color: #17252f;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
}

.checkbox input {
  width: auto;
  min-height: auto;
}

button {
  min-height: 36px;
  border: 0;
  border-radius: 7px;
  color: #083139;
  background: #67e8c9;
  font-weight: 700;
}

button:disabled {
  cursor: default;
  opacity: 0.55;
}

.error {
  margin: 0;
  color: #ffd5c8;
  font-size: 12px;
}
</style>
