/**
 * ResponseStream 组件 - 流式输出和打字机效果
 *
 * 复刻自 sophia-pro 项目的流式输出功能，支持：
 * - 流式文本输出
 * - 打字机效果
 * - 淡入效果
 * - 暂停/恢复功能
 * - AsyncIterable 流式输入
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';

/**
 * useTextStream Hook 的配置选项
 */
export interface UseTextStreamOptions {
  /** 文本流（字符串或异步迭代器） */
  textStream: string | AsyncIterable<string>;
  /** 速度（1-100，默认20） */
  speed?: number;
  /** 显示模式：打字机或淡入 */
  mode?: 'typewriter' | 'fade';
  /** 完成回调函数 */
  onComplete?: () => void;
}

/**
 * useTextStream Hook 的返回值
 */
export interface UseTextStreamResult {
  /** 当前显示的文本 */
  displayedText: string;
  /** 是否完成 */
  isComplete: boolean;
  /** 段落数组（用于淡入模式） */
  segments: Array<{ text: string; index: number }>;
  /** 重置函数 */
  reset: () => void;
  /** 暂停函数 */
  pause?: () => void;
  /** 恢复函数 */
  resume?: () => void;
}

/**
 * useTextStream Hook - 处理文本流式输出
 *
 * @param options - 配置选项
 * @returns 流式输出状态和控制函数
 *
 * @example
 * ```tsx
 * const { displayedText, isComplete } = useTextStream({
 *   textStream: 'Hello World',
 *   speed: 20,
 *   mode: 'typewriter',
 *   onComplete: () => console.log('Done!')
 * });
 * ```
 */
