export interface User {
  id: string;
  username: string;
  avatar: string;
}

export interface Guild {
  id: string;
  name: string;
  icon: string | null;
  bot_present: boolean;
  permissions: string;
}

export interface SystemStats {
  guild_count: number;
  user_count: number;
  latency_ms: number;
  uptime_seconds: number;
  platform: string;
  python_version: string;
  active_music_players: number;
}

export interface GuildSettings {
  default_timeout_seconds: number;
  default_warning_limit: number;
  audit_channel_id: string | null;
  moderator_roles: string;
  protected_roles: string;
  ignored_channels: string;
  ignored_roles: string;
}

export interface WelcomeSettings {
  welcome: {
    channel_id: string | null;
    message_text: string;
    embed_json: string;
    dm_enabled: boolean;
    enabled: boolean;
  };
  goodbye: {
    channel_id: string | null;
    message_text: string;
    embed_json: string;
    enabled: boolean;
  };
}

export interface Case {
  id: number;
  type: string;
  user_id: string;
  moderator_id: string;
  reason: string;
  duration: number | null;
  status: string;
  created_at: string;
}

export interface Ticket {
  id: number;
  channel_id: string;
  creator_id: string;
  status: string;
  claimed_by: string | null;
  topic: string;
  created_at: string;
  closed_at: string | null;
}

export interface ReactionRolePanel {
  message_id: string;
  channel_id: string;
  title: string;
  description: string;
  group_name: string;
  type: string;
  roles: Array<{
    emoji: string;
    role_id: string;
    label: string;
  }>;
}

export interface Track {
  uuid: string;
  title: string;
  url: string;
  duration: number;
  thumbnail: string | null;
  provider: string;
}

export interface QueueItem {
  uuid: string;
  added_by: string;
  added_at: string;
  track: Track;
}

export interface PlaybackState {
  state: string;
  current: (QueueItem & { position?: number }) | null;
  queue: QueueItem[];
  is_connected: boolean;
  channel_id: string | null;
}

export interface AITool {
  name: string;
  description: string;
  enabled: boolean;
}

export interface AIConfig {
  providers: string[];
  current_provider: string;
  current_model: string;
  system_prompt: string;
  tools: AITool[];
}

export interface LogEntry {
  type: string;
  timestamp: number;
  level: string;
  message: string;
  logger: string;
}
