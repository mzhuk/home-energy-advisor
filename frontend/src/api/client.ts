import type {
  AdviceRecord,
  ApiErrorEnvelope,
  ChatMessage,
  ChatMessageRequest,
  ChatMessageResponse,
  HomeCreateRequest,
  HomeDetail,
  HomeProfile,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1';

export class ApiClientError extends Error {
  readonly code: string;
  readonly details: Record<string, unknown>;
  readonly requestId: string;
  readonly status: number;

  constructor(status: number, envelope: ApiErrorEnvelope) {
    super(envelope.error.message);
    this.name = 'ApiClientError';
    this.status = status;
    this.code = envelope.error.code;
    this.details = envelope.error.details;
    this.requestId = envelope.error.request_id;
  }
}

export function listHomes(): Promise<HomeProfile[]> {
  return request<HomeProfile[]>('/homes');
}

export function createHome(payload: HomeCreateRequest): Promise<HomeDetail> {
  return request<HomeDetail>('/homes', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getHome(homeId: string): Promise<HomeDetail> {
  return request<HomeDetail>(`/homes/${homeId}`);
}

export function getAdvice(homeId: string): Promise<AdviceRecord> {
  return request<AdviceRecord>(`/homes/${homeId}/advice`);
}

export function generateAdvice(homeId: string): Promise<AdviceRecord> {
  return request<AdviceRecord>(`/homes/${homeId}/advice`, { method: 'POST' });
}

export function getChat(homeId: string): Promise<ChatMessage[]> {
  return request<ChatMessage[]>(`/homes/${homeId}/chat`);
}

export function sendChatMessage(
  homeId: string,
  payload: ChatMessageRequest,
): Promise<ChatMessageResponse> {
  return request<ChatMessageResponse>(`/homes/${homeId}/chat`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...init.headers,
    },
  });
  const payload = await parseJson(response);
  if (!response.ok) {
    throw toApiClientError(response.status, payload);
  }
  return payload as T;
}

async function parseJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return {};
  }
  try {
    return JSON.parse(text) as unknown;
  } catch (error) {
    throw new Error(`Expected JSON response from API, received invalid JSON. ${String(error)}`);
  }
}

function toApiClientError(status: number, payload: unknown): ApiClientError {
  if (isErrorEnvelope(payload)) {
    return new ApiClientError(status, payload);
  }
  return new ApiClientError(status, {
    error: {
      code: 'internal_error',
      message: 'The API returned an unexpected error response.',
      details: {},
      request_id: 'req_unknown',
    },
  });
}

function isErrorEnvelope(payload: unknown): payload is ApiErrorEnvelope {
  if (typeof payload !== 'object' || payload === null || !('error' in payload)) {
    return false;
  }
  const error = (payload as { error: unknown }).error;
  return typeof error === 'object' && error !== null && 'code' in error && 'message' in error;
}
