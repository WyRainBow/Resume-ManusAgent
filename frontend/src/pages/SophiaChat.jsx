/**
 * SophiaChat - 复刻 sophia-pro 风格的对话页面
 * 
 * 功能：
 * - AI 输出的 Thought Process（来自后端，折叠面板样式）
 * - 流式输出和打字机效果
 * - Markdown 渲染
 */

import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

// ============================================================================
// 配置
// ============================================================================

const WS_CONFIG = {
  PORT: 8080,
  PATH: '/ws',
  getUrl: () => `ws://localhost:${WS_CONFIG.PORT}${WS_CONFIG.PATH}`
};

// ============================================================================
// 打字机效果 Hook（复刻自 sophia-pro）
// ============================================================================

function useTypewriter(text, speed = 25, enabled = true) {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const indexRef = useRef(0);
  const timerRef = useRef(null);
  
  useEffect(() => {
    if (!enabled || !text) {
      setDisplayedText(text || '');
      setIsComplete(true);
      return;
    }
    
    setDisplayedText('');
    setIsComplete(false);
    indexRef.current = 0;
    
    const typeNext = () => {
      if (indexRef.current < text.length) {
        const chunk = Math.min(Math.floor(Math.random() * 3) + 1, text.length - indexRef.current);
        indexRef.current += chunk;
        setDisplayedText(text.slice(0, indexRef.current));
        timerRef.current = setTimeout(typeNext, speed + Math.random() * 15);
      } else {
        setIsComplete(true);
      }
    };
    
    timerRef.current = setTimeout(typeNext, 50);
    return () => clearTimeout(timerRef.current);
  }, [text, speed, enabled]);
  
  return { displayedText, isComplete };
}

// ============================================================================
// Thought Process 组件（复刻 sophia-pro 第四张图样式）
// ============================================================================

