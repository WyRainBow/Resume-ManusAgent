import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Loader2, Terminal, FileText, ChevronDown, ChevronUp, X, Eye, Sparkles, Brain, Zap, CheckCircle2, AlertCircle, Wrench, Search, Edit, BarChart, MessageSquare, Trash2, StopCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import HTMLTemplateRenderer from './components/HTMLTemplateRenderer';
import logger from './utils/logger';

// 空简历模板 - 用户会通过 AI 加载具体简历
const EMPTY_RESUME = {
  id: '',
  title: '我的简历',
  basic: {
    name: '',
    title: '',
    email: '',
    phone: '',
    location: '',
    employementStatus: ''
  },
  education: [],
  experience: [],
  projects: [],
  openSource: [],
  awards: [],
  skillContent: '',
  customData: {},
  menuSections: [
    { id: 'basic', title: '基本信息', icon: '', enabled: true, order: 0 },
    { id: 'skills', title: '专业技能', icon: '', enabled: true, order: 1 },
    { id: 'experience', title: '工作经历', icon: '', enabled: true, order: 2 },
    { id: 'projects', title: '项目经历', icon: '', enabled: true, order: 3 },
    { id: 'openSource', title: '开源经历', icon: '', enabled: true, order: 4 },
    { id: 'awards', title: '荣誉奖项', icon: '', enabled: true, order: 5 },
    { id: 'education', title: '教育经历', icon: '', enabled: true, order: 6 },
  ],
  draggingProjectId: null,
  globalSettings: {},
  activeSection: 'basic'
};

// WebSocket 配置
const WS_CONFIG = {
  PORT: 8080,
  PATH: '/ws',
  getUrl: () => `ws://localhost:${WS_CONFIG.PORT}${WS_CONFIG.PATH}`
};

// localStorage keys
const STORAGE_KEYS = {
  MESSAGES: 'openmanus_chat_messages',
  RESUME_DATA: 'openmanus_resume_data',
  SHOW_RESUME_PANEL: 'openmanus_show_resume_panel'
};

// 从 localStorage 加载消息历史
const loadMessagesFromStorage = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.MESSAGES);
    if (stored) {
      const parsed = JSON.parse(stored);
      console.log(`📜 恢复 ${parsed.length} 条历史消息`);
      return parsed;
    }
  } catch (e) {
    console.error('Failed to load messages from storage:', e);
  }
  return [];
};

// 检查是否是旧的示例数据（需要清除缓存）
const isOldSampleData = (data) => {
  if (!data || !data.basic) return false;
  // 检查是否包含旧的示例数据标记
  return (
    data.basic.name === '张三' ||
    data.basic.email === 'zhangsan@example.com' ||
    data.basic.email === 'zhang.san@example.com'
  );
};

// 从 localStorage 加载简历数据
const loadResumeDataFromStorage = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.RESUME_DATA);
    if (stored) {
      const data = JSON.parse(stored);
      // 如果是旧的示例数据，清除缓存并返回空简历
      if (isOldSampleData(data)) {
        console.log('🧹 检测到旧的示例数据，清除缓存');
        localStorage.removeItem(STORAGE_KEYS.RESUME_DATA);
        return EMPTY_RESUME;
      }
      return data;
    }
  } catch (e) {
    console.error('Failed to load resume data from storage:', e);
  }
  return EMPTY_RESUME;
};

// 保存消息到 localStorage
const saveMessagesToStorage = (messages) => {
  try {
    // 只保存最近的 100 条消息，避免存储溢出
    const toSave = messages.slice(-100);
    localStorage.setItem(STORAGE_KEYS.MESSAGES, JSON.stringify(toSave));
  } catch (e) {
    console.error('Failed to save messages to storage:', e);
  }
};

// 保存简历数据到 localStorage
const saveResumeDataToStorage = (data) => {
  try {
    localStorage.setItem(STORAGE_KEYS.RESUME_DATA, JSON.stringify(data));
  } catch (e) {
    console.error('Failed to save resume data to storage:', e);
  }
};

