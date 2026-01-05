/**
 * 前端日志系统
 * 将日志保存到 localStorage，并可以导出为文件
 */

class FrontendLogger {
  constructor() {
    this.logs = [];
    this.maxLogs = 1000; // 最多保存1000条日志
    this.loadLogs();

    // 拦截 console 方法
    this.interceptConsole();
  }

  // 加载已保存的日志
  loadLogs() {
    try {
      const saved = localStorage.getItem('frontend_logs');
      if (saved) {
        this.logs = JSON.parse(saved);
      }
    } catch (e) {
      console.error('Failed to load logs:', e);
    }
  }

  // 保存日志到 localStorage
  saveLogs() {
    try {
      // 只保留最近的 maxLogs 条日志
      if (this.logs.length > this.maxLogs) {
        this.logs = this.logs.slice(-this.maxLogs);
      }
      localStorage.setItem('frontend_logs', JSON.stringify(this.logs));
    } catch (e) {
      console.error('Failed to save logs:', e);
    }
  }

  // 添加日志
  log(level, message, data = null) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level: level, // 'info', 'warn', 'error', 'debug'
      message: message,
      data: data
    };

    this.logs.push(logEntry);
    this.saveLogs();

    // 同时输出到控制台
    const consoleMethod = console[level] || console.log;
    if (data) {
      consoleMethod(`[${level.toUpperCase()}] ${message}`, data);
    } else {
      consoleMethod(`[${level.toUpperCase()}] ${message}`);
    }

    // 发送到后端（异步，不等待响应）
    this.sendToBackend(logEntry);
  }

  // 发送日志到后端
  async sendToBackend(logEntry) {
    try {
      await fetch('http://localhost:8080/api/frontend-log', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(logEntry)
      });
    } catch (e) {
      // 静默失败，避免日志系统本身产生错误
    }
  }

  info(message, data) {
    this.log('info', message, data);
  }

  warn(message, data) {
    this.log('warn', message, data);
  }

  error(message, data) {
    this.log('error', message, data);
  }

  debug(message, data) {
    this.log('debug', message, data);
  }

  // WebSocket 消息日志
  wsMessage(type, content) {
    let preview = content;
    if (typeof content === 'string' && content.length > 100) {
      preview = content.substring(0, 100) + '...';
    }
    this.info(`[WebSocket] ${type}`, preview);
  }

  // 用户操作日志
  userAction(action, details) {
    this.info(`[用户操作] ${action}`, details);
  }

  // 清空日志
  clear() {
    this.logs = [];
    localStorage.removeItem('frontend_logs');
  }

  // 导出日志为 JSON 文件
  exportToFile() {
    const date = new Date().toISOString().split('T')[0].replace(/-/g, '');
    const filename = `${date}-frontend-logs.json`;

    const dataStr = JSON.stringify(this.logs, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();

    URL.revokeObjectURL(url);
    this.info('日志已导出', { filename, count: this.logs.length });
  }

  // 获取最近的日志
  getRecentLogs(count = 100) {
    return this.logs.slice(-count);
  }

  // 拦截 console 方法，自动记录
  interceptConsole() {
    const self = this;
    const originalConsole = {
      log: console.log,
      info: console.info,
      warn: console.warn,
      error: console.error
    };

    // 只记录错误和警告到日志系统
    // 使用标志防止递归
    let _isLogging = false;

    console.error = function(...args) {
      originalConsole.error.apply(console, args);

      // 防止递归
      if (_isLogging) return;
      _isLogging = true;

      try {
        const message = args.map(arg => {
          if (typeof arg === 'object') {
            try {
              return JSON.stringify(arg);
            } catch (e) {
              return String(arg);
            }
          }
          return String(arg);
        }).join(' ');
        self.log('error', message, args.length > 1 ? args : null);
      } finally {
        _isLogging = false;
      }
    };

    console.warn = function(...args) {
      originalConsole.warn.apply(console, args);

      // 防止递归
      if (_isLogging) return;
      _isLogging = true;

      try {
        const message = args.map(arg => String(arg)).join(' ');
        self.log('warn', message, args.length > 1 ? args : null);
      } finally {
        _isLogging = false;
      }
    };
  }
}

// 创建全局实例
const logger = new FrontendLogger();

export default logger;
