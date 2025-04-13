import { ChatResponse, Message } from './types';

// 真实API URL
const API_URL = 'http://localhost:8000/nativeai/agents/ship/chat';
// API Token
const API_TOKEN = 'app-3MjlCFdfgK9Cw5eIlEjAdFyv';

// 模拟对话历史存储 - 仍然保留本地历史记录功能
const mockConversations: Record<string, Message[]> = {
  '1': [
    {
      id: 'system-init-1',
      content: '你好！我是Native AI, 请问有什么我可以帮助您的？',
      isUser: false,
      timestamp: Date.now() - 3600000,
    }
  ]
};

// 会话ID映射表 - 用于将本地会话ID映射到API的session_id
const sessionIdMap: Record<string, string> = {};

// 发送消息到聊天API
export const sendMessage = async (message: string, conversationId: string = '1'): Promise<ChatResponse> => {
  try {
    // 确保对话存在于本地存储
    if (!mockConversations[conversationId]) {
      mockConversations[conversationId] = [];
    }
    
    // 添加用户消息到本地对话历史
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      content: message,
      isUser: true,
      timestamp: Date.now(),
    };
    
    mockConversations[conversationId].push(userMessage);
    
    // 获取或创建API的session_id
    let sessionId = sessionIdMap[conversationId];
    if (!sessionId) {
      // 如果是新会话，可以生成一个UUID作为session_id
      // 这里使用简单方法模拟UUID生成
      sessionId = 'session-' + Date.now() + '-' + Math.floor(Math.random() * 1000000);
      sessionIdMap[conversationId] = sessionId;
    }

    // 调用真实API
    console.log(`调用API，会话ID: ${conversationId}, SessionID: ${sessionId}`);
    
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_TOKEN}`,
        'Trace-ID': `trace-${Date.now()}` // 生成随机Trace-ID
      },
      body: JSON.stringify({
        content: message,
        session_id: sessionId,
        user_id: 'huyida-test'  // 可以从应用状态或用户输入获取
      })
    });

    if (!response.ok) {
      throw new Error(`API错误: ${response.status}`);
    }

    const data = await response.json();
    console.log('API响应:', data);
    
    // 如果API返回了新的session_id，更新映射
    if (data.session_id && data.session_id !== sessionId) {
      sessionIdMap[conversationId] = data.session_id;
      console.log(`更新SessionID: ${data.session_id}`);
    }

    // 添加API回复到本地对话历史
    const systemMessage: Message = {
      id: `system-${Date.now()}`,
      content: data.reply,
      isUser: false,
      timestamp: Date.now(),
    };
    
    mockConversations[conversationId].push(systemMessage);
    
    // 返回API响应
    return {
      reply: data.reply,
      status: 'success',
      metadata: {
        conversation_id: conversationId,
        session_id: data.session_id,
        message_id: systemMessage.id,
      }
    };
  } catch (error) {
    console.error('API调用失败:', error);
    
    // 使用备用回复机制 - 当API不可用时回退到模拟回复
    const fallbackReply = '抱歉，我暂时无法连接到服务器。请稍后再试或检查您的网络连接。';
    
    // 添加错误回复到本地对话历史
    const errorMessage: Message = {
      id: `system-error-${Date.now()}`,
      content: fallbackReply,
      isUser: false,
      timestamp: Date.now(),
    };
    
    mockConversations[conversationId].push(errorMessage);
    
    return {
      reply: fallbackReply,
      status: 'error',
      metadata: {
        error_code: 'API_CONNECTION_ERROR',
        conversation_id: conversationId,
        error_message: error instanceof Error ? error.message : String(error)
      }
    };
  }
};

// 获取指定会话的历史消息
export const getConversationHistory = (conversationId: string = '1'): Message[] => {
  return mockConversations[conversationId] || [];
};

// 创建新会话
export const createNewConversation = (): string => {
  const newId = `${Date.now()}`;
  mockConversations[newId] = [
    {
      id: `system-init-${newId}`,
      content: '您好！我是Native AI, 请问有什么我可以帮助您的？',
      isUser: false,
      timestamp: Date.now(),
    }
  ];
  return newId;
};

// 获取所有会话列表
export const getAllConversations = (): Array<{id: string, title: string, lastMessage: string, timestamp: number}> => {
  return Object.entries(mockConversations).map(([id, messages]) => {
    const lastMessage = messages[messages.length - 1];
    // 从用户消息中提取标题，如果消息太长则截断
    const userMessages = messages.filter(msg => msg.isUser);
    const title = userMessages.length > 0 
      ? (userMessages[0].content.length > 20 
          ? userMessages[0].content.substring(0, 20) + '...' 
          : userMessages[0].content)
      : `火车票用户咨询 ${id.substring(id.length - 4)}`;
      
    return {
      id,
      title,
      lastMessage: lastMessage.content.substring(0, 30) + (lastMessage.content.length > 30 ? '...' : ''),
      timestamp: lastMessage.timestamp
    };
  }).sort((a, b) => b.timestamp - a.timestamp); // 按时间倒序排列
};

// 删除会话
export const deleteConversation = (conversationId: string): boolean => {
  if (mockConversations[conversationId]) {
    delete mockConversations[conversationId];
    return true;
  }
  return false;
};
