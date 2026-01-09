/**
 * WebSocket 相关类型定义
 */

export interface WebSocketMessage {
  type: 'thought' | 'answer' | 'status' | 'complete' | 'error' | 'agent_start' | 'agent_end' | 'system';
  content?: string;
  is_complete?: boolean;
  data?: any;
}

export type ConnectionStatus = 'disconnected' | 'connecting' | 'idle' | 'processing';

