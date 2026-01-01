import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Loader2, Terminal, FileText, ChevronDown, ChevronUp, X, Eye } from 'lucide-react';
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

    // 添加用户消息
    setMessages(prev => [...prev, { role: 'user', content: input }]);

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
        showResumePanel ? 'flex-1 max-w-2xl' : 'w-full max-w-5xl mx-auto'
      }`}>

        {/* Header with Navigation */}
        <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white">
              <Bot size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">OpenManus</h1>
              <div className="flex items-center gap-2 text-xs">
                <span className={`w-2 h-2 rounded-full ${status === 'disconnected' ? 'bg-red-500' : 'bg-green-500'}`}></span>
                <span className="text-gray-500">
                  {status === 'processing' ? '正在思考...' : (status === 'disconnected' ? '未连接' : '就绪')}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadSampleResume}
              className="flex items-center gap-2 px-4 py-2 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors text-sm"
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
              <p className="text-lg">准备好为您服务。请输入您的任务。</p>
              <div className="mt-6 text-sm text-gray-400">
                <p>试着说：</p>
                <ul className="mt-2 space-y-1">
                  <li
                    className="cursor-pointer hover:text-indigo-500 underline"
                    onClick={() => setInput('请帮我加载示例简历')}
                  >请帮我加载示例简历</li>
                  <li
                    className="cursor-pointer hover:text-indigo-500 underline"
                    onClick={() => setInput('请介绍一下这位候选人')}
                  >请介绍一下这位候选人</li>
                  <li
                    className="cursor-pointer hover:text-indigo-500 underline"
                    onClick={() => setInput('把我的邮箱改成 newemail@example.com')}
                  >把我的邮箱改成 newemail@example.com</li>
                  <li
                    className="cursor-pointer hover:text-indigo-500 underline"
                    onClick={() => setInput('帮我添加一个技能：Python')}
                  >帮我添加一个技能：Python</li>
                </ul>
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <MessageItem key={idx} message={msg} />
          ))}

          {status === 'processing' && (
            <div className="flex items-center gap-2 text-gray-400 text-sm ml-12 animate-pulse">
              <Loader2 size={16} className="animate-spin" />
              <span>OpenManus 正在思考...</span>
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
              placeholder="输入您的指令...（试试：请帮我加载示例简历）"
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
        <div className="flex-1 border-l border-gray-200 bg-gray-100 flex flex-col overflow-hidden">
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
        <div className="bg-indigo-600 text-white px-5 py-3 rounded-2xl rounded-tr-none max-w-[80%] shadow-sm">
          {message.content}
        </div>
      </div>
    );
  }

  // 步骤信息展示
  if (message.type === 'step') {
    return (
      <div className="flex justify-center mb-2">
        <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-2 text-sm text-blue-700">
          <span className="font-medium">步骤 {message.step}:</span> {message.content}
        </div>
      </div>
    );
  }

  // 工具调用展示
  if (message.type === 'tool_call') {
    const isCVTool = message.tool === 'load_resume_data' || message.tool === 'cv_reader_agent' || message.tool === 'cv_editor_agent';
    return (
      <div className="flex justify-start ml-12 mb-2">
        <div className={`border rounded-lg p-3 max-w-[90%] w-full ${
          isCVTool
            ? 'bg-green-50 border-green-200'
            : 'bg-gray-100 border-gray-200'
        }`}>
          <div
            className="flex items-center justify-between cursor-pointer text-gray-600 text-sm"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            <div className="flex items-center gap-2">
              <Terminal size={14} />
              <span className="font-mono font-medium">
                {isCVTool ? '📄 ' : ''}使用工具: {message.tool}
              </span>
            </div>
            {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </div>

          {isExpanded && (
            <div className="mt-2 bg-gray-900 text-gray-100 p-3 rounded text-xs font-mono overflow-x-auto">
              <pre>{typeof message.args === 'string'
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

  // 工具结果展示
  if (message.type === 'tool_result') {
    const isCVTool = message.tool === 'load_resume_data' || message.tool === 'cv_reader_agent' || message.tool === 'cv_editor_agent';
    return (
      <div className="flex justify-start ml-12 mb-2">
        <div className={`border rounded-lg p-3 max-w-[90%] w-full ${
          isCVTool
            ? 'bg-green-50 border-green-200'
            : 'bg-blue-50 border border-blue-100'
        }`}>
          <div
            className="flex items-center justify-between cursor-pointer text-blue-700 text-sm"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            <div className="flex items-center gap-2">
              <FileText size={14} />
              <span className="font-medium">
                {isCVTool ? '📄 ' : ''}工具执行结果: {message.tool}
              </span>
            </div>
            {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </div>

          {isExpanded && (
            <div className="mt-2 bg-white border border-blue-100 p-3 rounded text-xs text-gray-600 font-mono overflow-x-auto max-h-64 overflow-y-auto">
              <pre>{message.content}</pre>
            </div>
          )}
        </div>
      </div>
    );
  }

  // 思考过程
  if (message.type === 'thought') {
    return (
      <div className="flex gap-4">
        <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
          <Bot size={18} className="text-gray-500" />
        </div>
        <div className="flex-1 bg-white border border-gray-100 p-4 rounded-2xl rounded-tl-none shadow-sm text-gray-600 italic">
          <ReactMarkdown className="prose prose-sm max-w-none text-gray-600">
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    );
  }

  // 最终答案
  return (
    <div className="flex gap-4">
      <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0">
        <Bot size={18} className="text-indigo-600" />
      </div>
      <div className="flex-1 bg-white border border-gray-100 p-5 rounded-2xl rounded-tl-none shadow-sm">
        <ReactMarkdown className="prose prose-sm max-w-none">
          {message.content}
        </ReactMarkdown>
      </div>
    </div>
  );
};

export default App;