function App() {
  const [input, setInput] = useState('');
  // 从 localStorage 恢复消息历史
  const [messages, setMessages] = useState(() => loadMessagesFromStorage());
  const [status, setStatus] = useState('idle'); // idle, connecting, processing
  const [ws, setWs] = useState(null);
  const wsRef = useRef(null); // 使用 ref 保存 WebSocket 引用，避免闭包问题
  const messagesEndRef = useRef(null);
  const [showResumePanel, setShowResumePanel] = useState(false);
  // 从 localStorage 恢复简历数据
  const [resumeData, setResumeData] = useState(() => loadResumeDataFromStorage());
  const [showThinkingProcess, setShowThinkingProcess] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [showSessions, setShowSessions] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);

  // 监听 messages 变化，自动保存到 localStorage
  useEffect(() => {
    saveMessagesToStorage(messages);
  }, [messages]);

  // 监听 resumeData 变化，自动保存到 localStorage
  useEffect(() => {
    saveResumeDataToStorage(resumeData);
  }, [resumeData]);

  useEffect(() => {
    // 自动连接 WebSocket
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // 从输入中提取简历路径
  const extractResumePath = (input) => {
    // 匹配多种格式，保留开头的 /
    // - "简历/路径" 或 "简历 路径"
    // - "我的简历/路径"
    // - "加载我的简历/路径"
    // - 以 .md 或 .txt 结尾的路径
    const patterns = [
      /简历(?:[\/\s]+)(\/[^\s]+\.(?:md|txt|MD|TXT))/,  // 简历//路径.md
      /(?:加载|导入|上传)(?:我的)?简历[\/\s]+(\/[^\s]+\.(?:md|txt|MD|TXT))/,  // 加载我的简历//路径.md
      /(\/[^\s]+\.(?:md|txt))/  // 任何 /path/to/file.md 或 /path/to/file.txt
    ];

    for (const pattern of patterns) {
      const match = input.match(pattern);
      if (match) {
        return match[1];
      }
    }
    return null;
  };

  const connectWebSocket = () => {
    // 🔴 后端端口配置
    const wsUrl = WS_CONFIG.getUrl();

    console.log("Connecting to", wsUrl);
    setStatus('connecting');
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('Connected to WebSocket');
      setStatus('idle');
      setWs(socket); // 连接成功时设置 ws
      wsRef.current = socket; // 同时保存到 ref

      // 连接成功后，发送历史消息给后端（用于恢复上下文）
      const storedMessages = loadMessagesFromStorage();
      if (storedMessages.length > 0) {
        // 只发送用户和助手的对话消息，过滤掉工具调用等
        const conversationMessages = storedMessages.filter(msg =>
          msg.role === 'user' || (msg.role === 'agent' && msg.type === 'answer')
        );

        if (conversationMessages.length > 0) {
          console.log(`📜 发送 ${conversationMessages.length} 条历史消息到后端`);
          socket.send(JSON.stringify({
            type: 'restore_history',
            messages: conversationMessages.map(msg => ({
              role: msg.role === 'user' ? 'user' : 'assistant',
              content: msg.content || ''
            }))
          }));
        }
      }
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (e) {
        console.error('Failed to parse message:', e, event.data);
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setStatus('disconnected');
    };

    socket.onclose = () => {
      console.log('Disconnected');
      setStatus('disconnected');
      setWs(null); // 清除 ws 引用
      wsRef.current = null; // 清除 ref 引用
      // 尝试重连
      setTimeout(connectWebSocket, 3000);
    };
  };

  const handleMessage = (data) => {
    // 记录所有 WebSocket 消息到日志
    logger.wsMessage(data.type, data.content || data);

    setMessages(prev => {
      const newMessages = [...prev];
      const lastMsg = newMessages[newMessages.length - 1];

      // 如果是步骤更新
      if (data.type === 'step') {
        // 显示步骤信息
        logger.debug(`步骤更新: ${data.content}`);
        return [...newMessages, {
          role: 'system',
          type: 'step',
          content: data.content,
          step: data.step
        }];
      }

      // 如果是思考过程 (thought)
      if (data.type === 'thought') {
        logger.debug(`思考过程: ${data.content.substring(0, 100)}...`);
        if (lastMsg && lastMsg.role === 'agent' && lastMsg.type === 'thought') {
          // 追加到上一条思考消息
          lastMsg.content += data.content;
          return [...newMessages];
        } else {
          return [...newMessages, { role: 'agent', type: 'thought', content: data.content }];
        }
      }

      // 如果是工具调用 - 检测是否是 CV 相关工具
      if (data.type === 'tool_call') {
        // 如果是加载简历或分析简历的工具，自动显示简历面板
        if (data.tool === 'load_resume_data' || data.tool === 'cv_reader_agent' || data.tool === 'cv_editor_agent') {
          setShowResumePanel(true);
        }
        return [...newMessages, {
          role: 'agent',
          type: 'tool_call',
          tool: data.tool,
          args: data.args
        }];
      }

      // 如果是工具结果
      if (data.type === 'tool_result') {
        const toolResultMsg = {
          role: 'system',
          type: 'tool_result',
          tool: data.tool,
          content: data.result
        };

        // 如果是 CV 相关工具执行成功，刷新简历数据
        const isCVTool = data.tool === 'cv_editor_agent' || data.tool === 'load_resume_data' || data.tool === 'cv_reader_agent';
        if (isCVTool && data.result && (
          data.result.includes('✅') ||
          data.result.includes('Successfully loaded') ||
          data.result.includes('Candidate:') ||
          data.result.includes('姓名') ||
          data.result.includes('电话') ||
          data.result.includes('##')
        )) {
          // 给后端一点时间处理数据
          setTimeout(() => refreshResumeData(), 300);
        }

        return [...newMessages, toolResultMsg];
      }

      // 如果是状态更新（包括停止）
      if (data.type === 'status') {
        if (data.content === 'stopped') {
          setStatus('idle');
          setShowThinkingProcess(false);
        } else if (data.content === 'processing') {
          setStatus('processing');
        }
        return newMessages;
      }

      // 如果是最终答案
      if (data.type === 'answer') {
        setStatus('idle');
        setShowThinkingProcess(false); // 思考完成，自动收起
        return [...newMessages, { role: 'agent', type: 'answer', content: data.content }];
      }

      // 错误信息
      if (data.type === 'error') {
        setStatus('idle');
        return [...newMessages, { role: 'system', type: 'error', content: data.content }];
      }

      return newMessages;
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || status === 'processing') return;

    // 记录用户操作
    logger.userAction('提交消息', { input: input.trim() });

    // 添加用户消息
    setMessages(prev => [...prev, { role: 'user', content: input }]);

    // 发送请求 - 使用 ref 获取最新的 WebSocket 引用
    const currentWs = wsRef.current || ws;
    if (currentWs && currentWs.readyState === WebSocket.OPEN) {
      const resumePath = extractResumePath(input.trim());
      const message = resumePath
        ? { prompt: input.trim(), resume_path: resumePath }
        : { prompt: input.trim() };
      currentWs.send(JSON.stringify(message));
      setStatus('processing');
      setInput('');
    } else {
      logger.error('WebSocket not connected, current state:', currentWs?.readyState);
      // 尝试重新连接
      console.log('尝试重新连接 WebSocket...');
      connectWebSocket();
      // 等待连接后再发送（延迟发送）
      setTimeout(() => {
        const newWs = wsRef.current;
        if (newWs && newWs.readyState === WebSocket.OPEN) {
          const resumePath = extractResumePath(input.trim());
          const message = resumePath
            ? { prompt: input.trim(), resume_path: resumePath }
            : { prompt: input.trim() };
          newWs.send(JSON.stringify(message));
          setStatus('processing');
          setInput('');
        } else {
          // 如果还是连接不上，显示错误消息
          setMessages(prev => [...prev, {
            role: 'agent',
            type: 'error',
            content: `⚠️ 无法连接到服务器，请检查后端服务是否运行（端口 ${WS_CONFIG.PORT}）。正在尝试重连...`
          }]);
        }
      }, 2000);
    }
  };

  // 停止 AI 执行
  const handleStop = () => {
    const currentWs = wsRef.current || ws;
    if (currentWs && currentWs.readyState === WebSocket.OPEN) {
      logger.userAction('停止执行', {});
      currentWs.send(JSON.stringify({ type: 'stop' }));
      setStatus('idle');
    }
  };

  const refreshResumeData = async () => {
    // 从后端获取最新的简历数据
    try {
      const response = await fetch('/api/resume');
      const data = await response.json();
      if (data.data && Object.keys(data.data).length > 0) {
        setResumeData(data.data);
      }
    } catch (error) {
      console.error('Failed to refresh resume data:', error);
    }
  };

  // 清除聊天历史
  const clearHistory = () => {
    // 直接清除，避免 confirm 弹窗阻塞自动化测试
    setMessages([]);
    localStorage.removeItem(STORAGE_KEYS.MESSAGES);
    console.log('🧹 已清除聊天历史');

    // 通知后端清除 Agent 状态
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'clear_history'
      }));
      console.log('🧹 已通知后端清除 Agent 状态');
    }
  };

  // 清除所有缓存（包括消息和简历数据）
  const clearAllCache = () => {
    if (window.confirm('确定要清除所有缓存数据吗？这将删除聊天历史和简历数据。')) {
      // 清除所有 localStorage 数据
      Object.values(STORAGE_KEYS).forEach(key => {
        localStorage.removeItem(key);
      });

      // 重置状态
      setMessages([]);
      setResumeData(EMPTY_RESUME);

      // 通知后端清除 Agent 状态
      const currentWs = wsRef.current || ws;
      if (currentWs && currentWs.readyState === WebSocket.OPEN) {
        currentWs.send(JSON.stringify({
          type: 'clear_history'
        }));
      }

      console.log('🧹 已清除所有缓存数据');
      alert('✅ 所有缓存已清除');
    }
  };

  const fetchSessions = async () => {
    setLoadingSessions(true);
    try {
      const resp = await fetch('/api/history/sessions/list');
      const data = await resp.json();
      setSessions(data.sessions || []);
    } catch (e) {
      console.error('Failed to load sessions:', e);
    } finally {
      setLoadingSessions(false);
    }
  };

  const loadSession = async (sessionId) => {
    try {
      const resp = await fetch(`/api/history/sessions/${sessionId}`);
      const data = await resp.json();
      const loaded = (data.messages || []).map((m) => ({
        role: m.role,
        content: m.content,
        type: m.role === 'assistant' ? 'answer' : 'user',
      }));
      setMessages(loaded);
      setCurrentSessionId(sessionId);
      saveMessagesToStorage(loaded);
      // 恢复上下文到后端
      const currentWs = wsRef.current || ws;
      if (currentWs && currentWs.readyState === WebSocket.OPEN) {
        currentWs.send(JSON.stringify({
          type: 'restore_history',
          messages: loaded.map(msg => ({
            role: msg.role === 'user' ? 'user' : 'assistant',
            content: msg.content || ''
          }))
        }));
      }
    } catch (e) {
      console.error('Failed to load session:', e);
    }
  };

  useEffect(() => {
    if (showSessions) {
      fetchSessions();
    }
  }, [showSessions]);

  return (
    <div className="flex h-screen bg-gray-50 text-gray-900 font-sans">
      {/* 主聊天区域 */}
      <div className={`flex flex-col h-full bg-white shadow-xl overflow-hidden transition-all duration-300 ${showResumePanel ? 'w-1/2' : 'w-full max-w-5xl mx-auto'
        }`}>

        {/* Header with Navigation */}
        <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white transition-all duration-300 ${status === 'processing' ? 'bg-gradient-to-br from-violet-500 to-purple-600 shadow-lg shadow-violet-200' : 'bg-indigo-600'
              }`}>
              {status === 'processing' ? (
                <Brain size={20} className="animate-pulse" />
              ) : (
                <Bot size={24} />
              )}
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">AI 简历助手</h1>
              <div className="flex items-center gap-2 text-xs">
                <span className={`w-2 h-2 rounded-full ${status === 'disconnected' ? 'bg-red-500' :
                  status === 'processing' ? 'bg-violet-500 animate-pulse' : 'bg-green-500'
                  }`}></span>
                <span className="text-gray-500">
                  {status === 'processing' ? '正在思考中...' : (status === 'disconnected' ? '未连接' : '✅ 就绪')}
                </span>
                {/* WebSocket 端口信息 */}
                <span className="text-gray-400 ml-2 font-mono">
                  WS: {WS_CONFIG.PORT}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSessions(!showSessions)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all text-sm border ${
                showSessions
                  ? 'bg-indigo-100 text-indigo-700 border-indigo-200'
                  : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border-indigo-100'
              }`}
              title="历史会话"
            >
              <MessageSquare size={16} />
              <span className="hidden sm:inline">历史会话</span>
            </button>
            {messages.length > 0 && (
              <>
                <button
                  onClick={clearHistory}
                  className="flex items-center gap-2 px-4 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-all text-sm border border-red-200"
                  title="清除聊天历史"
                >
                  <Trash2 size={16} />
                  <span className="hidden sm:inline">清除历史</span>
                </button>
                <button
                  onClick={clearAllCache}
                  className="flex items-center gap-2 px-3 py-2 bg-orange-50 text-orange-700 rounded-lg hover:bg-orange-100 transition-all text-sm border border-orange-200"
                  title="清除所有缓存（包括消息和简历数据）"
                >
                  <Wrench size={16} />
                  <span className="hidden sm:inline">清除缓存</span>
                </button>
              </>
            )}
            <button
              onClick={() => setShowResumePanel(!showResumePanel)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors text-sm ${showResumePanel
                ? 'bg-indigo-100 text-indigo-700'
                : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'
                }`}
            >
              <Eye size={16} />
              <span>简历预览</span>
            </button>
          </div>
        </header>

        {/* Messages Area */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50">
          {showSessions && (
            <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="text-sm font-semibold text-gray-700">历史会话</div>
                <button
                  onClick={fetchSessions}
                  className="text-xs text-indigo-600 hover:text-indigo-800"
                >
                  刷新
                </button>
              </div>
              {loadingSessions ? (
                <div className="text-xs text-gray-500">加载中...</div>
              ) : sessions.length === 0 ? (
                <div className="text-xs text-gray-500">暂无历史会话</div>
              ) : (
                <div className="space-y-2">
                  {sessions.map((s) => (
                    <button
                      key={s.session_id}
                      onClick={() => loadSession(s.session_id)}
                      className={`w-full text-left p-2 rounded border text-xs ${
                        currentSessionId === s.session_id
                          ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                          : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{s.title || s.session_id}</span>
                        <span className="text-gray-400">{s.message_count || 0} 条</span>
                      </div>
                      <div className="text-gray-400 mt-1">{s.updated_at || s.created_at}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <Bot size={64} className="mb-4 opacity-20" />
              <p className="text-lg">您的 AI 简历助手</p>
              <p className="text-sm text-gray-400 mt-2">告诉我您的信息，帮您生成专业简历</p>
              <div className="mt-6 text-sm text-gray-400">
                <p>试试说：</p>
                <ul className="mt-2 space-y-1">
                  <li
                    className="cursor-pointer hover:text-indigo-500 underline"
                    onClick={() => setInput('帮我加载简历模板')}
                  >帮我加载简历模板</li>
                  <li
                    className="cursor-pointer hover:text-indigo-500 underline"
                    onClick={() => setInput('我叫韦宇，是一名前端工程师')}
                  >我叫韦宇，是一名前端工程师</li>
                  <li
                    className="cursor-pointer hover:text-indigo-500 underline"
                    onClick={() => setInput('把我的邮箱改成 weiyu@example.com')}
                  >把我的邮箱改成 weiyu@example.com</li>
                  <li
                    className="cursor-pointer hover:text-indigo-500 underline"
                    onClick={() => setInput('帮我添加一段工作经历：在字节跳动做前端开发')}
                  >帮我添加一段工作经历</li>
                </ul>
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <MessageItem key={idx} message={msg} />
          ))}

          {status === 'processing' && (
            <div className="flex gap-3 my-4">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-md">
                <Brain size={16} className="text-white animate-pulse" />
              </div>
              <div className="flex-1 bg-gradient-to-br from-violet-50/50 to-purple-50/50 border border-violet-100 rounded-2xl rounded-tl-none shadow-sm">
                <div
                  className="p-4 cursor-pointer"
                  onClick={() => setShowThinkingProcess(!showThinkingProcess)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex gap-1">
                        <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                        <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                        <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                      </div>
                      <span className="text-violet-700 text-sm font-medium">AI 正在思考中</span>
                      <Sparkles size={14} className="text-violet-500 animate-pulse" />
                    </div>
                    <div className={`transition-transform duration-200 ${showThinkingProcess ? 'rotate-180' : ''}`}>
                      <ChevronDown size={16} className="text-violet-500 opacity-60" />
                    </div>
                  </div>
                </div>
                {showThinkingProcess && (
                  <div className="px-4 pb-4 border-t border-violet-100 pt-3">
                    {messages.filter(msg => msg.type === 'thought').length > 0 ? (
                      <div className="space-y-2 max-h-64 overflow-y-auto">
                        {messages
                          .filter(msg => msg.type === 'thought')
                          .map((thought, idx) => (
                            <div key={idx} className="text-xs text-violet-600 bg-white/50 p-2 rounded border border-violet-100">
                              <ReactMarkdown className="prose prose-xs max-w-none text-violet-700">
                                {thought.content}
                              </ReactMarkdown>
                            </div>
                          ))}
                      </div>
                    ) : (
                      <div className="text-xs text-violet-500 italic">
                        思考过程将在这里显示...
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </main>

        {/* Input Area */}
        <footer className="bg-white border-t border-gray-200 p-4">
          <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="告诉我您的信息，帮您生成简历...（例如：帮我分析教育经历）"
              className="w-full pl-4 pr-12 py-3 bg-gray-100 border-0 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all resize-none min-h-[56px] max-h-32"
              rows="1"
              disabled={status === 'processing'}
            />
            {status === 'processing' ? (
              <button
                type="button"
                onClick={handleStop}
                className="absolute right-3 bottom-3 p-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
                title="停止执行"
              >
                <StopCircle size={18} />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className="absolute right-3 bottom-3 p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send size={18} />
              </button>
            )}
          </form>
          <div className="text-center text-xs text-gray-400 mt-2">
            OpenManus may produce inaccurate information.
          </div>
        </footer>
      </div>

      {/* 简历预览面板 */}
      {showResumePanel && (
        <div className="w-1/2 border-l border-gray-200 bg-gray-100 flex flex-col overflow-hidden">
          <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between flex-shrink-0">
            <div>
              <h2 className="font-semibold text-gray-800">简历预览</h2>
              <p className="text-xs text-gray-500">{resumeData.basic?.name || '未命名'} - {resumeData.basic?.title || '无职位'}</p>
            </div>
            <button
              onClick={() => setShowResumePanel(false)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X size={18} className="text-gray-500" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-6 bg-gray-100">
            <div className="bg-white rounded-lg shadow-sm p-8 max-w-full mx-auto">
              <HTMLTemplateRenderer resumeData={resumeData} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// 消息组件
const MessageItem = ({ message }) => {
  const isUser = message.role === 'user';
  const [isExpanded, setIsExpanded] = useState(false);

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="bg-gradient-to-br from-indigo-600 to-indigo-700 text-white px-5 py-3 rounded-2xl rounded-tr-none max-w-[80%] shadow-md">
          {message.content}
        </div>
      </div>
    );
  }

  // 步骤信息展示 - 更现代化的设计
  if (message.type === 'step') {
    return (
      <div className="flex justify-center my-3">
        <div className="inline-flex items-center gap-2 bg-gradient-to-r from-violet-50 to-indigo-50 border border-violet-200 rounded-full px-4 py-2 text-sm text-violet-700 shadow-sm">
          <Sparkles size={14} className="animate-pulse" />
          <span className="font-medium">步骤 {message.step}</span>
          <span className="text-violet-400">·</span>
          <span>{message.content}</span>
        </div>
      </div>
    );
  }

  // 工具调用展示 - 增强版 + tool_call_id 显示
  if (message.type === 'tool_call') {
    const isCVTool = message.tool === 'load_resume_data' || message.tool === 'cv_reader_agent' || message.tool === 'cv_editor_agent';

    // 工具图标映射
    const toolIconComponents = {
      'load_resume_data': null, // 不显示图标
      'cv_reader_agent': null, // 不显示图标
      'cv_editor_agent': Edit,
      'create_chat_completion': MessageSquare,
    };

    const toolColors = {
      'load_resume_data': 'from-emerald-50 to-teal-50 border-emerald-200 text-emerald-700 bg-emerald-50/50',
      'cv_reader_agent': 'from-blue-50 to-cyan-50 border-blue-200 text-blue-700 bg-blue-50/50',
      'cv_editor_agent': 'from-violet-50 to-purple-50 border-violet-200 text-violet-700 bg-violet-50/50',
    };

    const colorClass = toolColors[message.tool] || 'from-gray-50 to-slate-50 border-gray-200 text-gray-700 bg-gray-50/50';
    const IconComponent = toolIconComponents[message.tool];

    return (
      <div className="flex justify-start ml-10 my-2">
        <div className={`bg-gradient-to-r ${colorClass} border rounded-xl p-3.5 max-w-[90%] w-full shadow-sm transition-all duration-200 hover:shadow-md hover:scale-[1.01]`}>
          <div
            className="flex items-center justify-between cursor-pointer"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            <div className="flex items-center gap-3">
              {IconComponent ? (
                <div className={`p-1.5 rounded-lg ${message.tool === 'cv_editor_agent' ? 'bg-violet-100' :
                  'bg-gray-100'}`}>
                  <IconComponent size={16} className={message.tool === 'cv_editor_agent' ? 'text-violet-600' :
                    'text-gray-600'} />
                </div>
              ) : null}
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm">调用工具</span>
                <span className="font-mono text-xs bg-white/70 px-2 py-1 rounded-md border border-white/50">{message.tool}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* ✅ 显示 tool_call_id */}
              {message.tool_call_id && (
                <span className="text-xs text-gray-500 font-mono bg-white/50 px-2 py-1 rounded-md">
                  ID: {message.tool_call_id.slice(0, 12)}...
                </span>
              )}
              <div className={`transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}>
                <ChevronDown size={16} className="opacity-60" />
              </div>
            </div>
          </div>

          {isExpanded && (
            <div className="mt-3 bg-gray-900 text-gray-100 p-4 rounded-lg text-xs font-mono overflow-x-auto shadow-inner border border-gray-800">
              <div className="flex items-center gap-2 text-gray-400 mb-2 pb-2 border-b border-gray-700">
                <Terminal size={12} />
                <span>参数</span>
                {message.tool_call_id && (
                  <span className="ml-auto text-xs text-gray-500">
                    tool_call_id: <span className="text-green-400">{message.tool_call_id}</span>
                  </span>
                )}
              </div>
              <pre className="text-green-400">{typeof message.args === 'string'
                ? (message.args.startsWith('{') || message.args.startsWith('[')
                  ? JSON.stringify(JSON.parse(message.args), null, 2)
                  : message.args)
                : JSON.stringify(message.args, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    );
  }

  // 工具结果展示 - 增强版 + tool_call_id 显示 + 上下文保存状态
  if (message.type === 'tool_result') {
    const isCVTool = message.tool === 'load_resume_data' || message.tool === 'cv_reader_agent' || message.tool === 'cv_editor_agent';
    const isSuccess = message.content && (message.content.includes('✅') || message.content.includes('Successfully') || message.content.includes('成功'));

    // ✅ 判断是否是分析工具结果（需要保存到上下文）
    const isAnalysisTool = message.tool === 'education_analyzer' || message.tool === 'cv_analyzer_agent';
    const contextSaved = isAnalysisTool;  // 分析工具的结果会保存到上下文

    // 如果是成功状态，显示简洁的成功通知卡片（参考文档中的深色成功通知样式）
    if (isSuccess) {
      const successText = message.tool === 'cv_reader_agent' || message.content.includes('读取') || message.content.includes('load') ? '读取简历内容执行成功' :
        message.tool === 'cv_analyzer_agent' || message.tool === 'education_analyzer' || message.content.includes('分析') || message.content.includes('analyze') ? '分析简历执行成功' :
          message.tool === 'cv_editor_agent' || message.content.includes('编辑') || message.content.includes('edit') ? '修改简历执行成功' :
            '执行成功';

      return (
        <div className="flex flex-col justify-start ml-10 my-2">
          <div className="bg-gray-800 rounded-xl px-4 py-3 flex items-center gap-3 shadow-lg max-w-[90%] cursor-pointer hover:bg-gray-700 transition-colors"
            onClick={() => setIsExpanded(!isExpanded)}>
            <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0">
              <CheckCircle2 size={14} className="text-white" />
            </div>
            <span className="text-white text-sm font-medium flex-1">{successText}</span>
            <div className="flex items-center gap-2">
              {/* ✅ 显示 tool_call_id */}
              {message.tool_call_id && (
                <span className="text-xs text-gray-400 font-mono bg-gray-700 px-2 py-1 rounded-md">
                  ID: {message.tool_call_id.slice(0, 8)}...
                </span>
              )}
              {/* ✅ 显示上下文保存状态 */}
              {contextSaved && (
                <span className="text-xs text-emerald-400 bg-emerald-900/50 px-2 py-1 rounded-md flex items-center gap-1">
                  <CheckCircle2 size={10} />
                  已保存上下文
                </span>
              )}
              <div className={`transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}>
                <ChevronDown size={16} className="text-gray-400" />
              </div>
            </div>
          </div>
          {isExpanded && (
            <div className="mt-2 bg-white border border-gray-200 p-3 rounded-lg text-xs font-mono overflow-x-auto max-h-64 overflow-y-auto shadow-inner max-w-[90%]">
              <div className="flex items-center justify-between mb-2 pb-2 border-b border-gray-100">
                <span className="text-gray-500">执行结果</span>
                {message.tool_call_id && (
                  <span className="text-xs text-gray-400">tool_call_id: {message.tool_call_id}</span>
                )}
              </div>
              <pre className="text-gray-600 whitespace-pre-wrap">{message.content}</pre>
            </div>
          )}
        </div>
      );
    }

    // 工具图标映射
    const toolIconComponents = {
      'load_resume_data': null, // 不显示图标
      'cv_reader_agent': null, // 不显示图标
      'cv_editor_agent': Edit,
    };

    const IconComponent = toolIconComponents[message.tool];

    return (
      <div className="flex justify-start ml-10 my-2">
        <div className={`${isSuccess ? 'bg-green-50 border-green-200' : 'bg-blue-50 border-blue-200'} border rounded-xl p-3.5 max-w-[90%] w-full shadow-sm transition-all duration-200 hover:shadow-md hover:scale-[1.01]`}>
          <div
            className="flex items-center justify-between cursor-pointer"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            <div className="flex items-center gap-3">
              {isSuccess ? (
                <div className="p-1.5 rounded-lg bg-green-100">
                  <CheckCircle2 size={16} className="text-green-600" />
                </div>
              ) : IconComponent ? (
                <div className="p-1.5 rounded-lg bg-blue-100">
                  <IconComponent size={16} className="text-blue-600" />
                </div>
              ) : null}
              <div className="flex items-center gap-2">
                <span className={`font-medium text-sm ${isSuccess ? 'text-green-700' : 'text-blue-700'}`}>
                  {isSuccess ? '执行成功' : '执行结果'}
                </span>
                <span className="font-mono text-xs bg-white/70 px-2 py-1 rounded-md border border-white/50">{message.tool}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* ✅ 显示 tool_call_id */}
              {message.tool_call_id && (
                <span className="text-xs text-gray-500 font-mono bg-white/50 px-2 py-1 rounded-md">
                  ID: {message.tool_call_id.slice(0, 8)}...
                </span>
              )}
              {/* ✅ 显示上下文保存状态 */}
              {contextSaved && (
                <span className="text-xs text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md flex items-center gap-1">
                  <CheckCircle2 size={10} />
                  已保存
                </span>
              )}
              <div className={`transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}>
                <ChevronDown size={16} className="opacity-60" />
              </div>
            </div>
          </div>

          {isExpanded && (
            <div className={`mt-3 bg-white border ${isSuccess ? 'border-green-100' : 'border-blue-100'} p-3 rounded-lg text-xs font-mono overflow-x-auto max-h-64 overflow-y-auto shadow-inner`}>
              <div className="flex items-center justify-between mb-2 pb-2 border-b border-gray-100">
                <span className="text-gray-500">执行结果</span>
                <div className="flex items-center gap-2">
                  {message.tool_call_id && (
                    <span className="text-xs text-gray-400">tool_call_id: {message.tool_call_id}</span>
                  )}
                  {contextSaved && (
                    <span className="text-xs text-emerald-600">💾 保存到 ChatHistory</span>
                  )}
                </div>
              </div>
              <pre className={isSuccess ? 'text-green-700' : 'text-gray-600 whitespace-pre-wrap'}>{message.content}</pre>
            </div>
          )}
        </div>
      </div>
    );
  }

  // 思考过程 - 全新设计，参考 Claude/Cursor，默认收起，可点击展开
  if (message.type === 'thought') {
    return (
      <div className="flex gap-3 my-3">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-md">
          <Brain size={16} className="text-white" />
        </div>
        <div className="flex-1 bg-gradient-to-br from-violet-50/50 to-purple-50/50 border border-violet-100 rounded-2xl rounded-tl-none shadow-sm">
          <div
            className="p-4 cursor-pointer"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-violet-700">
                <Sparkles size={14} className="text-violet-500" />
                <span className="text-xs font-semibold uppercase tracking-wide text-violet-500">思考过程</span>
              </div>
              <div className={`transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}>
                <ChevronDown size={16} className="text-violet-500 opacity-60" />
              </div>
            </div>
          </div>
          {isExpanded && (
            <div className="px-4 pb-4 border-t border-violet-100 pt-3">
              <ReactMarkdown className="prose prose-sm max-w-none text-gray-700">
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    );
  }

  // 最终答案 - 参考优秀设计的小字体+清晰层次
  return (
    <div className="flex gap-3 my-4">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-md">
        <Bot size={16} className="text-white" />
      </div>
      <div className="flex-1 bg-gray-50 border border-gray-200 p-4 rounded-2xl rounded-tl-none shadow-md">
        <ReactMarkdown
          className="prose max-w-none
            prose-headings:text-gray-900 prose-headings:font-bold prose-headings:mt-3 prose-headings:mb-2
            prose-h1:text-base prose-h2:text-sm prose-h3:text-xs
            prose-p:text-gray-700 prose-p:leading-relaxed prose-p:mb-2 prose-p:text-xs
            prose-strong:text-gray-900 prose-strong:font-semibold
            prose-ul:list-disc prose-ul:ml-3 prose-ul:mb-2 prose-ul:text-xs prose-ul:space-y-0.5
            prose-ol:list-decimal prose-ol:ml-3 prose-ol:mb-2 prose-ol:text-xs prose-ol:space-y-0.5
            prose-li:text-gray-700 prose-li:mb-1
            prose-code:text-xs prose-code:bg-gray-200 prose-code:px-1 prose-code:py-0.5 prose-code:rounded
            prose-blockquote:border-l-4 prose-blockquote:border-gray-300 prose-blockquote:pl-3 prose-blockquote:italic prose-blockquote:text-xs
            prose-a:text-indigo-600 prose-a:underline hover:prose-a:text-indigo-800"
          components={{
            // 自定义占位符样式（如 summary, keywords 等）
            p: ({ node, children, ...props }) => {
              const text = String(children);
              if (text.includes('summary') || text.includes('keywords') || text.match(/^[a-z_]+$/)) {
                return (
                  <div className="bg-gray-100 border border-gray-300 rounded px-3 py-2 my-2 inline-block">
                    <code className="text-gray-600 text-sm">{text}</code>
                  </div>
                );
              }
              return <p {...props}>{children}</p>;
            }
          }}
        >
          {message.content}
        </ReactMarkdown>
      </div>
    </div>
  );
};

export default App;
