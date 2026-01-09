/**
 * ChatDemo 页面 - 演示意图识别、Thought Process、流式输出和 Markdown 渲染
 * 
 * 复刻自 sophia-pro 项目的聊天功能
 */

import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Loader2, Brain, Sparkles } from 'lucide-react';
import ResponseStream from '../components/ResponseStream';
import ThoughtProcess from '../components/ThoughtProcess';
import EnhancedMarkdown from '../components/EnhancedMarkdown';

// WebSocket 配置
const WS_CONFIG = {
  PORT: 8080,
  PATH: '/ws',
  getUrl: () => `ws://localhost:${WS_CONFIG.PORT}${WS_CONFIG.PATH}`
};

export default function ChatDemo() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState('idle'); // idle, connecting, processing
  const [ws, setWs] = useState(null);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  
  // Thought Process 相关状态
  const [thoughtContent, setThoughtContent] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [intentReasoning, setIntentReasoning] = useState('');
  
  // 流式输出相关状态
  const [streamingAnswer, setStreamingAnswer] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  useEffect(() => {
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
  }, [messages, thoughtContent, streamingAnswer]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const connectWebSocket = () => {
    const wsUrl = WS_CONFIG.getUrl();
    console.log("Connecting to", wsUrl);
    setStatus('connecting');
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('Connected to WebSocket');
      setStatus('idle');
      setWs(socket);
      wsRef.current = socket;
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
      setWs(null);
      wsRef.current = null;
      // 尝试重连
      setTimeout(connectWebSocket, 3000);
    };
  };

  const handleMessage = (data) => {
    // 处理意图识别结果（从后端发送）
    if (data.type === 'intent_result') {
      setIntentReasoning(data.reasoning || '');
      console.log('Intent reasoning:', data.reasoning);
    }

    // 处理思考过程
    if (data.type === 'thought') {
      setIsThinking(true);
      setThoughtContent(prev => prev + (data.content || ''));
    }

    // 处理流式答案
    if (data.type === 'answer_chunk' || data.type === 'answer') {
      setIsStreaming(true);
      if (data.type === 'answer_chunk') {
        setStreamingAnswer(prev => prev + (data.content || ''));
      } else {
        setStreamingAnswer(data.content || '');
        setIsStreaming(false);
        setIsThinking(false);
      }
    }

    // 处理最终答案
    if (data.type === 'answer' && data.content) {
      setMessages(prev => [...prev, {
        role: 'agent',
        type: 'answer',
        content: data.content
      }]);
      setStreamingAnswer('');
      setIsStreaming(false);
      setIsThinking(false);
      setThoughtContent('');
      setStatus('idle');
    }

    // 处理状态更新
    if (data.type === 'status') {
      if (data.content === 'processing') {
        setStatus('processing');
        setIsThinking(true);
      } else if (data.content === 'stopped') {
        setStatus('idle');
        setIsThinking(false);
      }
    }

    // 处理错误
    if (data.type === 'error') {
      setStatus('idle');
      setMessages(prev => [...prev, {
        role: 'system',
        type: 'error',
        content: data.content
      }]);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || status === 'processing') return;

    // 添加用户消息
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    
    // 重置状态
    setThoughtContent('');
    setStreamingAnswer('');
    setIsThinking(false);
    setIsStreaming(false);
    setIntentReasoning('');

    // 发送请求
    const currentWs = wsRef.current || ws;
    if (currentWs && currentWs.readyState === WebSocket.OPEN) {
      currentWs.send(JSON.stringify({ prompt: input.trim() }));
      setStatus('processing');
      setIsThinking(true);
      setInput('');
    } else {
      console.error('WebSocket not connected');
      connectWebSocket();
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 text-gray-900 font-sans">
      {/* 主聊天区域 */}
      <div className="flex flex-col h-full bg-white shadow-xl overflow-hidden w-full max-w-5xl mx-auto">
        {/* Header */}
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
              <h1 className="text-xl font-bold text-gray-800">Reference-Sop 演示</h1>
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
        </header>

        {/* Messages Area */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <Bot size={64} className="mb-4 opacity-20" />
              <p className="text-lg">Reference-Sop 演示</p>
              <p className="text-sm text-gray-400 mt-2">输入"你好"查看意图识别、Thought Process、流式输出和 Markdown 渲染</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <MessageItem key={idx} message={msg} />
          ))}

          {/* 显示意图识别结果 */}
          {intentReasoning && (
            <div className="flex gap-3 my-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center flex-shrink-0 shadow-md">
                <Brain size={16} className="text-white" />
              </div>
              <div className="flex-1 bg-blue-50 border border-blue-100 rounded-2xl rounded-tl-none shadow-sm p-4">
                <div className="text-xs font-semibold uppercase tracking-wide text-blue-500 mb-2">
                  意图识别
                </div>
                <div className="text-sm text-blue-700">
                  {intentReasoning}
                </div>
              </div>
            </div>
          )}

          {/* 显示思考过程 */}
          {isThinking && (
            <ThoughtProcess
              content={thoughtContent}
              isStreaming={isThinking}
              defaultExpanded={true}
            />
          )}

          {/* 显示流式答案 */}
          {isStreaming && streamingAnswer && (
            <div className="flex gap-3 my-4">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-md">
                <Bot size={16} className="text-white" />
              </div>
              <div className="flex-1 bg-gray-50 border border-gray-200 p-4 rounded-2xl rounded-tl-none shadow-md">
                <ResponseStream
                  textStream={streamingAnswer}
                  mode="typewriter"
                  speed={30}
                />
              </div>
            </div>
          )}

          {/* 处理中状态 */}
          {status === 'processing' && !isThinking && !streamingAnswer && (
            <div className="flex gap-3 my-4">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-md">
                <Brain size={16} className="text-white animate-pulse" />
              </div>
              <div className="flex-1 bg-gradient-to-br from-violet-50/50 to-purple-50/50 border border-violet-100 rounded-2xl rounded-tl-none shadow-sm p-4">
                <div className="flex items-center gap-2 text-violet-700">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                  <span className="text-sm font-medium">AI 正在思考中</span>
                  <Sparkles size={14} className="text-violet-500 animate-pulse" />
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
              }}
              placeholder="输入"你好"查看完整功能演示..."
              className="w-full pl-4 pr-12 py-3 bg-gray-100 border-0 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all resize-none min-h-[56px] max-h-32"
              rows="1"
              disabled={status === 'processing'}
            />
            <button
              type="submit"
              disabled={!input.trim() || status === 'processing'}
              className="absolute right-3 bottom-3 p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={18} />
            </button>
          </form>
        </footer>
      </div>
    </div>
  );
}

// 消息组件
const MessageItem = ({ message }) => {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="bg-gradient-to-br from-indigo-600 to-indigo-700 text-white px-5 py-3 rounded-2xl rounded-tr-none max-w-[80%] shadow-md">
          {message.content}
        </div>
      </div>
    );
  }

  // AI 回答 - 使用增强的 Markdown 渲染
  if (message.type === 'answer') {
    return (
      <div className="flex gap-3 my-4">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-md">
          <Bot size={16} className="text-white" />
        </div>
        <div className="flex-1 bg-gray-50 border border-gray-200 p-4 rounded-2xl rounded-tl-none shadow-md">
          <EnhancedMarkdown>
            {message.content}
          </EnhancedMarkdown>
        </div>
      </div>
    );
  }

  // 错误消息
  if (message.type === 'error') {
    return (
      <div className="flex justify-center">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg text-sm">
          ⚠️ {message.content}
        </div>
      </div>
    );
  }

  return null;
};









