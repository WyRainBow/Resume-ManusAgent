/**
 * SophiaChat - 复刻 sophia-pro 风格的对话页面
 * 
 * 功能：
 * - 意图识别（通过提示词规则）
 * - Thought Process 显示
 * - 流式输出和打字机效果
 * - Markdown 渲染
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';

// ============================================================================
// 配置
// ============================================================================

const WS_CONFIG = {
  PORT: 8000,
  PATH: '/ws',
  getUrl: () => `ws://localhost:${WS_CONFIG.PORT}${WS_CONFIG.PATH}`
};

// ============================================================================
// 意图识别规则（复刻自 sophia-pro 的 greeting_exception）
// ============================================================================

const GREETING_KEYWORDS = ['你好', '您好', 'hello', 'hi', 'hey', '早上好', '下午好', '晚上好', '介绍'];
const CASUAL_KEYWORDS = ['谢谢', 'thanks', '再见', 'bye', '怎么样'];

function detectIntent(message) {
  const lower = message.toLowerCase();
  
  for (const kw of GREETING_KEYWORDS) {
    if (lower.includes(kw.toLowerCase())) {
      return {
        type: 'greeting',
        reasoning: `这是一个简单的问候和自我介绍请求,属于casual conversation类型。根据"Special Exception for Simple Greetings and Casual Conversations"规则,我应该在Response部分用自然、温暖、热情的方式回应,展现个性和真诚的连接感。不需要使用ask_human、需求澄清或任务规划。我应该用中文回复,因为用户用中文提问。`
      };
    }
  }
  
  for (const kw of CASUAL_KEYWORDS) {
    if (lower.includes(kw.toLowerCase())) {
      return {
        type: 'casual_chat',
        reasoning: `这是一个简单的休闲对话,属于casual conversation类型。根据规则,我应该用自然、温暖的方式回应。`
      };
    }
  }
  
  return {
    type: 'task_oriented',
    reasoning: `这是一个任务导向的请求,需要进行需求分析和任务规划。`
  };
}

// ============================================================================
// 打字机效果 Hook
// ============================================================================

function useTypewriter(text, speed = 30, enabled = true) {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const indexRef = useRef(0);
  const animationRef = useRef(null);
  
  useEffect(() => {
    if (!enabled || !text) {
      setDisplayedText(text || '');
      setIsComplete(true);
      return;
    }
    
    setDisplayedText('');
    setIsComplete(false);
    indexRef.current = 0;
    
    const animate = () => {
      if (indexRef.current < text.length) {
        const chunkSize = Math.max(1, Math.floor(speed / 10));
        const endIndex = Math.min(indexRef.current + chunkSize, text.length);
        setDisplayedText(text.slice(0, endIndex));
        indexRef.current = endIndex;
        animationRef.current = requestAnimationFrame(animate);
      } else {
        setIsComplete(true);
      }
    };
    
    // 延迟启动动画
    const timer = setTimeout(() => {
      animationRef.current = requestAnimationFrame(animate);
    }, 100);
    
    return () => {
      clearTimeout(timer);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [text, speed, enabled]);
  
  return { displayedText, isComplete };
}

// ============================================================================
// Thought Process 组件
// ============================================================================

function ThoughtProcess({ content, isStreaming }) {
  const [expanded, setExpanded] = useState(true);
  
  if (!content) return null;
  
  return (
    <div className="thought-process mb-4">
      <div 
        className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl overflow-hidden"
        style={{ boxShadow: '0 2px 8px rgba(251, 191, 36, 0.1)' }}
      >
        <div 
          className="px-4 py-3 cursor-pointer flex items-center justify-between"
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex items-center gap-2">
            <span className="text-amber-600">💭</span>
            <span className="text-sm font-medium text-amber-700">
              {isStreaming ? 'Thinking...' : 'Thought Process'}
            </span>
            {isStreaming && (
              <div className="flex gap-1 ml-2">
                <span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
            )}
          </div>
          <svg 
            className={`w-4 h-4 text-amber-500 transition-transform ${expanded ? 'rotate-180' : ''}`} 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
        
        {expanded && (
          <div className="px-4 pb-4 border-t border-amber-100">
            <p className="text-sm text-amber-800 leading-relaxed pt-3">
              {content}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// 消息组件
// ============================================================================

function Message({ message, isLatest }) {
  const { displayedText, isComplete } = useTypewriter(
    message.content, 
    40, 
    message.role === 'assistant' && isLatest
  );
  
  if (message.role === 'user') {
    return (
      <div className="flex justify-end mb-4">
        <div 
          className="max-w-[70%] px-4 py-3 rounded-2xl rounded-tr-sm text-white"
          style={{ 
            background: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
            boxShadow: '0 2px 10px rgba(249, 115, 22, 0.3)'
          }}
        >
          {message.content}
        </div>
      </div>
    );
  }
  
  // Assistant message with Markdown
  return (
    <div className="flex justify-start mb-4">
      <div className="flex gap-3 max-w-[85%]">
        <div 
          className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)' }}
        >
          <span className="text-white text-sm">✨</span>
        </div>
        <div 
          className="px-4 py-3 rounded-2xl rounded-tl-sm bg-white border border-gray-100"
          style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}
        >
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 text-gray-700 leading-relaxed">{children}</p>,
                strong: ({ children }) => <strong className="text-gray-900 font-semibold">{children}</strong>,
                ul: ({ children }) => <ul className="list-disc ml-4 mb-2 space-y-1">{children}</ul>,
                li: ({ children }) => <li className="text-gray-700">{children}</li>,
                h1: ({ children }) => <h1 className="text-lg font-bold text-gray-900 mb-2">{children}</h1>,
                h2: ({ children }) => <h2 className="text-base font-bold text-gray-900 mb-2">{children}</h2>,
                code: ({ children }) => <code className="bg-gray-100 px-1 rounded text-sm">{children}</code>,
              }}
            >
              {message.role === 'assistant' && isLatest ? displayedText : message.content}
            </ReactMarkdown>
            {message.role === 'assistant' && isLatest && !isComplete && (
              <span className="inline-block w-2 h-4 bg-orange-500 animate-pulse ml-0.5"></span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// 主页面组件
// ============================================================================

export default function SophiaChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [status, setStatus] = useState('idle');
  const [thoughtContent, setThoughtContent] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [ws, setWs] = useState(null);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  
  // WebSocket 连接
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);
  
  // 自动滚动
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thoughtContent]);
  
  const connectWebSocket = () => {
    const wsUrl = WS_CONFIG.getUrl();
    console.log('Connecting to', wsUrl);
    setStatus('connecting');
    
    const socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
      console.log('Connected');
      setStatus('idle');
      setWs(socket);
      wsRef.current = socket;
    };
    
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (e) {
        console.error('Parse error:', e);
      }
    };
    
    socket.onerror = () => {
      setStatus('disconnected');
    };
    
    socket.onclose = () => {
      setStatus('disconnected');
      setWs(null);
      wsRef.current = null;
      setTimeout(connectWebSocket, 3000);
    };
  };
  
  const handleMessage = (data) => {
    if (data.type === 'thought') {
      setThoughtContent(prev => prev + (data.content || ''));
    }
    
    if (data.type === 'answer') {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.content
      }]);
      setThoughtContent('');
      setIsThinking(false);
      setStatus('idle');
    }
    
    if (data.type === 'status') {
      if (data.content === 'processing') {
        setStatus('processing');
      } else if (data.content === 'stopped') {
        setStatus('idle');
        setIsThinking(false);
      }
    }
    
    if (data.type === 'error') {
      setStatus('idle');
      setIsThinking(false);
    }
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || status === 'processing') return;
    
    const userMessage = input.trim();
    
    // 添加用户消息
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    
    // 意图识别并显示 Thought Process
    const intent = detectIntent(userMessage);
    setThoughtContent(intent.reasoning);
    setIsThinking(true);
    
    // 发送到后端
    const currentWs = wsRef.current || ws;
    if (currentWs && currentWs.readyState === WebSocket.OPEN) {
      currentWs.send(JSON.stringify({ prompt: userMessage }));
      setStatus('processing');
      setInput('');
    }
  };
  
  return (
    <div 
      className="min-h-screen flex flex-col"
      style={{ 
        background: 'linear-gradient(180deg, #FFF7ED 0%, #FFEDD5 50%, #FFF7ED 100%)'
      }}
    >
      {/* Header */}
      <header className="py-8 text-center">
        <h1 
          className="text-4xl font-bold mb-2"
          style={{ color: '#1a1a1a' }}
        >
          All Marketing. One Command.
        </h1>
        <p className="text-gray-500 text-sm">
          Powered by SophiaPro AI
        </p>
      </header>
      
      {/* Main Content */}
      <main className="flex-1 max-w-3xl w-full mx-auto px-4 pb-32">
        {/* Messages */}
        <div className="space-y-4">
          {messages.length === 0 && !isThinking && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">✨</div>
              <p className="text-gray-500">
                输入 <span className="text-orange-500 font-medium">"你好"</span> 开始对话
              </p>
              <p className="text-gray-400 text-sm mt-2">
                体验意图识别、Thought Process、流式输出和 Markdown 渲染
              </p>
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <Message 
              key={idx} 
              message={msg} 
              isLatest={idx === messages.length - 1 && msg.role === 'assistant'}
            />
          ))}
          
          {/* Thought Process */}
          {isThinking && thoughtContent && (
            <ThoughtProcess 
              content={thoughtContent} 
              isStreaming={status === 'processing'}
            />
          )}
          
          {/* Loading indicator */}
          {status === 'processing' && !thoughtContent && (
            <div className="flex justify-start mb-4">
              <div className="flex gap-3">
                <div 
                  className="w-8 h-8 rounded-full flex items-center justify-center"
                  style={{ background: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)' }}
                >
                  <span className="text-white text-sm animate-pulse">✨</span>
                </div>
                <div className="px-4 py-3 rounded-2xl bg-white border border-gray-100">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </main>
      
      {/* Input Area - Fixed at bottom */}
      <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-orange-50 to-transparent pt-8 pb-6">
        <div className="max-w-3xl mx-auto px-4">
          {/* Input Box */}
          <form onSubmit={handleSubmit}>
            <div 
              className="bg-white rounded-2xl border border-gray-200 overflow-hidden"
              style={{ boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}
            >
              <div className="flex items-center px-4 py-3">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="输入你好开始体验..."
                  className="flex-1 outline-none text-gray-700 placeholder-gray-400"
                  disabled={status === 'processing'}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || status === 'processing'}
                  className="ml-3 px-4 py-2 rounded-xl text-white font-medium transition-all disabled:opacity-50"
                  style={{ 
                    background: input.trim() ? 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)' : '#ccc',
                  }}
                >
                  发送
                </button>
              </div>
              
              {/* Tags */}
              <div className="px-4 pb-3 flex gap-2 flex-wrap">
                {['Influencer Marketing', 'GEO', 'Social Listening', 'AI Writing'].map((tag, idx) => (
                  <span 
                    key={tag}
                    className="px-3 py-1 rounded-full text-xs border cursor-pointer hover:bg-gray-50 transition-colors flex items-center gap-1"
                    style={{ borderColor: '#e5e7eb', color: '#6b7280' }}
                  >
                    <span>{['🟢', '🟡', '🔴', '🟢'][idx]}</span>
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </form>
          
          {/* Status */}
          <div className="text-center mt-3">
            <span className={`inline-flex items-center gap-1 text-xs ${
              status === 'idle' ? 'text-green-600' : 
              status === 'processing' ? 'text-orange-600' : 'text-red-600'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${
                status === 'idle' ? 'bg-green-500' :
                status === 'processing' ? 'bg-orange-500 animate-pulse' : 'bg-red-500'
              }`}></span>
              {status === 'idle' ? '就绪' : status === 'processing' ? '思考中...' : '未连接'}
            </span>
          </div>
          
          <p className="text-center text-gray-400 text-xs mt-2">
            Dive deeper with dedicated apps for advanced work
          </p>
        </div>
      </div>
    </div>
  );
}