export function useTextStream({
  textStream,
  speed = 20,
  mode = 'typewriter',
  onComplete,
}: UseTextStreamOptions): UseTextStreamResult {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const [segments, setSegments] = useState<Array<{ text: string; index: number }>>([]);

  const speedRef = useRef(speed);
  const modeRef = useRef(mode);
  const currentIndexRef = useRef(0);
  const animationRef = useRef<number | null>(null);
  const streamRef = useRef<AbortController | null>(null);
  const completedRef = useRef(false);
  const onCompleteRef = useRef(onComplete);
  const isPausedRef = useRef(false);
  // 用于跟踪增量更新的 refs
  const prevTextLengthRef = useRef(0);  // 之前的文本长度，用于检测增量更新
  const fullTextRef = useRef('');       // 完整的目标文本，用于增量更新时的打字机效果

  useEffect(() => {
    speedRef.current = speed;
    modeRef.current = mode;
  }, [speed, mode]);

  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  // 计算每次处理的字符数
  const getChunkSize = useCallback(() => {
    const normalizedSpeed = Math.min(100, Math.max(1, speedRef.current));
    if (modeRef.current === 'typewriter') {
      if (normalizedSpeed < 25) return 1;
      return Math.max(1, Math.round((normalizedSpeed - 25) / 10));
    }
    return 1;
  }, []);

  // 计算处理延迟
  const getProcessingDelay = useCallback(() => {
    const normalizedSpeed = Math.min(100, Math.max(1, speedRef.current));
    return Math.max(1, Math.round(100 / Math.sqrt(normalizedSpeed)));
  }, []);

  // 更新段落（用于淡入模式）
  const updateSegments = useCallback((text: string) => {
    if (modeRef.current === 'fade') {
      try {
        // 使用简单的空格分割作为段落
        const newSegments = text
          .split(/(\s+)/)
          .filter(Boolean)
          .map((word, index) => ({
            text: word,
            index,
          }));
        setSegments(newSegments);
      } catch (error) {
        console.error('Error updating segments:', error);
      }
    }
  }, []);

  const markComplete = useCallback(() => {
    if (!completedRef.current) {
      completedRef.current = true;
      setIsComplete(true);
      onCompleteRef.current?.();
    }
  }, []);

  const reset = useCallback(() => {
    currentIndexRef.current = 0;
    setDisplayedText('');
    setSegments([]);
    setIsComplete(false);
    completedRef.current = false;
    isPausedRef.current = false;
    prevTextLengthRef.current = 0;
    fullTextRef.current = '';

    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
  }, []);

  const pause = useCallback(() => {
    isPausedRef.current = true;
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
  }, []);

  const resume = useCallback(() => {
    if (isPausedRef.current && typeof textStream === 'string') {
      isPausedRef.current = false;
      processStringTypewriter(textStream);
    }
  }, [textStream]);

  // 处理字符串的打字机效果（支持增量更新）
  const processStringTypewriter = useCallback((text: string, isIncremental: boolean = false) => {
    // 如果已经有动画在运行，增量更新时不要重新开始（让当前动画继续使用最新文本）
    if (isIncremental && animationRef.current) {
      // 更新目标文本，当前运行的 streamContent 会使用 fullTextRef.current
      return;
    }

    let lastFrameTime = 0;

    const streamContent = (timestamp: number) => {
      if (isPausedRef.current) {
        return;
      }

      // 使用最新的文本（支持动态变化）
      // 如果是增量更新，始终使用 fullTextRef.current，否则使用传入的 text
      const currentText = isIncremental ? fullTextRef.current : text;

      const delay = getProcessingDelay();
      if (delay > 0 && timestamp - lastFrameTime < delay) {
        animationRef.current = requestAnimationFrame(streamContent);
        return;
      }
      lastFrameTime = timestamp;

      // 如果当前索引已经达到或超过文本长度
      if (currentIndexRef.current >= currentText.length) {
        // 如果是增量更新，检查是否有新内容
        if (isIncremental) {
          const latestText = fullTextRef.current;
          if (latestText.length > currentIndexRef.current) {
            // 有新内容，继续打字（使用最新文本）
            animationRef.current = requestAnimationFrame(streamContent);
            return;
          }
        }
        // 没有新内容了，标记完成
        markComplete();
        return;
      }

      // 继续打字
      const chunkSize = getChunkSize();
      const endIndex = Math.min(
        currentIndexRef.current + chunkSize,
        currentText.length
      );
      const newDisplayedText = currentText.slice(0, endIndex);

      setDisplayedText(newDisplayedText);
      if (modeRef.current === 'fade') {
        updateSegments(newDisplayedText);
      }

      currentIndexRef.current = endIndex;

      // 继续下一帧
      animationRef.current = requestAnimationFrame(streamContent);
    };

    // 启动动画
    animationRef.current = requestAnimationFrame(streamContent);
  }, [getProcessingDelay, getChunkSize, updateSegments, markComplete]);

  // 处理异步迭代器（流式输入）
  const processAsyncIterable = useCallback(async (stream: AsyncIterable<string>) => {
    const controller = new AbortController();
    streamRef.current = controller;

    let displayed = '';

    try {
      for await (const chunk of stream) {
        if (controller.signal.aborted || isPausedRef.current) return;

        displayed += chunk;
        setDisplayedText(displayed);
        updateSegments(displayed);
      }

      markComplete();
    } catch (error) {
      console.error('Error processing text stream:', error);
      markComplete();
    }
  }, [updateSegments, markComplete]);

  const startStreaming = useCallback(() => {
    if (typeof textStream === 'string') {
      // 检查是否是增量更新（流式传输）
      // 增量更新：新长度 > 旧长度 且 旧长度 > 0
      const isIncremental = textStream.length > prevTextLengthRef.current && prevTextLengthRef.current > 0;

      // 更新目标文本
      fullTextRef.current = textStream;

      if (isIncremental) {
        // 增量更新：只更新目标文本，继续打字机效果
        // 如果还没有开始打字机效果，现在开始
        if (!animationRef.current && !completedRef.current) {
          processStringTypewriter(textStream, true);
        }
        // 如果打字机效果已经完成但文本还在增长，继续打字
        if (completedRef.current && textStream.length > currentIndexRef.current) {
          setIsComplete(false);
          completedRef.current = false;
          // 不要重置 currentIndexRef，继续从当前位置打字
          if (!animationRef.current) {
            processStringTypewriter(textStream, true);
          }
        }
        // 更新长度记录
        prevTextLengthRef.current = textStream.length;
      } else {
        // 全新文本：重置并开始打字机效果
        if (textStream.length > 0 && prevTextLengthRef.current === 0) {
          // 从空字符串变为有内容，重置并开始
          reset();
          processStringTypewriter(textStream, false);
          prevTextLengthRef.current = textStream.length;
        } else if (textStream.length === 0 && prevTextLengthRef.current > 0) {
          // 从有内容变为空，可能是消息完成，不重置，让打字机效果继续完成
          // 不执行任何操作，让打字机效果自然完成
          prevTextLengthRef.current = 0;
        } else if (textStream.length < prevTextLengthRef.current) {
          // 文本变短：重置
          reset();
          prevTextLengthRef.current = textStream.length;
        } else if (textStream.length === prevTextLengthRef.current && textStream.length > 0) {
          // 文本长度不变但内容可能变了，需要重新开始（比如 canStartResponseTypewriter 从 false 变为 true）
          reset();
          processStringTypewriter(textStream, false);
          prevTextLengthRef.current = textStream.length;
        } else {
          prevTextLengthRef.current = textStream.length;
        }
      }
    } else if (textStream) {
      reset();
      processAsyncIterable(textStream);
    }
  }, [textStream, reset, processStringTypewriter, processAsyncIterable]);

  useEffect(() => {
    startStreaming();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (streamRef.current) {
        streamRef.current.abort();
      }
    };
  }, [textStream, startStreaming]);

  return {
    displayedText,
    isComplete,
    segments,
    reset,
    pause,
    resume,
  };
}

