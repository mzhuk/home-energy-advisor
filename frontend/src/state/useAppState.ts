import { computed, reactive, ref } from 'vue';
import type {
  AdviceRecord,
  AreaId,
  ChatMessage,
  ChatSource,
  HomeCreateRequest,
  HomeDetail,
  HomeProfile,
} from '../types/api';
import * as api from '../api/client';

const SELECTED_HOME_STORAGE_KEY = 'home-energy-advisor:selected-home-id';

const homes = ref<HomeProfile[]>([]);
const selectedHomeId = ref<string | null>(localStorage.getItem(SELECTED_HOME_STORAGE_KEY));
const selectedArea = ref<AreaId>('solar');
const adviceByHomeId = reactive<Record<string, AdviceRecord | undefined>>({});
const chatByHomeId = reactive<Record<string, ChatMessage[] | undefined>>({});
const draftBySource = reactive<Record<ChatSource, string>>({
  global: '',
  solar: '',
  battery: '',
  heat_pump: '',
  smart_controls: '',
  ev_charging: '',
});
const errorBySource = reactive<Partial<Record<ChatSource | 'app' | 'profiles' | 'advice', string>>>(
  {},
);
const loading = reactive({
  app: false,
  profiles: false,
  advice: false,
});
const sendingSource = ref<ChatSource | null>(null);

export function useAppState() {
  const selectedHome = computed(
    () => homes.value.find((home) => home.id === selectedHomeId.value) ?? null,
  );
  const selectedAdvice = computed(() =>
    selectedHomeId.value ? adviceByHomeId[selectedHomeId.value] ?? null : null,
  );
  const selectedChatHistory = computed(() =>
    selectedHomeId.value ? chatByHomeId[selectedHomeId.value] ?? [] : [],
  );

  async function initialize(): Promise<void> {
    loading.app = true;
    clearError('app');
    try {
      homes.value = await api.listHomes();
      selectInitialHome();
      if (selectedHomeId.value) {
        await loadSelectedHomeData();
      }
    } catch (error) {
      setError('app', error);
    } finally {
      loading.app = false;
    }
  }

  async function createProfile(payload: HomeCreateRequest): Promise<HomeDetail | null> {
    loading.profiles = true;
    clearError('profiles');
    try {
      const detail = await api.createHome(payload);
      upsertHome(detail);
      await selectHome(detail.id);
      await generateSelectedAdvice();
      return detail;
    } catch (error) {
      setError('profiles', error);
      return null;
    } finally {
      loading.profiles = false;
    }
  }

  async function selectHome(homeId: string): Promise<void> {
    selectedHomeId.value = homeId;
    localStorage.setItem(SELECTED_HOME_STORAGE_KEY, homeId);
    await loadSelectedHomeData();
  }

  async function loadSelectedHomeData(): Promise<void> {
    if (!selectedHomeId.value) {
      return;
    }
    const homeId = selectedHomeId.value;
    const [detail, chat] = await Promise.all([api.getHome(homeId), api.getChat(homeId)]);
    upsertHome(detail);
    chatByHomeId[homeId] = chat;
    if (detail.latest_advice) {
      adviceByHomeId[homeId] = detail.latest_advice;
    } else {
      await loadAdvice(homeId);
    }
    if (!detail.has_ev && selectedArea.value === 'ev_charging') {
      selectedArea.value = 'solar';
    }
  }

  async function loadAdvice(homeId: string): Promise<void> {
    clearError('advice');
    try {
      adviceByHomeId[homeId] = await api.getAdvice(homeId);
    } catch (error) {
      if (error instanceof api.ApiClientError && error.code === 'advice_not_found') {
        return;
      }
      setError('advice', error);
    }
  }

  async function generateSelectedAdvice(): Promise<void> {
    if (!selectedHomeId.value) {
      return;
    }
    loading.advice = true;
    clearError('advice');
    try {
      adviceByHomeId[selectedHomeId.value] = await api.generateAdvice(selectedHomeId.value);
    } catch (error) {
      setError('advice', error);
    } finally {
      loading.advice = false;
    }
  }

  async function sendChat(source: ChatSource, message?: string): Promise<void> {
    if (!selectedHomeId.value || sendingSource.value) {
      return;
    }
    const homeId = selectedHomeId.value;
    const content = (message ?? draftBySource[source]).trim();
    if (!content) {
      return;
    }
    const temporaryMessage: ChatMessage = {
      id: `pending_${crypto.randomUUID()}`,
      home_id: homeId,
      role: 'user',
      source,
      content,
      created_at: new Date().toISOString(),
    };
    sendingSource.value = source;
    clearError(source);
    chatByHomeId[homeId] = [...(chatByHomeId[homeId] ?? []), temporaryMessage];
    if (!message) {
      draftBySource[source] = '';
    }
    try {
      const response = await api.sendChatMessage(homeId, { source, message: content });
      const history = chatByHomeId[homeId] ?? [];
      chatByHomeId[homeId] = [
        ...history.filter((chatMessage) => chatMessage.id !== temporaryMessage.id),
        response.user_message,
        response.assistant_message,
      ];
    } catch (error) {
      setError(source, error);
      try {
        chatByHomeId[homeId] = await api.getChat(homeId);
      } catch {
        chatByHomeId[homeId] = (chatByHomeId[homeId] ?? []).filter(
          (chatMessage) => chatMessage.id !== temporaryMessage.id,
        );
      }
    } finally {
      sendingSource.value = null;
    }
  }

  return {
    homes,
    selectedHomeId,
    selectedHome,
    selectedArea,
    selectedAdvice,
    selectedChatHistory,
    adviceByHomeId,
    chatByHomeId,
    draftBySource,
    sendingSource,
    errorBySource,
    loading,
    initialize,
    createProfile,
    selectHome,
    generateSelectedAdvice,
    sendChat,
  };
}

function selectInitialHome(): void {
  if (selectedHomeId.value && homes.value.some((home) => home.id === selectedHomeId.value)) {
    return;
  }
  selectedHomeId.value = homes.value[0]?.id ?? null;
  if (selectedHomeId.value) {
    localStorage.setItem(SELECTED_HOME_STORAGE_KEY, selectedHomeId.value);
  } else {
    localStorage.removeItem(SELECTED_HOME_STORAGE_KEY);
  }
}

function upsertHome(home: HomeProfile): void {
  const index = homes.value.findIndex((existing) => existing.id === home.id);
  if (index === -1) {
    homes.value = [home, ...homes.value];
    return;
  }
  homes.value = homes.value.map((existing) => (existing.id === home.id ? home : existing));
}

function clearError(key: ChatSource | 'app' | 'profiles' | 'advice'): void {
  delete errorBySource[key];
}

function setError(key: ChatSource | 'app' | 'profiles' | 'advice', error: unknown): void {
  errorBySource[key] = error instanceof Error ? error.message : 'Something went wrong.';
}
