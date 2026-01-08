/**
 * ThoughtProcess 组件 - 显示 AI 的思考过程
 * 
 * 复刻自 sophia-pro 项目的 Thought Process 显示功能
 */

import React, { useState, useEffect } from 'react';
import { ChevronDown, Brain, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

/**
 * ThoughtProcess 组件
 * 
 * @param {Object} props
 * @param {string} props.content - 思考内容
 * @param {boolean} props.isStreaming - 是否正在流式输出
 * @param {boolean} props.defaultExpanded - 默认是否展开
 * @param {string} props.className - CSS 类名
 */
export default function ThoughtProcess({
  content,
  isStreaming = false,
  defaultExpanded = true,
  className = '',
}) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  
  // 如果没有内容，不显示
  if (!content || !content.trim()) {
    return null;
  }
  
  const triggerText = isStreaming ? 'Thinking...' : 'Thought Process';
  
  return (
    <div className={`thinking-message rounded-lg px-0 py-1 mb-2 ${className}`}>
      <div className="bg-gradient-to-br from-violet-50/50 to-purple-50/50 border border-violet-100 rounded-2xl rounded-tl-none shadow-sm">
        <div
          className="p-4 cursor-pointer"
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-violet-700">
              <Brain size={16} className="text-violet-500" />
              <span className="text-xs font-semibold uppercase tracking-wide text-violet-500">
                {triggerText}
              </span>
              {isStreaming && (
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                  <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                  <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                </div>
              )}
            </div>
            <div className={`transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}>
              <ChevronDown size={16} className="text-violet-500 opacity-60" />
            </div>
          </div>
        </div>
        
        {expanded && (
          <div className="px-4 pb-4 border-t border-violet-100 pt-3">
            <div className="text-xs leading-relaxed text-neutral-600">
              <ReactMarkdown className="prose prose-xs max-w-none text-violet-700">
                {content}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}





