export interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: number;
  loading?: boolean;
}

export interface ChatResponse {
  reply: string;
  status: 'success' | 'error';
  metadata?: Record<string, any>;
}

export interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: number;
}
