import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Loader2, Terminal, FileText, ChevronDown, ChevronUp, X, Eye, Sparkles, Brain, Zap, CheckCircle2, AlertCircle, Wrench, Search, Edit, BarChart, MessageSquare } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import HTMLTemplateRenderer from './components/HTMLTemplateRenderer';

// 示例简历数据
const SAMPLE_RESUME = {
  id: 'sample-001',
  title: '前端工程师简历',
  basic: {
    name: '张三',
    title: '高级前端工程师',
    email: 'zhangsan@example.com',
    phone: '13800138000',
    location: '北京',
    employementStatus: '在职，看机会'
  },
  education: [
    {
      id: 'edu-1',
      school: '北京大学',
      degree: '学士',
      major: '计算机科学与技术',
      startDate: '2018-09',
      endDate: '2022-06',
      gpa: '3.8/4.0',
      description: '<p>主修课程：数据结构、算法、计算机网络、操作系统</p>'
    }
  ],
  experience: [
    {
      id: 'exp-1',
      company: '阿里巴巴',
      position: '前端工程师',
      date: '2022-07 - 至今',
      details: '<p>负责淘宝前端页面开发，使用 React 和 TypeScript</p><p>优化页面性能，提升用户体验</p>'
    }
  ],
  projects: [
    {
      id: 'proj-1',
      name: '开源组件库',
      role: '核心开发者',
      date: '2023-01 - 2023-12',
      description: '<p>开发了一套 React 组件库，已在 GitHub 获得 1000+ stars</p>',
      link: 'https://github.com/example/ui-lib'
    }
  ],
  openSource: [
    {
      id: 'os-1',
      name: 'Vue.js',
      role: '贡献者',
      description: '<p>修复了多个 bug，参与了新功能开发</p>',
      repo: 'https://github.com/vuejs/core'
    }
  ],
  awards: [
    {
      id: 'award-1',
      title: '优秀员工',
      issuer: '阿里巴巴',
      date: '2023-12'
    }
  ],
  skillContent: '<p><strong>前端技能：</strong>React, Vue, TypeScript, HTML/CSS</p><p><strong>后端技能：</strong>Node.js, Python</p>',
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

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState('idle'); // idle, connecting, processing
  const [ws, setWs] = useState(null);
  const messagesEndRef = useRef(null);
  const [showResumePanel, setShowResumePanel] = useState(false);
  const [resumeData, setResumeData] = useState(SAMPLE_RESUME);
  const [showThinkingProcess, setShowThinkingProcess] = useState(false);

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

  const handleMessage = (data) => {
    setMessages(prev => {
      const newMessages = [...prev];
      const lastMsg = newMessages[newMessages.length - 1];

      // 如果是步骤更新
      if (data.type === 'step') {
        // 显示步骤信息
        return [...newMessages, {
          role: 'system',
          type: 'step',
          content: data.content,
          step: data.step
        }];
      }

      // 如果是思考过程 (thought)
      if (data.type === 'thought') {
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
        const isCVTool = data.tool === 'cv_editor_agent' || data.tool === 'load_resume_data';
        if (isCVTool && data.result && (
          data.result.includes('✅') ||
          data.result.includes('Successfully loaded') ||
          data.result.includes('Candidate:')
        )) {
          // 给后端一点时间处理数据
          setTimeout(() => refreshResumeData(), 300);
        }

        return [...newMessages, toolResultMsg];
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

    // 检测是否是问候消息
    const isGreeting = /^(你好|您好|hi|hello|嗨)$/i.test(input.trim());

    // 添加用户消息
    setMessages(prev => [...prev, { role: 'user', content: input }]);

    // 如果是问候，立即返回markdown欢迎消息
    if (isGreeting) {
      setMessages(prev => [...prev, {
        role: 'agent',
        type: 'greeting',
        content: `# 👋 你好！我是 OpenManus

很高兴为您服务！我可以帮您：

## ✨ 我的能力

- 📊 **分析简历** - 深入分析简历质量和问题
- ✏️ **优化简历** - 改进内容和格式，提升竞争力
- 💡 **求职建议** - 提供专业的求职指导
- 🎨 **格式美化** - 优化简历结构和排版

## 🚀 如何开始

1. **加载简历** - 请先上传或输入您的简历数据
2. **分析问题** - 告诉我 '分析一下我的简历'
3. **开始优化** - 跟随我的建议逐步优化

请告诉我您的需求，让我们开始吧！ 😊`
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

  const loadSampleResume = () => {
    setResumeData(SAMPLE_RESUME);
    setShowResumePanel(true);
    // 自动发送加载简历的消息
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ prompt: '请帮我加载示例简历' }));
      setStatus('processing');
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

  return (
    <div className="flex h-screen bg-gray-50 text-gray-900 font-sans">
      {/* 主聊天区域 */}
      <div className={`flex flex-col h-full bg-white shadow-xl overflow-hidden transition-all duration-300 ${
        showResumePanel ? 'w-1/2' : 'w-full max-w-5xl mx-auto'
      }`}>

        {/* Header with Navigation */}
        <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white transition-all duration-300 ${
              status === 'processing' ? 'bg-gradient-to-br from-violet-500 to-purple-600 shadow-lg shadow-violet-200' : 'bg-indigo-600'
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
                <span className={`w-2 h-2 rounded-full ${
                  status === 'disconnected' ? 'bg-red-500' :
                  status === 'processing' ? 'bg-violet-500 animate-pulse' : 'bg-green-500'
                }`}></span>
                <span className="text-gray-500">
                  {status === 'processing' ? '正在思考中...' : (status === 'disconnected' ? '未连接' : '✅ 就绪')}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadSampleResume}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-emerald-50 to-teal-50 text-emerald-700 rounded-lg hover:from-emerald-100 hover:to-teal-100 transition-all text-sm border border-emerald-200"
            >
              <FileText size={16} />
              <span>加载简历</span>
            </button>
            <button
              onClick={() => setShowResumePanel(!showResumePanel)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors text-sm ${
                showResumePanel
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
                        <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
                        <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                        <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
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
              placeholder="告诉我您的信息，帮您生成简历...（例如：我叫张三，是一名后端工程师）"
              className="w-full pl-4 pr-12 py-3 bg-gray-100 border-0 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all resize-none min-h-[56px] max-h-32"
              rows="1"
            />
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

  // 工具调用展示 - 增强版
  if (message.type === 'tool_call') {
    const isCVTool = message.tool === 'load_resume_data' || message.tool === 'cv_reader_agent' || message.tool === 'cv_editor_agent';

    // 工具图标映射
    const toolIconComponents = {
      'load_resume_data': null, // 不显示图标
      'cv_reader_agent': null, // 使用 emoji 🔍
      'cv_editor_agent': Edit,
      'get_resume_structure': BarChart,
      'create_chat_completion': MessageSquare,
    };

    const toolEmojis = {
      'cv_reader_agent': '🔍',
    };

    const toolColors = {
      'load_resume_data': 'from-emerald-50 to-teal-50 border-emerald-200 text-emerald-700 bg-emerald-50/50',
      'cv_reader_agent': 'from-blue-50 to-cyan-50 border-blue-200 text-blue-700 bg-blue-50/50',
      'cv_editor_agent': 'from-violet-50 to-purple-50 border-violet-200 text-violet-700 bg-violet-50/50',
      'get_resume_structure': 'from-amber-50 to-orange-50 border-amber-200 text-amber-700 bg-amber-50/50',
    };

    const colorClass = toolColors[message.tool] || 'from-gray-50 to-slate-50 border-gray-200 text-gray-700 bg-gray-50/50';
    const IconComponent = toolIconComponents[message.tool];
    const emoji = toolEmojis[message.tool];

    return (
      <div className="flex justify-start ml-10 my-2">
        <div className={`bg-gradient-to-r ${colorClass} border rounded-xl p-3.5 max-w-[90%] w-full shadow-sm transition-all duration-200 hover:shadow-md hover:scale-[1.01]`}>
          <div
            className="flex items-center justify-between cursor-pointer"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            <div className="flex items-center gap-3">
              {emoji ? (
                <div className={`p-1.5 rounded-lg ${message.tool === 'cv_reader_agent' ? 'bg-blue-100' : 'bg-gray-100'}`}>
                  <span className="text-base">{emoji}</span>
                </div>
              ) : IconComponent ? (
                <div className={`p-1.5 rounded-lg ${message.tool === 'cv_editor_agent' ? 'bg-violet-100' :
                                                        message.tool === 'get_resume_structure' ? 'bg-amber-100' :
                                                        'bg-gray-100'}`}>
                  <IconComponent size={16} className={message.tool === 'cv_editor_agent' ? 'text-violet-600' :
                                                          message.tool === 'get_resume_structure' ? 'text-amber-600' :
                                                          'text-gray-600'} />
                </div>
              ) : null}
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm">调用工具</span>
                <span className="font-mono text-xs bg-white/70 px-2 py-1 rounded-md border border-white/50">{message.tool}</span>
              </div>
            </div>
            <div className={`transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}>
              <ChevronDown size={16} className="opacity-60" />
            </div>
          </div>

          {isExpanded && (
            <div className="mt-3 bg-gray-900 text-gray-100 p-4 rounded-lg text-xs font-mono overflow-x-auto shadow-inner border border-gray-800">
              <div className="flex items-center gap-2 text-gray-400 mb-2 pb-2 border-b border-gray-700">
                <Terminal size={12} />
                <span>参数</span>
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

  // 工具结果展示 - 增强版
  if (message.type === 'tool_result') {
    const isCVTool = message.tool === 'load_resume_data' || message.tool === 'cv_reader_agent' || message.tool === 'cv_editor_agent';
    const isSuccess = message.content && (message.content.includes('✅') || message.content.includes('Successfully') || message.content.includes('成功'));

    // 如果是成功状态，显示简洁的成功通知卡片（参考文档中的深色成功通知样式）
    if (isSuccess) {
      const successText = message.content.includes('读取') || message.content.includes('load') ? '读取简历内容执行成功' :
                         message.content.includes('分析') || message.content.includes('analyze') ? '分析简历执行成功' :
                         message.content.includes('编辑') || message.content.includes('edit') ? '编辑简历执行成功' :
                         '执行成功';

      return (
        <div className="flex flex-col justify-start ml-10 my-2">
          <div className="bg-gray-800 rounded-xl px-4 py-3 flex items-center gap-3 shadow-lg max-w-[90%] cursor-pointer hover:bg-gray-700 transition-colors"
               onClick={() => setIsExpanded(!isExpanded)}>
            <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0">
              <CheckCircle2 size={14} className="text-white" />
            </div>
            <span className="text-white text-sm font-medium flex-1">{successText}</span>
            <div className={`transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}>
              <ChevronDown size={16} className="text-gray-400" />
            </div>
          </div>
          {isExpanded && (
            <div className="mt-2 bg-white border border-gray-200 p-3 rounded-lg text-xs font-mono overflow-x-auto max-h-64 overflow-y-auto shadow-inner max-w-[90%]">
              <pre className="text-gray-600 whitespace-pre-wrap">{message.content}</pre>
            </div>
          )}
        </div>
      );
    }

    // 工具图标映射
    const toolIconComponents = {
      'load_resume_data': null, // 不显示图标
      'cv_reader_agent': null, // 使用 emoji 🔍
      'cv_editor_agent': Edit,
      'get_resume_structure': BarChart,
    };

    const toolEmojis = {
      'cv_reader_agent': '🔍',
    };

    const IconComponent = toolIconComponents[message.tool];
    const emoji = toolEmojis[message.tool];

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
              ) : emoji ? (
                <div className="p-1.5 rounded-lg bg-blue-100">
                  <span className="text-base">{emoji}</span>
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
            <div className={`transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}>
              <ChevronDown size={16} className="opacity-60" />
            </div>
          </div>

          {isExpanded && (
            <div className={`mt-3 bg-white border ${isSuccess ? 'border-green-100' : 'border-blue-100'} p-3 rounded-lg text-xs font-mono overflow-x-auto max-h-64 overflow-y-auto shadow-inner`}>
              <pre className={isSuccess ? 'text-green-700' : 'text-gray-600 whitespace-pre-wrap'}>{message.content}</pre>
            </div>
          )}
        </div>
      </div>
    );
  }

  // 思考过程 - 全新设计，参考 Claude/Cursor
  if (message.type === 'thought') {
    return (
      <div className="flex gap-3 my-3">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-md">
          <Brain size={16} className="text-white" />
        </div>
        <div className="flex-1 bg-gradient-to-br from-violet-50/50 to-purple-50/50 border border-violet-100 p-4 rounded-2xl rounded-tl-none shadow-sm">
          <div className="flex items-center gap-2 mb-2 text-violet-700">
            <Sparkles size={14} className="text-violet-500" />
            <span className="text-xs font-semibold uppercase tracking-wide text-violet-500">思考过程</span>
          </div>
          <ReactMarkdown className="prose prose-sm max-w-none text-gray-700">
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    );
  }

  // 问候消息 - 纯 markdown 渲染
  if (message.type === 'greeting') {
    return (
      <div className="flex gap-3 my-4">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-md">
          <Bot size={16} className="text-white" />
        </div>
        <div className="flex-1 prose prose-sm max-w-none prose-headings:font-bold prose-headings:text-indigo-900 prose-a:text-indigo-700">
          <ReactMarkdown>
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    );
  }

  // 最终答案 - 全新设计，增强 Markdown 渲染样式
  return (
    <div className="flex gap-3 my-4">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-md">
        <Bot size={16} className="text-white" />
      </div>
      <div className="flex-1 bg-gray-50 border border-gray-200 p-5 rounded-2xl rounded-tl-none shadow-md">
        <ReactMarkdown
          className="prose prose-sm max-w-none
            prose-headings:text-gray-800 prose-headings:font-bold prose-headings:mt-6 prose-headings:mb-3
            prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg
            prose-p:text-gray-700 prose-p:leading-relaxed prose-p:mb-4
            prose-strong:text-gray-800 prose-strong:font-semibold
            prose-ul:list-disc prose-ul:ml-6 prose-ul:mb-4
            prose-ol:list-decimal prose-ol:ml-6 prose-ol:mb-4
            prose-li:text-gray-700 prose-li:mb-2
            prose-code:text-sm prose-code:bg-gray-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
            prose-blockquote:border-l-4 prose-blockquote:border-gray-300 prose-blockquote:pl-4 prose-blockquote:italic
            prose-a:text-indigo-600 prose-a:underline hover:prose-a:text-indigo-800"
          components={{
            // 自定义占位符样式（如 summary, keywords 等）
            p: ({node, children, ...props}) => {
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