function ThoughtProcess({ content, isStreaming }) {
  const [expanded, setExpanded] = useState(true);
  
  if (!content) return null;
  
  return (
    <div className="mb-4">
      <div 
        className="cursor-pointer flex items-center gap-2 py-1"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex gap-1 items-center">
          <span className="text-slate-400 text-sm font-normal">Thought Process</span>
          <svg 
            className={`w-3 h-3 text-slate-400 transition-transform duration-200 ${expanded ? '' : 'rotate-180'}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          </svg>
        </div>
        {isStreaming && (
          <div className="flex gap-1 ml-1">
            <span className="w-1 h-1 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
            <span className="w-1 h-1 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '100ms' }}></span>
            <span className="w-1 h-1 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '200ms' }}></span>
          </div>
        )}
      </div>
      
      {expanded && (
        <div className="text-slate-400 text-sm leading-relaxed pl-0 font-normal">
          {content}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Markdown 渲染（复刻 sophia-pro 样式）
// ============================================================================

function MarkdownContent({ children, className = '' }) {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        components={{
          p: ({ children }) => (
            <p className="mb-4 text-gray-800 leading-relaxed">{children}</p>
          ),
          strong: ({ children }) => (
            <strong className="font-bold text-gray-900">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="italic">{children}</em>
          ),
          ul: ({ children }) => (
            <ul className="mb-4 space-y-2">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-4 space-y-2 list-decimal ml-6">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="text-gray-800 leading-relaxed pl-1">{children}</li>
          ),
          h1: ({ children }) => (
            <h1 className="text-xl font-bold text-gray-900 mb-4 mt-6">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-bold text-gray-900 mb-3 mt-5">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-bold text-gray-900 mb-2 mt-4">{children}</h3>
          ),
          code: ({ inline, children }) => (
            inline ? (
              <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800">{children}</code>
            ) : (
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm font-mono overflow-x-auto mb-4">
                <code>{children}</code>
              </pre>
            )
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 my-4">{children}</blockquote>
          ),
          a: ({ href, children }) => (
            <a href={href} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">{children}</a>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}

// ============================================================================
// 对话消息组件（复刻 sophia-pro 样式）
// ============================================================================

function ChatMessage({ message, isLatest, isStreaming }) {
  const { displayedText, isComplete } = useTypewriter(
    message.content,
    20,
    message.role === 'assistant' && isLatest && isStreaming
  );
  
  if (message.role === 'user') {
    return (
      <div className="flex justify-end mb-6">
        <div className="max-w-[80%]">
          <div className="text-right text-xs text-gray-400 mb-1">
            {new Date().toLocaleString()}
          </div>
          <div className="bg-white border border-gray-200 rounded-lg px-4 py-3 text-gray-800">
            {message.content}
          </div>
        </div>
      </div>
    );
  }
  
  // Assistant 消息
  const textToShow = isLatest && isStreaming ? displayedText : message.content;
  
  return (
    <div className="mb-6">
      {/* Thought Process（如果有） */}
      {message.thought && (
        <ThoughtProcess 
          content={message.thought} 
          isStreaming={isLatest && isStreaming && !message.content}
        />
      )}
      
      {/* Response 内容 */}
      {textToShow && (
        <div className="text-gray-800">
          <MarkdownContent>{textToShow}</MarkdownContent>
          {isLatest && isStreaming && !isComplete && (
            <span className="inline-block w-0.5 h-4 bg-gray-400 animate-pulse ml-0.5" />
          )}
        </div>
      )}
      
      {/* 反馈按钮 */}
      {!isStreaming && message.content && (
        <div className="flex gap-2 mt-4">
          <button className="p-1.5 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
            </svg>
          </button>
          <button className="p-1.5 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
            </svg>
          </button>
          <button className="p-1.5 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="1.5" />
              <circle cx="6" cy="12" r="1.5" />
              <circle cx="18" cy="12" r="1.5" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// 主页面组件
// ============================================================================

export default function SophiaChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [status, setStatus] = useState('disconnected');
  const [currentThought, setCurrentThought] = useState('');
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  
  useEffect(() => {
    connectWebSocket();
    return () => wsRef.current?.close();
  }, []);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentThought, currentAnswer]);
  
  const connectWebSocket = () => {
    const wsUrl = WS_CONFIG.getUrl();
    console.log('[SophiaChat] Connecting to', wsUrl);
    setStatus('connecting');
    
    const socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
      console.log('[SophiaChat] Connected');
      setStatus('idle');
      wsRef.current = socket;
    };
    
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('[SophiaChat] Received:', data.type, data);
        handleMessage(data);
      } catch (e) {
        console.error('[SophiaChat] Parse error:', e);
      }
    };
    
    socket.onerror = () => setStatus('disconnected');
    socket.onclose = () => {
      setStatus('disconnected');
      wsRef.current = null;
      setTimeout(connectWebSocket, 3000);
    };
  };
  
  const handleMessage = (data) => {
    switch (data.type) {
      case 'thought':
        setCurrentThought(prev => prev + (data.content || ''));
        break;
        
      case 'answer':
        setCurrentAnswer(prev => prev + (data.content || ''));
        break;
        
      case 'status':
        if (data.content === 'processing') {
          setIsProcessing(true);
        } else if (data.content === 'complete' || data.content === 'stopped') {
          finalizeMessage();
        }
        break;
        
      case 'complete':
        finalizeMessage();
        break;
        
      case 'error':
        setIsProcessing(false);
        setStatus('idle');
        break;
    }
  };
  
  const finalizeMessage = () => {
    if (currentThought || currentAnswer) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          thought: currentThought,
          content: currentAnswer,
        }
      ]);
    }
    setCurrentThought('');
    setCurrentAnswer('');
    setIsProcessing(false);
    setStatus('idle');
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;
    
    const userMessage = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setCurrentThought('');
    setCurrentAnswer('');
    setIsProcessing(true);
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ prompt: userMessage }));
      setStatus('processing');
      setInput('');
    }
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-b from-orange-50 to-white">
      {/* Header */}
      <header className="border-b border-gray-100 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <h1 className="text-xl font-semibold text-gray-800">
            SophiaPro Chat
          </h1>
          <p className="text-sm text-gray-500">
            Thought Process · Streaming · Markdown
          </p>
        </div>
      </header>
      
      {/* Chat Area */}
      <main className="max-w-4xl mx-auto px-6 py-8 pb-32">
        {messages.length === 0 && !isProcessing && (
          <div className="text-center py-20">
            <div className="text-5xl mb-4">✨</div>
            <p className="text-gray-600 text-lg mb-2">
              输入 <span className="font-medium text-orange-500">"你好"</span> 开始对话
            </p>
            <p className="text-gray-400 text-sm">
              体验 Thought Process · 流式输出 · Markdown 渲染
            </p>
          </div>
        )}
        
        {/* 历史消息 */}
        {messages.map((msg, idx) => (
          <ChatMessage 
            key={idx} 
            message={msg}
            isLatest={idx === messages.length - 1 && msg.role === 'assistant'}
            isStreaming={false}
          />
        ))}
        
        {/* 当前正在生成的消息 */}
        {isProcessing && (currentThought || currentAnswer) && (
          <ChatMessage 
            message={{
              role: 'assistant',
              thought: currentThought,
              content: currentAnswer,
            }}
            isLatest={true}
            isStreaming={true}
          />
        )}
        
        {/* Loading */}
        {isProcessing && !currentThought && !currentAnswer && (
          <div className="flex items-center gap-2 text-gray-400 text-sm mb-6">
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '100ms' }}></span>
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '200ms' }}></span>
            </div>
            <span>Thinking...</span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </main>
      
      {/* Input Area */}
      <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-white via-white to-transparent pt-6 pb-6">
        <div className="max-w-4xl mx-auto px-6">
          <form onSubmit={handleSubmit}>
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
              <div className="flex items-center">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="输入消息..."
                  className="flex-1 px-4 py-3 outline-none text-gray-700 placeholder-gray-400"
                  disabled={isProcessing}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isProcessing}
                  className="px-6 py-3 text-gray-500 hover:text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
            </div>
          </form>
          
          {/* Status */}
          <div className="text-center mt-3 text-xs text-gray-400">
            <span className={`inline-flex items-center gap-1.5 ${
              status === 'idle' ? 'text-green-500' : 
              status === 'processing' ? 'text-orange-500' : 'text-gray-400'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${
                status === 'idle' ? 'bg-green-500' :
                status === 'processing' ? 'bg-orange-500 animate-pulse' : 'bg-gray-400'
              }`}></span>
              {status === 'idle' ? 'Ready' : status === 'processing' ? 'Processing...' : 'Connecting...'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
