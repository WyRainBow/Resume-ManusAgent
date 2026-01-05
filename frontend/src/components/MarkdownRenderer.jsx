import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
// highlight.js 样式已通过 rehype-highlight 自动加载，如需自定义可导入其他主题

/**
 * 移除文本中的 emoji
 */
const removeEmojis = (text) => {
  // 匹配各种 emoji Unicode 范围
  const emojiRegex = /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F600}-\u{1F64F}]|[\u{1F680}-\u{1F6FF}]|[\u{1F900}-\u{1F9FF}]|[\u{1FA00}-\u{1FA6F}]|[\u{1FA70}-\u{1FAFF}]|[\u{200D}]|[\u{FE0F}]/gu;
  return text.replace(emojiRegex, '');
};

/**
 * 修复 Markdown 格式问题
 * 处理 ** text** 或 **text ** 这种空格导致的加粗失效问题
 */
const fixMarkdownFormat = (text) => {
  // 修复 ** text** → **text**
  let fixed = text.replace(/\*\*\s+([^*]+)\*\*/g, '**$1**');
  // 修复 **text ** → **text**
  fixed = fixed.replace(/\*\*([^*]+)\s+\*\*/g, '**$1**');
  // 移除加粗标记内的首尾空格
  fixed = fixed.replace(/\*\*\s*([^*]+?)\s*\*\*/g, '**$1**');
  return fixed;
};

/**
 * 统一的 Markdown 渲染组件
 * 支持 GFM（表格、任务列表等）和代码高亮
 */
const MarkdownRenderer = ({
  content,
  className = '',
  size = 'sm', // 'xs' | 'sm' | 'base'
  variant = 'default', // 'default' | 'compact' | 'greeting'
  removeEmoji = false // 是否移除 emoji
}) => {
  // 处理内容：移除 emoji（如果需要）并修复 Markdown 格式问题
  let processedContent = content;
  if (removeEmoji) {
    processedContent = removeEmojis(processedContent);
  }
  // 总是修复 Markdown 格式问题
  processedContent = fixMarkdownFormat(processedContent);
  // 根据 size 设置基础样式
  const sizeClasses = {
    xs: 'prose-xs',
    sm: 'prose-sm',
    base: 'prose'
  };

  // 根据 variant 设置样式变体
  const variantClasses = {
    default: `
      prose-headings:text-gray-900 prose-headings:font-bold
      prose-h1:text-xl prose-h2:text-lg prose-h3:text-base
      prose-p:text-gray-700 prose-p:leading-relaxed prose-p:mb-3
      prose-strong:text-gray-900 prose-strong:font-semibold
      prose-ul:list-disc prose-ul:ml-6 prose-ul:mb-3
      prose-ol:list-decimal prose-ol:ml-6 prose-ol:mb-3
      prose-li:text-gray-700 prose-li:mb-1
      prose-code:text-sm prose-code:bg-gray-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:font-mono prose-code:text-gray-800
      prose-pre:bg-gray-50 prose-pre:text-gray-900 prose-pre:border prose-pre:border-gray-200 prose-pre:rounded-lg prose-pre:p-4 prose-pre:overflow-x-auto
      prose-blockquote:border-l-4 prose-blockquote:border-gray-300 prose-blockquote:pl-4 prose-blockquote:italic prose-blockquote:text-gray-600
      prose-a:text-indigo-600 prose-a:underline hover:prose-a:text-indigo-800
      prose-table:border-collapse prose-table:w-full prose-table:my-4
      prose-th:border prose-th:border-gray-300 prose-th:bg-gray-100 prose-th:px-4 prose-th:py-2 prose-th:text-left prose-th:font-semibold
      prose-td:border prose-td:border-gray-300 prose-td:px-4 prose-td:py-2
    `,
    compact: `
      prose-headings:text-gray-900 prose-headings:font-bold prose-headings:mt-3 prose-headings:mb-2
      prose-h1:text-base prose-h2:text-sm prose-h3:text-xs
      prose-p:text-gray-700 prose-p:leading-relaxed prose-p:mb-2 prose-p:text-xs
      prose-strong:text-gray-900 prose-strong:font-semibold
      prose-ul:list-disc prose-ul:ml-3 prose-ul:mb-2 prose-ul:text-xs prose-ul:space-y-0.5
      prose-ol:list-decimal prose-ol:ml-3 prose-ol:mb-2 prose-ol:text-xs prose-ol:space-y-0.5
      prose-li:text-gray-700 prose-li:mb-1
      prose-code:text-xs prose-code:bg-gray-200 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-gray-800
      prose-blockquote:border-l-4 prose-blockquote:border-gray-300 prose-blockquote:pl-3 prose-blockquote:italic prose-blockquote:text-xs
      prose-a:text-indigo-600 prose-a:underline hover:prose-a:text-indigo-800
    `,
    greeting: `
      prose-headings:font-bold prose-headings:text-indigo-900
      prose-a:text-indigo-700
    `
  };

  return (
    <ReactMarkdown
      className={`prose ${sizeClasses[size]} max-w-none ${variantClasses[variant]} ${className}`}
      remarkPlugins={[remarkGfm]} // 启用 GFM 支持（表格、任务列表等）
      rehypePlugins={[rehypeHighlight]} // 启用代码高亮
      components={{
        // 自定义占位符样式
        p: ({ node, children, ...props }) => {
          const text = String(children);
          if (text.includes('summary') || text.includes('keywords') || text.match(/^[a-z_]+$/)) {
            return (
              <div className="bg-gray-100 border border-gray-300 rounded px-3 py-2 my-2 inline-block">
                <code className="text-gray-800 text-sm">{text}</code>
              </div>
            );
          }
          return <p {...props}>{children}</p>;
        },
        // 确保 strong 标签正确渲染
        strong: ({ node, children, ...props }) => {
          return <strong className="font-semibold text-gray-900" {...props}>{children}</strong>;
        },
        // 自定义代码块容器
        code: ({ node, inline, className, children, ...props }) => {
          const match = /language-(\w+)/.exec(className || '');
          return !inline && match ? (
            <code className={className} {...props}>
              {children}
            </code>
          ) : (
            <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800" {...props}>
              {children}
            </code>
          );
        }
      }}
    >
      {processedContent}
    </ReactMarkdown>
  );
};

export default MarkdownRenderer;

