import React, { useEffect, useState, useCallback } from 'react';
import './index.css';
import {
  Attachments,
  Bubble,
  Conversations,
  Prompts,
  Sender,
  Welcome,
  ThoughtChain,
  Suggestion,
} from '@ant-design/x';
import { createStyles } from 'antd-style';
import { Typography } from 'antd';

import {
  CloudUploadOutlined,
  CommentOutlined,
  EllipsisOutlined,
  FireOutlined,
  HeartOutlined,
  PaperClipOutlined,
  PlusOutlined,
  ReadOutlined,
  ShareAltOutlined,
  SmileOutlined,
  UserOutlined,
  RobotOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  ShopOutlined,
  GithubOutlined,
  BulbOutlined,
  ShoppingCartOutlined,
  CoffeeOutlined,
  HomeOutlined,
  StarOutlined,
  CalendarOutlined,
} from '@ant-design/icons';
import { Badge, Button, type GetProp, Space, message, Tooltip } from 'antd';
import { v4 as uuidv4 } from 'uuid';
import MarkdownIt from 'markdown-it';

// 配置Markdown渲染器
const md = new MarkdownIt({
  html: true,
  breaks: true,
  linkify: true,
  typographer: true
});

// 添加消息类型定义
interface LocalMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: number;
  loading?: boolean;
}

// 修改：模块信息接口
interface ModuleInfo {
  icon: React.ReactNode;
  title: string;
}

// 新增：API响应接口
interface InvoiceApiResponse {
  event: string;
  task_id: string;
  id: string;
  message_id: string;
  conversation_id: string;
  mode: string;
  answer: string;
  metadata: {
    usage: {
      prompt_tokens: number;
      total_tokens: number;
    }
  };
  created_at: number;
}

// 新增：API解析后的内容
interface InvoiceAnswerData {
  answer: string;
  node?: string;
}

// API配置
const API_URL = 'http://localhost:8000/nativeai/llm/question'; // 普通对话API URL
const DEFAULT_CONVERSATION_ID = uuidv4();

// 模拟对话历史存储
const mockConversations: Record<string, LocalMessage[]> = {
  [DEFAULT_CONVERSATION_ID]: [
    {
      id: `system-init-${DEFAULT_CONVERSATION_ID}`,
      content: '你好！我是Native，有什么我可以帮到您的？',
      isUser: false,
      timestamp: Date.now() - 3600000,
    }
  ]
};

// 会话ID映射表 - 用于将本地会话ID映射到API的session_id
const sessionIdMap: Record<string, string> = {};

// 新增：会话ID映射表
const invoiceConversationIdMap: Record<string, string> = {};

