/**
 * ResponseStream 组件 - 流式输出和打字机效果
 * 
 * 复刻自 sophia-pro 项目的流式输出功能，支持：
 * - 流式文本输出
 * - 打字机效果
 * - 淡入效果
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';

/**
 * useTextStream Hook - 处理文本流式输出
 * 
 * @param {string|AsyncIterable<string>} textStream - 文本流（字符串或异步迭代器）
 * @param {number} speed - 速度（1-100，默认20）
 * @param {'typewriter'|'fade'} mode - 模式：打字机或淡入
 * @param {Function} onComplete - 完成回调
 */
export function useTextStream({
  textStream,
  speed = 20,
  mode = 'typewriter',
  onComplete,
}) {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const [segments, setSegments] = useState([]);
  
  const speedRef = useRef(speed);
  const modeRef = useRef(mode);
  const currentIndexRef = useRef(0);
  const animationRef = useRef(null);
  const streamRef = useRef(null);
  const completedRef = useRef(false);
  const onCompleteRef = useRef(onComplete);
  
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
  const updateSegments = useCallback((text) => {
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
    
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
  }, []);
  
  // 处理字符串的打字机效果
  const processStringTypewriter = useCallback((text) => {
    let lastFrameTime = 0;
    
    const streamContent = (timestamp) => {
      const delay = getProcessingDelay();
      if (delay > 0 && timestamp - lastFrameTime < delay) {
        animationRef.current = requestAnimationFrame(streamContent);
        return;
      }
      lastFrameTime = timestamp;
      
      if (currentIndexRef.current >= text.length) {
        markComplete();
        return;
      }
      
      const chunkSize = getChunkSize();
      const endIndex = Math.min(
        currentIndexRef.current + chunkSize,
        text.length
      );
      const newDisplayedText = text.slice(0, endIndex);
      
      setDisplayedText(newDisplayedText);
      if (modeRef.current === 'fade') {
        updateSegments(newDisplayedText);
      }
      
      currentIndexRef.current = endIndex;
      
      if (endIndex < text.length) {
        animationRef.current = requestAnimationFrame(streamContent);
      } else {
        markComplete();
      }
    };
    
    animationRef.current = requestAnimationFrame(streamContent);
  }, [getProcessingDelay, getChunkSize, updateSegments, markComplete]);
  
  // 处理异步迭代器（流式输入）
  const processAsyncIterable = useCallback(async (stream) => {
    const controller = new AbortController();
    streamRef.current = controller;
    
    let displayed = '';
    
    try {
      for await (const chunk of stream) {
        if (controller.signal.aborted) return;
        
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
    reset();
    
    if (typeof textStream === 'string') {
      processStringTypewriter(textStream);
    } else if (textStream) {
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
  };
}

/**
 * ResponseStream 组件
 * 
 * @param {string|AsyncIterable<string>} textStream - 文本流
 * @param {'typewriter'|'fade'} mode - 显示模式
 * @param {number} speed - 速度（1-100）
 * @param {string} className - CSS 类名
 * @param {Function} onComplete - 完成回调
 * @param {string} as - 渲染的 HTML 标签
 */
export default function ResponseStream({
  textStream,
  mode = 'typewriter',
  speed = 20,
  className = '',
  onComplete,
  as: Container = 'div',
}) {
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





