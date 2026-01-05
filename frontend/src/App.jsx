import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, Brain, Zap, AlertCircle, History, X, Clock, RotateCcw } from 'lucide-react';
import MarkdownRenderer from './components/MarkdownRenderer';
import logger from './utils/logger';

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState('idle'); // idle, connecting, processing
  const [ws, setWs] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [checkpointHistory, setCheckpointHistory] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // 自动连接 WebSocket
    connectWebSocket();
    return () => {
      if (ws) ws.close();
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // 在开发模式下，Vite 会代理 /ws 到后端
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    console.log("Connecting to", wsUrl);
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('Connected to WebSocket');
      setStatus('idle');
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
      // 尝试重连
      setTimeout(connectWebSocket, 3000);
    };

    setWs(socket);
  };

  // 获取历史对话
  const fetchHistory = async () => {
    try {
      // 获取对话历史
      const chatRes = await fetch('/api/history/chat');
      if (chatRes.ok) {
        const chatData = await chatRes.json();
        setChatHistory(chatData.messages || []);
      }

      // 获取 Checkpoint 历史
      const checkpointRes = await fetch('/api/history/checkpoints');
      if (checkpointRes.ok) {
        const checkpointData = await checkpointRes.json();
        setCheckpointHistory(checkpointData.checkpoints || []);
      }
    } catch (error) {
      console.error('Failed to fetch history:', error);
    }
  };

  const handleMessage = (data) => {
    // 记录所有 WebSocket 消息到日志
    logger.wsMessage(data.type, data.content || data);

    setMessages(prev => {
      const newMessages = [...prev];

      // 只显示 Manus 的思考过程、工具调用和最终报告
      // 不显示工具返回的原始数据、步骤信息、上下文信息

      if (data.type === 'step') {
        setStatus('processing');
        return newMessages; // 不显示步骤信息
      }

      if (data.type === 'context') {
        return newMessages; // 不显示上下文信息
      }

      if (data.type === 'thought') {
        // 显示 Manus 的思考过程
          return [...newMessages, { role: 'agent', type: 'thought', content: data.content }];
      }

      if (data.type === 'tool_call') {
        // 显示工具调用和参数
        let argsDisplay = '';
        if (data.args) {
          try {
            const argsObj = typeof data.args === 'string' ? JSON.parse(data.args) : data.args;
            argsDisplay = `\n参数: ${JSON.stringify(argsObj, null, 2)}`;
          } catch (e) {
            argsDisplay = `\n参数: ${data.args}`;
          }
        }
        const toolInfo = `🔧 调用工具: ${data.tool}${argsDisplay}`;
        return [...newMessages, { role: 'agent', type: 'tool_call', content: toolInfo, tool: data.tool }];
      }

      if (data.type === 'tool_result') {
        // 不显示工具返回的原始数据，只记录到日志
        logger.debug(`工具结果: ${data.tool} (已隐藏详细内容)`);
        return newMessages; // 不显示工具结果
      }

      if (data.type === 'answer') {
        setStatus('idle');
        // 显示最终报告
        return [...newMessages, { role: 'agent', type: 'answer', content: data.content }];
      }

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

    // 检测是否是问候消息
    const isGreeting = /^(你好|您好|hi|hello|嗨)$/i.test(input.trim());

    // 添加用户消息
    setMessages(prev => [...prev, { role: 'user', content: input }]);

    // 如果是问候，立即返回markdown欢迎消息
    if (isGreeting) {
      setMessages(prev => [...prev, {
        role: 'agent',
        type: 'greeting',
        content: `# 👋 你好：我是 OpenManus

很高兴为您服务！我可以帮您：

## ✨ 我的能力

- 📊 **分析简历** - 深入分析简历质量和问题
- ✏️ **优化简历** - 改进内容和格式、提升竞争力
- 💡 **求职建议** - 提供专业的求职指导
- 🎨 **格式美化** - 优化简历结构和排版

## 🚀 如何开始

1. **加载简历** - 请先上传或输入您的简历数据
2. **分析问题** - 告诉我 “分析一下我的简历“”
3. **开始优化** - 跟随我的建议逐步优化

请告诉我您的需求：让我们开始吧！ 😊`
      }]);
      setInput('');
      return;
    }

    // 发送请求
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ prompt: input }));
      setStatus('processing');
      setInput('');
    } else {
      console.error('WebSocket not connected');
    }
  };


  return (
    <div className="flex h-screen bg-gray-50 text-gray-900 font-sans">
      {/* 历史侧边栏 */}
      {showHistory && (
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="font-semibold text-gray-800 flex items-center gap-2">
              <Clock size={18} />
              历史记录
            </h2>
            <button
              onClick={() => setShowHistory(false)}
              className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X size={18} className="text-gray-500" />
            </button>
          </div>

          {/* Checkpoint 历史 */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-4">
              <h3 className="text-xs font-semibold text-gray-500 uppercase mb-3">简历版本历史</h3>
              {checkpointHistory.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-4">暂无版本记录</p>
              ) : (
                <div className="space-y-2">
                  {checkpointHistory.map((cp) => (
                    <div key={cp.version} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-indigo-600">版本 {cp.version}</span>
                        <span className="text-xs text-gray-400">{new Date(cp.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <div className="text-xs text-gray-600">{cp.action}</div>
                      <div className="text-xs text-gray-400 mt-1">Agent: {cp.agent}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 对话历史 */}
            <div className="p-4 border-t border-gray-200">
              <h3 className="text-xs font-semibold text-gray-500 uppercase mb-3">对话历史</h3>
              {chatHistory.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-4">暂无对话记录</p>
              ) : (
                <div className="space-y-2">
                  {chatHistory.slice(-10).map((msg, idx) => (
                    <div key={idx} className={`text-sm p-2 rounded ${msg.role === 'user' ? 'bg-indigo-50 text-indigo-700' : 'bg-gray-50 text-gray-600'}`}>
                      <div className="font-medium text-xs mb-1">{msg.role === 'user' ? '👤 用户' : '🤖 AI'}</div>
                      <div className="truncate">{msg.content}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 主聊天区域 */}
      <div className="flex flex-col h-full bg-white shadow-xl overflow-hidden w-full max-w-5xl mx-auto">

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
              </div>
            </div>
          </div>

          {/* 历史按钮 */}
          <button
            onClick={() => {
              setShowHistory(!showHistory);
              if (!showHistory) fetchHistory();
            }}
            className={`p-2 rounded-lg transition-colors ${showHistory ? 'bg-indigo-100 text-indigo-600' : 'hover:bg-gray-100 text-gray-600'}`}
            title="历史记录"
          >
            <History size={20} />
          </button>
        </header>

        {/* Messages Area */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50">
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
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-md">
                <Bot size={16} className="text-white animate-pulse" />
              </div>
              <div className="flex-1 flex items-center">
                  <div className="flex gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                </div>
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
                // 支持 Tab 键一键补全
                if (e.key === 'Tab' && !input.trim()) {
                  e.preventDefault();
                  setInput('介绍我的简历');
                }
              }}
              placeholder="介绍我的简历"
              className="w-full pl-4 pr-12 py-3 bg-gray-100 border-0 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all resize-none min-h-[56px] max-h-32"
              rows="1"
            />
            {!input.trim() && (
              <button
                type="button"
                onClick={() => setInput('介绍我的简历')}
                className="absolute right-14 bottom-3 px-3 py-2 text-xs text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 rounded-lg transition-colors"
                title="按 Tab 键或点击快速填充"
              >
                一键补全
              </button>
            )}
            <button
              type="submit"
              disabled={!input.trim() || status === 'processing'}
              className="absolute right-3 bottom-3 p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={18} />
            </button>
          </form>
          <div className="text-center text-xs text-gray-400 mt-2">
            OpenManus may produce inaccurate information.
          </div>
        </footer>
      </div>
    </div>
  );
}

// 消息组件 - 只显示 Manus 的思考、工具调用和最终报告
const MessageItem = ({ message }) => {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="bg-indigo-600 text-white px-4 py-2 rounded-lg max-w-[80%]">
          {message.content}
        </div>
      </div>
    );
  }

  // 只显示思考过程、工具调用和最终报告
  if (message.type === 'thought') {
    // 思考过程 - 用灰色背景显示
    return (
      <div className="flex gap-3 mb-2">
        <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center flex-shrink-0">
          <Brain size={14} className="text-gray-600" />
        </div>
        <div className="flex-1">
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs text-gray-600">
            <div className="font-semibold text-gray-500 mb-1">💭 Manus 思考中...</div>
            <div className="whitespace-pre-wrap">{message.content}</div>
          </div>
        </div>
      </div>
    );
  }

  if (message.type === 'tool_call') {
    // 工具调用 - 用蓝色背景显示
    return (
      <div className="flex gap-3 mb-2">
        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
          <Zap size={14} className="text-blue-600" />
              </div>
        <div className="flex-1">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs">
            <pre className="whitespace-pre-wrap font-mono text-gray-700 overflow-x-auto">
              {message.content}
            </pre>
          </div>
        </div>
      </div>
    );
  }

  if (message.type === 'greeting' || message.type === 'answer') {
    // 最终报告 - 用白色背景，支持 Markdown
    return (
      <div className="flex gap-3 mb-4">
        <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center flex-shrink-0">
          <Bot size={16} className="text-white" />
              </div>
        <div className="flex-1">
          <div className="bg-white border border-gray-200 rounded-lg p-4 text-sm">
            <div style={{ '--tw-prose-links': '#4f46e5' }}>
              <MarkdownRenderer
                content={message.content}
                size="sm"
                variant={message.type === 'greeting' ? 'greeting' : 'compact'}
              />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (message.type === 'error') {
    // 错误信息
    return (
      <div className="flex gap-3 mb-4">
        <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
          <AlertCircle size={16} className="text-red-600" />
        </div>
        <div className="flex-1">
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
            {message.content}
          </div>
        </div>
      </div>
    );
  }

  // 其他类型不显示
  return null;
};

export default App;
