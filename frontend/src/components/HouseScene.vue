<script setup lang="ts">
import { computed } from 'vue';
import houseImageUrl from '../assets/energy-effective-house.png';
import type { AreaId, Priority } from '../types/api';
import { useAppState } from '../state/useAppState';

interface Hotspot {
  areaId: AreaId;
  label: string;
  x: number;
  y: number;
}

const state = useAppState();

const hotspots: Hotspot[] = [
  { areaId: 'solar', label: 'Solar panels', x: 50, y: 18 },
  { areaId: 'battery', label: 'Power station', x: 50, y: 63 },
  { areaId: 'heat_pump', label: 'Heat pump', x: 70, y: 63 },
  { areaId: 'smart_controls', label: 'Smart controls', x: 65, y: 86 },
  { areaId: 'ev_charging', label: 'EV charging', x: 18, y: 63 },
];

const visibleHotspots = computed(() =>
  hotspots.filter((hotspot) => hotspot.areaId !== 'ev_charging' || state.selectedHome.value?.has_ev),
);

function priorityFor(areaId: AreaId): Priority | null {
  return state.selectedAdvice.value?.areas.find((area) => area.area_id === areaId)?.priority ?? null;
}
</script>

<template>
  <div class="house-scene">
    <img :src="houseImageUrl" alt="Modern energy efficient house with solar panels" />
    <button
      v-for="hotspot in visibleHotspots"
      :key="hotspot.areaId"
      class="hotspot"
      :class="[priorityFor(hotspot.areaId), { selected: state.selectedArea.value === hotspot.areaId }]"
      type="button"
      :aria-label="hotspot.label"
      :style="{ left: `${hotspot.x}%`, top: `${hotspot.y}%` }"
      :disabled="!state.selectedHome.value || !state.selectedAdvice.value"
      @click="state.selectedArea.value = hotspot.areaId"
    >
      <span>{{ hotspot.label }}</span>
    </button>
  </div>
</template>

<style scoped>
.house-scene {
  position: relative;
  width: 900px;
  height: 600px;
  overflow: hidden;
  background: #d8efe7;
}

img {
  display: block;
  width: 900px;
  height: 600px;
  object-fit: cover;
}

.hotspot {
  position: absolute;
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  margin: -17px 0 0 -17px;
  border: 2px solid #ffffff;
  border-radius: 50%;
  background: #0f9f8f;
  box-shadow:
    0 8px 24px rgba(15, 62, 72, 0.28),
    0 0 0 6px rgba(255, 255, 255, 0.28);
}

.hotspot span {
  position: absolute;
  left: 50%;
  bottom: 42px;
  width: max-content;
  max-width: 150px;
  transform: translateX(-50%);
  border-radius: 6px;
  padding: 5px 8px;
  color: #ffffff;
  background: rgba(12, 45, 55, 0.92);
  font-size: 12px;
  pointer-events: none;
}

.hotspot.high {
  background: #ef6f4d;
}

.hotspot.medium {
  background: #f4b740;
}

.hotspot.low {
  background: #0f9f8f;
}

.hotspot.selected {
  outline: 4px solid rgba(73, 214, 184, 0.58);
}

.hotspot:disabled {
  cursor: default;
  opacity: 0.55;
}
</style>
