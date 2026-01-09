/**
 * EnhancedMarkdown 组件 - 增强的 Markdown 渲染
 *
 * 复刻自 sophia-pro 项目的 Markdown 渲染功能，支持：
 * - 代码高亮
 * - 表格
 * - 链接
 * - 列表
 * - 引用
 */

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import MermaidBlock from './MermaidBlock';

/**
 * 自定义代码渲染器类型
 */
export type CustomCodeRenderer = (code: string) => React.ReactNode;

/**
 * EnhancedMarkdown 组件的 Props
 */
export interface EnhancedMarkdownProps {
  /** Markdown 文本内容 */
  children: string;
  /** CSS 类名 */
  className?: string;
  /** 自定义代码渲染器 */
  customCodeRenderers?: Record<string, CustomCodeRenderer>;
}

/**
 * EnhancedMarkdown 组件 - 增强的 Markdown 渲染组件
 *
 * 支持代码高亮、表格、链接、列表、引用、Mermaid 图表等 Markdown 功能
 *
 * @param props - 组件属性
 * @returns React 组件
 *
 * @example
 * ```tsx
 * <EnhancedMarkdown>
 *   # Hello World
 *   ```python
 *   print("Hello")
 *   ```
 *   ```mermaid
 *   graph TD; A-->B
 *   ```
 * </EnhancedMarkdown>
 * ```
 */
export default function EnhancedMarkdown({
  children,
  className = '',
  customCodeRenderers = {},
}: EnhancedMarkdownProps) {
  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkBreaks]}
        className="prose max-w-none
          prose-headings:text-gray-900 prose-headings:font-bold prose-headings:mt-3 prose-headings:mb-2
          prose-h1:text-base prose-h2:text-sm prose-h3:text-xs
          prose-p:text-gray-700 prose-p:leading-relaxed prose-p:mb-2 prose-p:text-sm
          prose-strong:text-gray-900 prose-strong:font-semibold
          prose-ul:list-disc prose-ul:ml-3 prose-ul:mb-2 prose-ul:text-sm prose-ul:space-y-0.5
          prose-ol:list-decimal prose-ol:ml-3 prose-ol:mb-2 prose-ol:text-sm prose-ol:space-y-0.5
          prose-li:text-gray-700 prose-li:mb-1
          prose-code:text-sm prose-code:bg-gray-200 prose-code:px-1 prose-code:py-0.5 prose-code:rounded
          prose-blockquote:border-l-4 prose-blockquote:border-gray-300 prose-blockquote:pl-3 prose-blockquote:italic prose-blockquote:text-sm
          prose-a:text-indigo-600 prose-a:underline hover:prose-a:text-indigo-800
          prose-table:border-collapse prose-table:border prose-table:border-gray-300
          prose-th:border prose-th:border-gray-300 prose-th:px-2 prose-th:py-1 prose-th:bg-gray-100
          prose-td:border prose-td:border-gray-300 prose-td:px-2 prose-td:py-1"
        components={{
          // 自定义段落样式
          p: ({ node, children, ...props }: any) => {
            const text = String(children);
            // 处理特殊占位符
            if (text.includes('summary') || text.includes('keywords') || text.match(/^[a-z_]+$/)) {
              return (
                <div className="bg-gray-100 border border-gray-300 rounded px-3 py-2 my-2 inline-block">
                  <code className="text-gray-600 text-sm">{text}</code>
                </div>
              );
            }
            return <p {...props}>{children}</p>;
          },
          // 代码块样式（支持语法高亮、Mermaid、自定义渲染器）
          pre: ({ children, ...props }: any) => {
            const codeElement = React.Children.toArray(children)[0] as any;
            if (codeElement?.type === 'code') {
              const { className, children: codeChildren } = codeElement.props;
              const match = /language-(\w+)/.exec(className || '');
              const language = match ? match[1] : 'text';
              const code = String(codeChildren).replace(/\n$/, '');

              // Mermaid 图表支持
              if (language === 'mermaid') {
                return <MermaidBlock code={code} className="mb-4" />;
              }

              // 自定义代码渲染器
              if (language === 'component' && customCodeRenderers[language]) {
                return <>{customCodeRenderers[language](code)}</>;
              }

              // 其他自定义渲染器
              if (customCodeRenderers[language]) {
                return <>{customCodeRenderers[language](code)}</>;
              }

              // 默认代码高亮
              return (
                <div className="relative mb-4">
                  <div className="flex items-center justify-between bg-gray-900 px-4 py-2 rounded-t-lg border-b border-gray-700">
                    <span className="text-xs text-gray-400 font-mono">{language}</span>
                    <button
                      onClick={() => {
                        navigator.clipboard?.writeText(code).catch(() => {});
                      }}
                      className="text-xs text-gray-400 hover:text-gray-200 transition-colors"
                      title="Copy to clipboard"
                    >
                      Copy
                    </button>
                  </div>
                  <SyntaxHighlighter
                    language={language}
                    style={vscDarkPlus}
                    PreTag="div"
                    className="rounded-b-lg"
                    customStyle={{
                      margin: 0,
                      borderRadius: '0 0 0.5rem 0.5rem',
                    }}
                  >
                    {code}
                  </SyntaxHighlighter>
                </div>
              );
            }
            return <pre {...props}>{children}</pre>;
          },
          // 内联代码样式
          code: ({ node, inline, className, children, ...props }: any) => {
            const isInline = inline || !/language-(\w+)/.exec(className || '');

            if (isInline) {
              return (
                <code className="bg-gray-200 rounded-sm px-1 font-mono text-sm" {...props}>
                  {children}
                </code>
              );
            }

            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}

