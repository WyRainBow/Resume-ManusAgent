/**
 * ChatMessage 组件 - 对话消息显示
 *
 * 复刻自 sophia-pro 风格的对话消息组件
 * 支持用户消息和助手消息，包含 Thought Process 和 Markdown 渲染
 */

import React from 'react';
import { ChatMessageProps } from '@/types/chat';
import ThoughtProcess from './ThoughtProcess';
import EnhancedMarkdown from './EnhancedMarkdown';
import { useTextStream } from './ResponseStream';

/**
 * ChatMessage 组件 - 对话消息显示组件
 *
 * 支持用户消息和助手消息两种类型
 * 助手消息支持 Thought Process 显示和打字机效果
 *
 * @param props - 组件属性
 * @returns React 组件
 *
 * @example
 * ```tsx
 * <ChatMessage
 *   message={{
 *     role: 'assistant',
 *     content: 'Hello!',
 *     thought: 'Thinking...'
 *   }}
 *   isLatest={true}
 *   isStreaming={true}
 * />
 * ```
 */
export default function ChatMessage({ message, isLatest = false, isStreaming = false }: ChatMessageProps) {
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
  const shouldUseTypewriter = message.role === 'assistant' && isLatest && isStreaming;
  const { displayedText, isComplete } = useTextStream({
    textStream: shouldUseTypewriter ? message.content : '',
    speed: 20,
    mode: 'typewriter',
  });

  const textToShow = shouldUseTypewriter ? displayedText : message.content;

  return (
    <div className="mb-6">
      {/* Thought Process（如果有）- 复刻 sophia-pro 样式 */}
      {message.thought && (
        <ThoughtProcess
          content={message.thought}
          isStreaming={isLatest && isStreaming && !message.content}
          isLatest={isLatest}
          defaultExpanded={true}
        />
      )}

      {/* Response 内容 */}
      {textToShow && (
        <div className="text-gray-800">
          <EnhancedMarkdown>{textToShow}</EnhancedMarkdown>
          {shouldUseTypewriter && !isComplete && (
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