// API调用函数
const apiSendMessage = async (message: string, conversationId: string = '0') => {
  try {
    if (!mockConversations[conversationId]) {
      mockConversations[conversationId] = [];
    }
    
    const userMessage: LocalMessage = {
      id: `user-${Date.now()}`,
      content: message,
      isUser: true,
      timestamp: Date.now(),
    };
    
    const hasDuplicateMessage = mockConversations[conversationId].some(
      msg => msg.isUser && msg.content === message && Date.now() - msg.timestamp < 5000
    );
    
    if (!hasDuplicateMessage) {
      mockConversations[conversationId].push(userMessage);
    }
    
    let sessionId = sessionIdMap[conversationId];
    if (!sessionId) {
      sessionId = 'session-' + Date.now() + '-' + Math.floor(Math.random() * 1000000);
      sessionIdMap[conversationId] = sessionId;
    }

    console.log(`调用API，会话ID: ${conversationId}, SessionID: ${sessionId}`);
    
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Trace-ID': `trace-${Date.now()}`
      },
      body: JSON.stringify({
        question: message,
        session_id: sessionId,
        user_id: 'huyida-test'
      })
    });

    if (!response.ok) {
      throw new Error(`API错误: ${response.status}`);
    }

    const data = await response.json();
    console.log('API响应:', data);
    
    if (data.session_id && data.session_id !== sessionId) {
      sessionIdMap[conversationId] = data.session_id;
      console.log(`更新SessionID: ${data.session_id}`);
    }

    const systemMessage: LocalMessage = {
      id: `system-${Date.now()}`,
      content: data.reply,
      isUser: false,
      timestamp: Date.now(),
    };
    
    mockConversations[conversationId].push(systemMessage);
    
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
    
    const fallbackReply = '抱歉，我暂时无法连接到服务器。请稍后再试或检查您的网络连接。';
    
    const errorMessage: LocalMessage = {
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
const getConversationHistory = (conversationId: string = '0'): LocalMessage[] => {
  return mockConversations[conversationId] || [];
};

// 从对话历史中提取标题
const getTitleFromMessages = (messages: LocalMessage[], id: string): string => {
  const userMessages = messages.filter(msg => msg.isUser);
  return userMessages.length > 0 
    ? (userMessages[0].content.length > 20 
        ? userMessages[0].content.substring(0, 20) + '...' 
        : userMessages[0].content)
    : `Native AI ${id}`;
};

const renderTitle = (icon: React.ReactElement, title: string) => (
  <Space align="start">
    {icon}
    <span>{title}</span>
  </Space>
);

const defaultConversationsItems = [
  {
    key: DEFAULT_CONVERSATION_ID,
    label: 'Native AI',
  },
];

const useStyle = createStyles(({ token, css }) => {
  return {
    layout: css`
      width: 100%;
      min-width: 900px;
      height: 100%;
      border-radius: ${token.borderRadius}px;
      display: flex;
      background: ${token.colorBgContainer};
      font-family: AlibabaPuHuiTi, ${token.fontFamily}, sans-serif;

      .ant-prompts {
        color: ${token.colorText};
      }
    `,
    menu: css`
      background: ${token.colorBgLayout}80;
      width: 250px;
      height: 100%;
      display: flex;
      flex-direction: column;
    `,
    conversations: css`
      padding: 0 12px;
      flex: 1;
      overflow-y: auto;
    `,
    chat: css`
      height: 100%;
      width: 100%;
      max-width: 850px;
      margin: 0 auto;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      padding: ${token.paddingLG}px;
      gap: 10px;

      .ant-bubble-list {
        .ant-bubble-item {
          margin: 8px 0;
        }
        
        .ant-bubble-item-end {
          .ant-bubble-content {
            margin-right: 10px;
          }
        }
        
        .ant-bubble-item-start {
          .ant-bubble-content {
            margin-left: 10px;
          }
        }
      }
    `,
    messages: css`
      flex: 1;
    `,
    placeholder: css`
      padding-top: 32px;
    `,
    sender: css`
      box-shadow: ${token.boxShadow};
    `,
    logo: css`
      display: flex;
      height: 72px;
      align-items: center;
      justify-content: start;
      padding: 0 24px;
      box-sizing: border-box;

      img {
        width: 24px;
        height: 24px;
        display: inline-block;
      }

      span {
        display: inline-block;
        margin: 0 8px;
        font-weight: bold;
        color: ${token.colorText};
        font-size: 16px;
      }
    `,
    addBtn: css`
      background: #1677ff0f;
      border: 1px solid #1677ff34;
      width: calc(100% - 24px);
      margin: 0 12px 24px 12px;
    `,
    thoughtChain: css`
      width: 240px;
      border-left: 1px solid ${token.colorBorderSecondary};
      padding: ${token.padding}px;
      height: 100%;
      overflow-y: auto;
    `,
    moduleIcon: css`
      font-size: 20px !important;
      margin-right: 8px !important;
      color: ${token.colorPrimary} !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
    `,
    markdown: css`
      pre {
        background-color: #f6f8fa;
        padding: 12px;
        border-radius: 4px;
        overflow-x: auto;
      }
      
      code {
        font-family: monospace;
      }
      
      a {
        color: ${token.colorPrimary};
        text-decoration: none;
      }
      
      table {
        border-collapse: collapse;
        width: 100%;
        margin: 12px 0;
      }
      
      th, td {
        border: 1px solid #dfe2e5;
        padding: 6px 13px;
      }
      
      blockquote {
        margin: 0;
        padding-left: 12px;
        border-left: 4px solid #dfe2e5;
        color: #6a737d;
      }
    `,
  };
});

// Markdown渲染函数
const renderMarkdown = (content: string) => (
  <Typography>
    <div 
      dangerouslySetInnerHTML={{ __html: md.render(content) }} 
      style={{ 
        fontSize: '14px',
        lineHeight: '1.6',
        '& pre': { 
          backgroundColor: '#f6f8fa',
          padding: '12px',
          borderRadius: '4px',
          overflowX: 'auto'
        },
        '& code': {
          fontFamily: 'monospace'
        },
        '& a': {
          color: '#1890ff'
        }
      }}
    />
  </Typography>
);

// 美团相关的提示项 - 非新会话时显示
const senderPromptsItems: GetProp<typeof Prompts, 'items'> = [
  {
    key: '1',
    icon: <BulbOutlined style={{ color: '#FFD700' }} />,
    label: '附近有哪些高评分餐厅',
    description: '推荐附近评分4.8分以上的餐厅',
  },
  {
    key: '2',
    icon: <SmileOutlined style={{ color: '#52C41A' }} />,
    label: '如何使用美团红包',
    description: '如何使用美团红包',
  },
  {
    key: '3',
    icon: <BulbOutlined style={{ color: '#1890ff' }} />,
    label: '退款规则是什么',
    description: '美团订单退款的规则是什么',
  },
];

// 修改新会话时显示的默认提示项
const defaultPromptsItems: GetProp<typeof Prompts, 'items'> = [
  {
    key: '1',
    icon: <BulbOutlined style={{ color: '#1890ff' }} />,
    label: '订单分析',
  },
  {
    key: '2',
    icon: <ShoppingCartOutlined style={{ color: '#52C41A' }} />,
    label: '外卖助手',
  },
  {
    key: '3',
    icon: <HeartOutlined style={{ color: '#FF4D4F' }} />,
    label: '美食推荐',
  },
  {
    key: '4',
    icon: <CommentOutlined style={{ color: '#722ED1' }} />,
    label: '评价助手',
  },
  {
    key: '5',
    icon: <PaperClipOutlined style={{ color: '#FA8C16' }} />,
    label: '优惠券管理',
  },
];

// 欢迎页面提示项
const placeholderPromptsItems: GetProp<typeof Prompts, 'items'> = [
  {
    key: '1',
    label: renderTitle(<FireOutlined style={{ color: '#FF4D4F' }} />, '热门服务'),
    description: '您可能感兴趣的内容',
    children: [
      {
        key: '1-1',
        description: '附近有什么值得推荐的美食？',
      },
      {
        key: '1-2',
        description: '如何查询我的订单退款状态？',
      },
      {
        key: '1-3',
        description: '有什么本周末的优惠活动？',
      },
    ],
  },
  {
    key: '2',
    label: renderTitle(<ReadOutlined style={{ color: '#1890FF' }} />, '使用指南'),
    description: '如何更好地使用Native AI',
    children: [
      {
        key: '2-1',
        icon: <HeartOutlined />,
        description: `如何获得更多的红包优惠`,
      },
      {
        key: '2-2',
        icon: <SmileOutlined />,
        description: `会员积分使用技巧`,
      },
      {
        key: '2-3',
        icon: <CommentOutlined />,
        description: `如何撰写有效的商家评价`,
      },
    ],
  },
  {
    key: '3',
    label: renderTitle(<ReadOutlined style={{ color: '#52C41A' }} />, '本地生活'),
    description: '探索周边精彩生活',
    children: [
      {
        key: '3-1',
        icon: <CoffeeOutlined />,
        description: `附近有哪些高评分的咖啡店`,
      },
      {
        key: '3-2',
        icon: <BulbOutlined />,
        description: `周末亲子活动推荐`,
      },
      {
        key: '3-3',
        icon: <StarOutlined />,
        description: `人气商家排行榜`,
      },
    ],
  },
  {
    key: '4',
    label: renderTitle(<ReadOutlined style={{ color: '#722ED1' }} />, '高级功能'),
    description: '解锁更多可能性',
    children: [
      {
        key: '4-1',
        icon: <CloudUploadOutlined />,
        description: `问题订单快速解决`,
      },
      {
        key: '4-2',
        icon: <PaperClipOutlined />,
        description: `优惠券自动筛选`,
      },
      {
        key: '4-3',
        icon: <ShareAltOutlined />,
        description: `分享订单获得奖励`,
      },
    ],
  },
];

// 建议项
const suggestionItems = [
  { label: '美食推荐', value: '我想了解附近的特色美食推荐' },
  { label: '外卖配送时间', value: '外卖大约需要多久能送达' },
  { label: '如何退款', value: '我的订单需要退款，怎么操作' },
];

const Independent: React.FC = () => {
  const { styles } = useStyle();

  const [headerOpen, setHeaderOpen] = React.useState(false);
  const [content, setContent] = React.useState('');
  const [conversationsItems, setConversationsItems] = React.useState(defaultConversationsItems);
  const [activeKey, setActiveKey] = React.useState(defaultConversationsItems[0].key);
  const [attachedFiles, setAttachedFiles] = React.useState<GetProp<typeof Attachments, 'items'>>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [messages, setMessages] = React.useState<LocalMessage[]>([]);
  const [isNewConversation, setIsNewConversation] = React.useState(true);
  const [activeModule, setActiveModule] = React.useState<ModuleInfo | null>(null);
  const [showSessionAnalysisInput, setShowSessionAnalysisInput] = useState(false);
  const [sessionIdToAnalyze, setSessionIdToAnalyze] = useState('');
  const [nodeData, setNodeData] = useState<string[]>([]);

  const createNewConversation = (): string => {
    const newId = uuidv4();;
    mockConversations[newId] = [
      {
        id: `system-init-${newId}`,
        content: '您好！我是Native AI，可以帮您推荐美食、查询订单、优惠券管理等，有什么我可以帮助您的？',
        isUser: false,
        timestamp: Date.now(),
      }
    ];
    return newId;
  };

  useEffect(() => {
    const history = getConversationHistory(activeKey);
    setMessages(history);
    setIsNewConversation(history.length <= 1);
  }, []);

  useEffect(() => {
    const history = getConversationHistory(activeKey);
    setMessages(history);
    setIsNewConversation(history.length <= 1);
  }, [activeKey]);

  const onSubmit = async (nextContent: string) => {
    if (!nextContent.trim()) return;
    
    if (isLoading) return;
    
    if (isNewConversation) {
      setIsNewConversation(false);
    }

    const userMessageId = `user-${Date.now()}`;
    const userMessage: LocalMessage = {
      id: userMessageId,
      content: nextContent,
      isUser: true,
      timestamp: Date.now(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    setContent('');
    
    const loadingMessageId = `system-${Date.now()}-loading`;
    setMessages(prev => [...prev, {
      id: loadingMessageId,
      content: '',
      isUser: false,
      timestamp: Date.now(),
      loading: true,
    }]);
    
    setIsLoading(true);
    
    try {
      let response;
      
      if (activeModule) {
        switch (activeModule.title) {
          case '外卖助手':
            console.log('调用外卖专用API');
            response = await apiSendMessage(nextContent, activeKey);
            break;
          case '订单分析':
            console.log('调用订单分析API');
            response = await apiSendMessage(nextContent, activeKey);
            setShowSessionAnalysisInput(false);
            break;
          case '优惠券管理':
            console.log('调用优惠券专用API');
            response = await apiSendMessage(nextContent, activeKey);
            if (response.metadata?.node) {
              setNodeData(prev => [...prev, response.metadata.node]);
            }
            break;
          default:
            console.log('调用普通对话API');
            response = await apiSendMessage(nextContent, activeKey);
        }
      } else {
        console.log('调用普通对话API');
        response = await apiSendMessage(nextContent, activeKey);
      }
      
      console.log('API响应结果:', response);
      
      setMessages(prev => {
        const filteredMessages = prev.filter(msg => 
          msg.id !== loadingMessageId && 
          !(msg.isUser && msg.content === nextContent && Date.now() - msg.timestamp < 3000 && msg.id !== userMessageId)
        );
        
        return [...filteredMessages, {
          id: response.metadata?.message_id || `system-${Date.now()}`,
          content: response.reply,
          isUser: false,
          timestamp: Date.now(),
        }];
      });
      
      if (response.status === 'error') {
        message.error('服务器连接失败，使用了离线回复模式');
      }
      
      if (mockConversations[activeKey]) {
        const title = getTitleFromMessages(mockConversations[activeKey], activeKey);
        const updatedItems = conversationsItems.map(item => {
          if (item.key === activeKey) {
            return { ...item, label: title };
          }
          return item;
        });
        setConversationsItems(updatedItems);
      }
    } catch (error) {
      message.error('发送消息失败，请重试');
      console.error('发送消息错误:', error);
      setMessages(prev => prev.filter(msg => msg.id !== loadingMessageId));
    } finally {
      setIsLoading(false);
    }
  };

  const onPromptsItemClick: GetProp<typeof Prompts, 'onItemClick'> = (info) => {
    if (isLoading) return;
    
    console.log("点击提示项:", info);
    
    if (isNewConversation) {
      const moduleKey = info.data.key;
      console.log("查找模块的key:", moduleKey);
      
      const module = defaultPromptsItems.find(item => item.key === moduleKey);
      console.log("找到的模块:", module);
      
      if (module) {
        setActiveModule({
          icon: module.icon,
          title: module.label as string
        });
        
        if (module.label === '订单分析') {
          setIsNewConversation(false);
          setShowSessionAnalysisInput(true);
          message.info('请输入需要分析的订单号');
          
          setMessages([
            {
              id: `system-init-${Date.now()}`,
              content: '请输入您要分析的订单号或相关要求',
              isUser: false,
              timestamp: Date.now(),
            }
          ]);
        } else if (module.label === '优惠券管理') {
          setIsNewConversation(false);
          message.success('已切换到优惠券管理模式，请输入您的需求');
          
          setMessages([
            {
              id: `system-init-${Date.now()}`,
              content: '您好，我是优惠券管理助手。请问有什么可以帮助您的？',
              isUser: false,
              timestamp: Date.now(),
            }
          ]);
        } else {
          message.success(`已切换到 ${module.label} 模式`);
        }
        
        return;
      }
    }
    
    const description = info.data?.description as string;
    if (description) {
      console.log("发送提示消息:", description);
      onSubmit(description);
    }
  };

  const onAddConversation = () => {
    const newId = createNewConversation();
    const newItem = {
      key: newId,
      label: `新会话 ${newId}`,
    };
    
    setConversationsItems([...conversationsItems, newItem]);
    setActiveKey(newId);
    
    const history = getConversationHistory(newId);
    setMessages(history);
    setIsNewConversation(true);
    setContent('');
    setNodeData([]);
  };

  const onConversationClick: GetProp<typeof Conversations, 'onActiveChange'> = (key) => {
    setActiveKey(key);
    setActiveModule(null);
    setNodeData([]);
  };

  const handleFileChange: GetProp<typeof Attachments, 'onChange'> = (info) =>
    setAttachedFiles(info.fileList);

  const placeholderNode = (
    <Space direction="vertical" size={16} className={styles.placeholder}>
      <Welcome
        variant="borderless"
        icon="https://mdn.alipayobjects.com/huamei_iwk9zp/afts/img/A*s5sNRo5LjfQAAAAAAAAAAAAADgCCAQ/fmt.webp"
        title="Hello, I'm Native AI"
        description="我可以帮您推荐美食、查询订单、管理优惠券等，请告诉我您需要什么帮助？"
        extra={
          <Space>
            <Button icon={<ShareAltOutlined />}></Button>
            <Button icon={<EllipsisOutlined />}></Button>
          </Space>
        }
      />
      <Prompts
        title="您可能想要了解："
        items={placeholderPromptsItems}
        styles={{
          list: {
            width: '100%',
          },
          item: {
            flex: 1,
          },
        }}
        onItemClick={onPromptsItemClick}
      />
    </Space>
  );

  const bubbleItems = isNewConversation 
    ? [{ key: 'welcome', content: placeholderNode, variant: 'borderless' }]
    : messages
      .filter((msg, index, self) => 
        self.findIndex(m => m.id === msg.id) === index
      )
      .sort((a, b) => a.timestamp - b.timestamp)
      .map(msg => ({
        key: msg.id,
        content: msg.content,
        placement: msg.isUser ? 'end' : 'start',
        avatar: msg.isUser 
          ? { icon: <UserOutlined /> } 
          : { icon: <RobotOutlined /> },
        messageRender: !msg.isUser ? renderMarkdown : undefined,
        loading: msg.loading,
        styles: {
          content: {
            padding: '8px 12px',
            maxWidth: '85%',
          },
          message: !msg.isUser ? styles.markdown : undefined
        }
      }));

  const attachmentsNode = (
    <Badge dot={attachedFiles.length > 0 && !headerOpen}>
      <Button type="text" icon={<PaperClipOutlined />} onClick={() => setHeaderOpen(!headerOpen)} />
    </Badge>
  );

  const prefixNode = (
    <>
      {activeModule && (
        <Tooltip title={`使用功能: ${activeModule.title}`}>
          <div 
            style={{ 
              fontSize: '20px', 
              marginRight: '8px', 
              color: '#1890ff',
              display: 'inline-flex',
              alignItems: 'center'
            }}
          >
            {activeModule.icon}
          </div>
        </Tooltip>
      )}
      {attachmentsNode}
    </>
  );

  const senderHeader = (
    <Sender.Header
      title="Attachments"
      open={headerOpen}
      onOpenChange={setHeaderOpen}
      styles={{
        content: {
          padding: 0,
        },
      }}
    >
      <Attachments
        beforeUpload={() => false}
        items={attachedFiles}
        onChange={handleFileChange}
        placeholder={(type) =>
          type === 'drop'
            ? { title: 'Drop file here' }
            : {
                icon: <CloudUploadOutlined />,
                title: 'Upload files',
                description: 'Click or drag files to this area to upload',
              }
        }
      />
    </Sender.Header>
  );

  const logoNode = (
    <div className={styles.logo}>
      <img
        src="https://mdn.alipayobjects.com/huamei_iwk9zp/afts/img/A*s5sNRo5LjfQAAAAAAAAAAAAADgCCAQ/fmt.webp"
        draggable={false}
        alt="logo"
      />
      <span>Native AI</span>
    </div>
  );

  const getPlaceholderText = () => {
    if (activeModule) {
      if (activeModule.title === '订单分析' && showSessionAnalysisInput) {
        return '请输入您要分析的订单号或相关要求';
      }
      return `正在使用${activeModule.title}服务，请输入您的问题`;
    }
    return isNewConversation ? '想吃什么？去哪玩？问我吧' : '输入消息或键入 "/" 查看建议';
  };

  const getNodeThoughtChainItems = () => {
    if (nodeData.length === 0) return [];
    
    return nodeData.map((node, index) => ({
      title: `${node}`,
      status: 'success' as const,
      icon: <LoadingOutlined />,
      description: `步骤 ${index + 1}`,
    }));
  };

  return (
    <div className={styles.layout}>
      <div className={styles.menu}>
        {logoNode}
        <Button
          onClick={onAddConversation}
          type="link"
          className={styles.addBtn}
          icon={<PlusOutlined />}
        >
          新建对话
        </Button>
        <Conversations
          items={conversationsItems}
          className={styles.conversations}
          activeKey={activeKey}
          onActiveChange={onConversationClick}
        />
      </div>
      <div className={styles.chat}>
        <Bubble.List
          items={bubbleItems}
          className={styles.messages}
          styles={{
            item: {
              marginBottom: '6px',
            }
          }}
        />
        {isNewConversation ? 
          <Prompts 
            title="推荐服务："
            items={defaultPromptsItems} 
            onItemClick={onPromptsItemClick}
            styles={{
              list: {
                width: '100%',
              },
              item: {
                margin: '0 8px 8px 0',
              },
            }}
          /> : 
          <Prompts 
            items={senderPromptsItems} 
            onItemClick={onPromptsItemClick} 
          />
        }
        <Suggestion items={suggestionItems}>
          {({ onTrigger, onKeyDown, onSelect }) => (
            <Sender
              value={content}
              header={senderHeader}
              onSubmit={onSubmit}
              onChange={(nextVal) => {
                if (nextVal === '/') {
                  onTrigger();
                } else if (!nextVal) {
                  onTrigger(false);
                  if (content !== '' && !showSessionAnalysisInput) {
                    setActiveModule(null);
                  }
                }
                setContent(nextVal);
              }}
              onKeyDown={(e) => {
                onKeyDown(e);
              }}
              prefix={prefixNode}
              loading={isLoading}
              placeholder={getPlaceholderText()}
              className={styles.sender}
            />
          )}
        </Suggestion>
      </div>
      <div className={styles.thoughtChain}>
        <ThoughtChain
          items={[
            {
              title: 'Native AI',
              status: 'success',
              description: `会话ID: ${activeKey}`,
              icon: <CheckCircleOutlined />,
              content: '欢迎使用Native AI，我可以帮您寻找美食、查询订单、推荐优惠等。',
            },
            ...(activeModule ? [{
              title: `使用功能: ${activeModule.title}`,
              status: 'success',
              icon: activeModule.icon,
              description: activeModule.title === '外卖助手' ? 
                '当前使用外卖专用服务' : 
                activeModule.title === '订单分析' ?
                '当前使用订单分析服务' : 
                activeModule.title === '优惠券管理' ?
                '当前使用优惠券管理服务' : 
                '当前使用通用服务',
            }] : []),
            ...getNodeThoughtChainItems(),
            {
              title: isLoading ? '正在处理...' : '等待输入',
              status: isLoading ? 'pending' : 'success',
              description: isLoading ? '正在查询回复' : 
                (showSessionAnalysisInput ? '请输入订单号' : '准备接收新消息'),
              icon: isLoading ? <LoadingOutlined /> : <CheckCircleOutlined />,
            },
          ]}
        />
      </div>
    </div>
  );
};

export default Independent;