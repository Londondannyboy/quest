/**
 * Centralized logging utility
 * Replace console.log with structured logging
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

interface LogContext {
  userId?: string
  sessionId?: string
  component?: string
  [key: string]: unknown
}

class Logger {
  private isDevelopment = process.env.NODE_ENV === 'development'
  private logLevel: LogLevel = this.isDevelopment ? 'debug' : 'info'
  
  private shouldLog(level: LogLevel): boolean {
    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error']
    const currentLevelIndex = levels.indexOf(this.logLevel)
    const messageLevelIndex = levels.indexOf(level)
    return messageLevelIndex >= currentLevelIndex
  }
  
  private formatMessage(level: LogLevel, message: string, context?: LogContext): string {
    const timestamp = new Date().toISOString()
    const contextStr = context ? ` ${JSON.stringify(context)}` : ''
    return `[${timestamp}] [${level.toUpperCase()}]${contextStr} ${message}`
  }
  
  debug(message: string, context?: LogContext) {
    if (this.shouldLog('debug')) {
      console.log(this.formatMessage('debug', message, context))
    }
  }
  
  info(message: string, context?: LogContext) {
    if (this.shouldLog('info')) {
      console.log(this.formatMessage('info', message, context))
    }
  }
  
  warn(message: string, context?: LogContext) {
    if (this.shouldLog('warn')) {
      console.warn(this.formatMessage('warn', message, context))
    }
  }
  
  error(message: string, error?: Error | unknown, context?: LogContext) {
    if (this.shouldLog('error')) {
      console.error(this.formatMessage('error', message, context))
      if (error) {
        console.error(error)
      }
    }
  }
  
  // Special logger for audio events
  audio(event: string, data?: unknown) {
    if (this.isDevelopment) {
      console.log(`[AUDIO] ${event}`, data)
    }
  }
  
  // Special logger for WebSocket events
  ws(event: string, data?: unknown) {
    if (this.isDevelopment) {
      console.log(`[WS] ${event}`, data)
    }
  }
}

export const logger = new Logger()