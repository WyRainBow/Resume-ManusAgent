/**
 * SophiaChat - 复刻 sophia-pro 风格的对话页面
 *
 * 使用 SSE (Server-Sent Events) 替代 WebSocket
 *
 * 功能：
 * - AI 输出的 Thought Process（来自后端，折叠面板样式）
 * - 流式输出和打字机效果
 * - Markdown 渲染
 * - 心跳检测和自动重连
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ArrowUp } from 'lucide-react';
import ChatMessage from '@/components/chat/ChatMessage';
import { Message } from '@/types/chat';
import { SSETransport, SSEEvent, createSSETransport } from '@/transports/SSETransport';
import { ConnectionStatus, normalizeSSEEvent, SSEMessage } from '@/types/transport';

// ============================================================================
// 配置
// ============================================================================

const SSE_CONFIG = {
  BASE_URL: 'http://localhost:8080',
  HEARTBEAT_TIMEOUT: 60000,  // 60 seconds
};

// ============================================================================
// 主页面组件
// ============================================================================

export default function SophiaChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [status, setStatus] = useState<ConnectionStatus>('idle');
  const [currentThought, setCurrentThought] = useState('');
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const transportRef = useRef<SSETransport | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const isFinalizedRef = useRef(false);
  const shouldFinalizeRef = useRef(false); // 标记是否需要完成（等待打字机效果完成）

  // Initialize SSE transport
  useEffect(() => {
    const transport = createSSETransport({
      baseUrl: SSE_CONFIG.BASE_URL,
      heartbeatTimeout: SSE_CONFIG.HEARTBEAT_TIMEOUT,
      onConnect: () => {
        console.log('[SophiaChat] SSE Connected');
      },
      onDisconnect: () => {
        console.log('[SophiaChat] SSE Disconnected');
        // 不在 disconnect 时自动 finalize，让正常的完成流程处理
        // 避免重复调用 finalizeMessage
      },
      onError: (error) => {
        console.error('[SophiaChat] SSE Error:', error);
        setStatus('idle');
        setIsProcessing(false);
      },
    });

    // Add message listener
    transport.onMessage((event: SSEEvent) => {
      handleSSEEvent(event);
    });

    // Add error listener
    transport.onError((error: Error) => {
      console.error('[SophiaChat] Transport error:', error);
    });

    transportRef.current = transport;

    // Set initial status to ready
    setStatus('idle');

    return () => {
      transport.disconnect();
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentThought, currentAnswer]);

  /**
   * Handle SSE events from backend
   */
  const handleSSEEvent = useCallback((event: SSEEvent) => {
    console.log('[SophiaChat] Received:', event.type, event);

    // Convert to normalized format for compatibility
    const normalized = normalizeSSEEvent(event as unknown as SSEMessage);

    switch (normalized.type) {
      case 'thought':
        // Thought 事件通常是完整的，直接替换而不是追加（避免重复）
        setCurrentThought(normalized.content || '');
        break;

      case 'answer':
        setCurrentAnswer(prev => {
          // 如果是完整的 answer 事件，直接替换而不是追加（避免重复）
          // 否则追加内容（流式传输）
          const newAnswer = normalized.is_complete
            ? (normalized.content || '')
            : (prev + (normalized.content || ''));

          // 如果 answer 事件标记为完成，标记需要完成
          // 但不立即调用 finalizeMessage，等待打字机效果完成
          if (normalized.is_complete) {
            shouldFinalizeRef.current = true;
            // 添加超时保护：如果打字机效果没有开始或完成，在合理时间后强制完成
            // 根据内容长度计算超时时间（每100字符1秒，最少5秒，最多15秒）
            const timeout = Math.min(15000, Math.max(5000, (newAnswer.length / 100) * 1000));
            setTimeout(() => {
              if (shouldFinalizeRef.current && !isFinalizedRef.current) {
                console.log('[SophiaChat] 打字机效果超时，强制完成消息');
                shouldFinalizeRef.current = false;
                finalizeMessage();
              }
            }, timeout);
          }
          return newAnswer;
        });
        break;

      case 'status':
        if (normalized.content === 'processing') {
          setIsProcessing(true);
          setStatus('processing');
        } else if (normalized.content === 'complete' || normalized.content === 'stopped') {
          // 标记需要完成，等待打字机效果完成
          shouldFinalizeRef.current = true;
        }
        break;

      case 'agent_end':
        // Agent 执行结束，标记需要完成，等待打字机效果完成
        shouldFinalizeRef.current = true;
        break;

      case 'agent_start':
      case 'system':
        // 这些事件不需要特殊处理，只是记录
        break;

      case 'error':
        console.error('[SophiaChat] Agent error:', normalized.content);
        setIsProcessing(false);
        setStatus('idle');
        break;
    }
  }, []);

  /**
   * Finalize current message and add to history
   */
  const finalizeMessage = useCallback(() => {
    // 防止重复调用
    if (isFinalizedRef.current) {
      console.log('[SophiaChat] finalizeMessage already called, skipping');
      return;
    }

    isFinalizedRef.current = true;

    // 使用函数式更新获取最新状态值
    setCurrentThought((prevThought) => {
      const thought = prevThought.trim();
      setCurrentAnswer((prevAnswer) => {
        const answer = prevAnswer.trim();

        // 检查是否有内容需要保存
        if (!thought && !answer) {
          // 没有内容，只重置状态，不添加到消息列表
          console.log('[SophiaChat] No content to finalize, just resetting state');
          setIsProcessing(false);
          setStatus('idle');
          // 延迟重置标志，允许下一次消息
          setTimeout(() => {
            isFinalizedRef.current = false;
          }, 100);
          return '';
        }

        // 使用更唯一的 ID：时间戳 + 随机数
        const uniqueId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        // 添加到消息列表
        // 确保至少有一个内容（thought 或 answer）
        if (thought || answer) {
          const newMessage: Message = {
            id: uniqueId,
            role: 'assistant',
            content: answer || '',
            timestamp: new Date().toISOString(),
          };
          if (thought) {
            newMessage.thought = thought;
          }
          setMessages((prev) => [...prev, newMessage]);
        }

        // 立即重置状态，避免重复显示
        setIsProcessing(false);
        setStatus('idle');

        // 延迟重置标志，允许下一次消息
        setTimeout(() => {
          isFinalizedRef.current = false;
        }, 100);

        return '';
      });
      return '';
    });
  }, []);

  /**
   * Send message to backend via SSE
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userMessage = input.trim();
    const uniqueId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Add user message to UI
    setMessages(prev => [...prev, {
      id: uniqueId,
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    }]);

    // Reset state for new message
    setCurrentThought('');
    setCurrentAnswer('');
    setIsProcessing(true);
    setStatus('processing');
    isFinalizedRef.current = false;
    shouldFinalizeRef.current = false; // 重置完成标记
    setInput('');

    // Send via SSE
    if (transportRef.current) {
      try {
        await transportRef.current.send(userMessage);
      } catch (error) {
        console.error('[SophiaChat] Failed to send message:', error);
        setIsProcessing(false);
        setStatus('idle');
      }
    }
  };

  /**
   * Clear conversation
   */
  const handleClearConversation = () => {
    setMessages([]);
    setCurrentThought('');
    setCurrentAnswer('');
    transportRef.current?.clearConversation();
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-orange-50 to-white">
      {/* Header */}
      <header className="border-b border-gray-100 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-semibold text-gray-800">
              SophiaPro Chat
            </h1>
            <p className="text-sm text-gray-500">
              Thought Process · Streaming · Markdown · SSE
            </p>
          </div>
          <button
            onClick={handleClearConversation}
            className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1 rounded border border-gray-200 hover:border-gray-300 transition-colors"
          >
            Clear
          </button>
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
            <p className="text-gray-300 text-xs mt-4">
              使用 SSE (Server-Sent Events) 传输
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
            onTypewriterComplete={() => {
              // 打字机效果完成时，如果标记了需要完成，则调用 finalizeMessage
              if (shouldFinalizeRef.current) {
                shouldFinalizeRef.current = false;
                finalizeMessage();
              }
            }}
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
            <span className="animate-bounce" style={{ animationDelay: '300ms' }}>Thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* Input Area */}
      <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-white via-white to-transparent pt-6 pb-6">
        <div className="max-w-4xl mx-auto px-6">
          <form onSubmit={handleSubmit}>
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden flex items-center">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="输入消息..."
                className="flex-1 px-4 py-3 outline-none text-gray-700 placeholder-gray-400 bg-transparent"
                disabled={isProcessing}
              />
              <div className="pr-2 py-2">
                <button
                  type="submit"
                  disabled={!input.trim() || isProcessing}
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center
                    transition-all duration-200
                    ${!input.trim() || isProcessing
                      ? 'bg-gray-200 cursor-not-allowed'
                      : 'bg-gradient-to-br from-orange-500 via-orange-600 to-orange-700 hover:from-orange-600 hover:via-orange-700 hover:to-orange-800 shadow-sm hover:shadow-md'
                    }
                  `}
                  title="发送消息"
                >
                  <ArrowUp
                    className={`w-5 h-5 ${!input.trim() || isProcessing
                      ? 'text-gray-400'
                      : 'text-white'
                      }`}
                  />
                </button>
              </div>
            </div>
          </form>

          {/* Status */}
          <div className="text-center mt-3 text-xs text-gray-400">
            <span className={`inline-flex items-center gap-1.5 ${status === 'idle' ? 'text-green-500' :
              status === 'processing' ? 'text-orange-500' : 'text-gray-400'
              }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${status === 'idle' ? 'bg-green-500' :
                status === 'processing' ? 'bg-orange-500 animate-pulse' : 'bg-gray-400'
                }`}></span>
              {status === 'idle' ? 'Ready (SSE)' : status === 'processing' ? 'Processing...' : 'Connecting...'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
