/**
 * SophiaChat - 复刻 sophia-pro 风格的对话页面
 *
 * 功能：
 * - AI 输出的 Thought Process（来自后端，折叠面板样式）
 * - 流式输出和打字机效果
 * - Markdown 渲染
 */

import React, { useState, useEffect, useRef } from 'react';
import ChatMessage from '@/components/chat/ChatMessage';
import { Message } from '@/types/chat';
import { WebSocketMessage, ConnectionStatus } from '@/types/websocket';

// ============================================================================
// 配置
// ============================================================================

const WS_CONFIG = {
  PORT: 8080,
  PATH: '/ws',
  getUrl: () => `ws://localhost:${WS_CONFIG.PORT}${WS_CONFIG.PATH}`
};

// ============================================================================
// 主页面组件
// ============================================================================

export default function SophiaChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [currentThought, setCurrentThought] = useState('');
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const isFinalizedRef = useRef(false); // 防止 finalizeMessage 被多次调用

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
        const data: WebSocketMessage = JSON.parse(event.data);
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

  const handleMessage = (data: WebSocketMessage) => {
    switch (data.type) {
      case 'thought':
        setCurrentThought(prev => prev + (data.content || ''));
        break;

      case 'answer':
        setCurrentAnswer(prev => prev + (data.content || ''));
        // 如果 answer 事件标记为完成，立即完成消息
        if (data.is_complete) {
          finalizeMessage();
        }
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

      case 'agent_end':
        // Agent 执行结束，完成消息
        finalizeMessage();
        break;

      case 'agent_start':
      case 'system':
        // 这些事件不需要特殊处理，只是记录
        break;

      case 'error':
        setIsProcessing(false);
        setStatus('idle');
        break;
    }
  };

  const finalizeMessage = () => {
    // 防止重复调用
    if (isFinalizedRef.current) {
      console.log('[SophiaChat] finalizeMessage already called, skipping');
      return;
    }
    isFinalizedRef.current = true;

    // 使用 ref 确保获取最新状态值
    setCurrentThought((prevThought) => {
      const thought = prevThought;
      setCurrentAnswer((prevAnswer) => {
        const answer = prevAnswer;
        if (thought || answer) {
          // 使用更唯一的 ID：时间戳 + 随机数
          const uniqueId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
          setMessages((prev) => [
            ...prev,
            {
              id: uniqueId,
              role: 'assistant',
              thought: thought,
              content: answer,
              timestamp: new Date().toISOString(),
            }
          ]);
        }
        // 重置状态
        setIsProcessing(false);
        setStatus('idle');
        return '';
      });
      return '';
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userMessage = input.trim();
    // 使用更唯一的 ID
    const uniqueId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    setMessages(prev => [...prev, {
      id: uniqueId,
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    }]);
    setCurrentThought('');
    setCurrentAnswer('');
    setIsProcessing(true);
    isFinalizedRef.current = false; // 重置防重复标志

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
            key={msg.id || idx}
            message={msg}
            isLatest={idx === messages.length - 1 && msg.role === 'assistant'}
            isStreaming={false}
          />
        ))}

        {/* 当前正在生成的消息 */}
        {isProcessing && (currentThought || currentAnswer) && (
          <ChatMessage
            message={{
              id: 'current',
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

