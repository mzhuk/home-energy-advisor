export type BuildPeriod = 'pre_1978' | 'y1980_2000' | 'post_2000' | 'in_progress';
export type HomeSize = 'under_100' | 'y100_200' | 'over_200';
export type Residents = 'one_two' | 'three_four' | 'five_plus';
export type HeatingSystem = 'gas' | 'heat_pump' | 'other_unknown';

export type AreaId = 'solar' | 'battery' | 'heat_pump' | 'smart_controls' | 'ev_charging';
export type ChatSource = 'global' | AreaId;
export type ChatRole = 'user' | 'assistant';
export type Priority = 'high' | 'medium' | 'low';

export type ErrorCode =
  | 'validation_error'
  | 'not_found'
  | 'advice_not_found'
  | 'llm_unavailable'
  | 'llm_auth_error'
  | 'llm_timeout'
  | 'llm_bad_response'
  | 'prompt_injection_blocked'
  | 'off_topic_blocked'
  | 'pii_scrubbed_and_failed'
  | 'internal_error';

export interface ApiErrorEnvelope {
  error: {
    code: ErrorCode;
    message: string;
    details: Record<string, unknown>;
    request_id: string;
  };
}

export interface HomeCreateRequest {
  name: string;
  build_period: BuildPeriod;
  home_size: HomeSize;
  residents: Residents;
  heating_system: HeatingSystem;
  has_ev: boolean;
}

export interface HomeProfile extends HomeCreateRequest {
  id: string;
  created_at: string;
  updated_at: string;
}

export interface HomeDetail extends HomeProfile {
  ai_context: string[];
  latest_advice: AdviceRecord | null;
}

export interface AreaAdvice {
  area_id: AreaId;
  title: string;
  priority: Priority;
  insight: string;
  first_step: string;
  default_prompt: string;
  suggested_questions: string[];
}

export interface AdviceRecord {
  id: string;
  home_id: string;
  summary: string;
  areas: AreaAdvice[];
  disclaimer: string;
  provider: string;
  used_fallback: boolean;
  created_at: string;
}

export interface ChatMessageRequest {
  message: string;
  source: ChatSource;
}

export interface ChatMessage {
  id: string;
  home_id: string;
  role: ChatRole;
  source: ChatSource;
  content: string;
  created_at: string;
}

export interface ChatMessageResponse {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
}