/**
 * ResponseStream 组件的 Props
 */
export interface ResponseStreamProps {
  /** 文本流（字符串或异步迭代器） */
  textStream: string | AsyncIterable<string>;
  /** 显示模式：打字机或淡入 */
  mode?: 'typewriter' | 'fade';
  /** 速度（1-100，默认20） */
  speed?: number;
  /** CSS 类名 */
  className?: string;
  /** 完成回调函数 */
  onComplete?: () => void;
  /** 渲染的 HTML 标签 */
  as?: keyof JSX.IntrinsicElements;
}

/**
 * ResponseStream 组件 - 流式文本显示组件
 *
 * 支持打字机效果和淡入效果两种模式
 *
 * @param props - 组件属性
 * @returns React 组件
 *
 * @example
 * ```tsx
 * <ResponseStream
 *   textStream="Hello World"
 *   mode="typewriter"
 *   speed={20}
 *   onComplete={() => console.log('Done!')}
 * />
 * ```
 */
export default function ResponseStream({
  textStream,
  mode = 'typewriter',
  speed = 20,
  className = '',
  onComplete,
  as: Container = 'div',
}: ResponseStreamProps) {
  const {
    displayedText,
    isComplete,
    segments,
  } = useTextStream({
    textStream,
    speed,
    mode,
    onComplete,
  });

  useEffect(() => {
    if (isComplete && onComplete) {
      onComplete();
    }
  }, [isComplete, onComplete]);

  // 淡入样式
  const fadeStyle = `
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    .fade-segment {
      display: inline-block;
      opacity: 0;
      animation: fadeIn 300ms ease-out forwards;
    }

    .fade-segment-space {
      white-space: pre;
    }
  `;

  const renderContent = () => {
    switch (mode) {
      case 'typewriter':
        return <>{displayedText}</>;

      case 'fade':
        return (
          <>
            <style>{fadeStyle}</style>
            <div className="relative">
              {segments.map((segment, idx) => {
                const isWhitespace = /^\s+$/.test(segment.text);

                return (
                  <span
                    key={`${segment.text}-${idx}`}
                    className={`fade-segment ${isWhitespace ? 'fade-segment-space' : ''}`}
                    style={{
                      animationDelay: `${idx * 50}ms`,
                    }}
                  >
                    {segment.text}
                  </span>
                );
              })}
            </div>
          </>
        );

      default:
        return <>{displayedText}</>;
    }
  };

  return React.createElement(Container, { className }, renderContent());
}

