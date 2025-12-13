import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import './index.css'
import './App.css'

const API_URL = 'http://localhost:8000'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [userId] = useState('user_' + Math.random().toString(36).substr(2, 9))
  const [stats, setStats] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_URL}/user/${userId}/stats`)
        setStats(response.data)
      } catch (error) {
        console.error('Error fetching stats:', error)
      }
    }, 5000)
    return () => clearInterval(interval)
  }, [userId])

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await axios.post(`${API_URL}/chat`, {
        user_id: userId,
        message: input,
        conversation_history: messages
      })

      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        sentiment: response.data.sentiment,
        next_action: response.data.next_action,
        sources: response.data.sources
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Full error object:', error)
      console.error('Error response:', error.response)
      console.error('Error message:', error.message)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.response?.data?.detail || error.message || 'Unknown error'}`
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="app-container">
      <motion.header
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="glass header"
      >
        <div className="header-content">
          <div>
            <h1 className="gradient-text title">NeuroLearn</h1>
            <p className="subtitle">Your Adaptive AI Tutor</p>
          </div>

          {stats && (
            <div className="stats-container">
              <div className="glass stat-card">
                <p className="stat-label">Mastery</p>
                <p className="stat-value blue">
                  {Math.round(stats.topic_mastery * 100)}%
                </p>
              </div>
              <div className="glass stat-card">
                <p className="stat-label">Quiz Score</p>
                <p className="stat-value purple">
                  {stats.last_quiz_score}
                </p>
              </div>
            </div>
          )}
        </div>
      </motion.header>

      <div className="glass chat-container">
        <div className="messages-area">
          <AnimatePresence>
            {messages.length === 0 && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="welcome-message"
              >
                <div className="welcome-icon">🧠</div>
                <h2 className="welcome-title">Welcome to NeuroLearn!</h2>
                <p className="welcome-text">
                  Ask me anything about Intelligent Systems
                </p>
              </motion.div>
            )}

            {messages.map((msg, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={`message-wrapper ${msg.role}`}
              >
                <div className={`message ${msg.role}`}>
                  <p className="message-content">{msg.content}</p>
                  {msg.next_action && (
                    <div className="message-meta">
                      <span className="next-action">
                        Next: {msg.next_action}
                      </span>
                      {msg.sentiment && (
                        <span className={`sentiment ${msg.sentiment}`}>
                          {msg.sentiment === 'happy' ? '😊' : msg.sentiment === 'frustrated' ? '😟' : '😐'}
                        </span>
                      )}
                    </div>
                  )}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="message-sources">
                      <p className="sources-label">Sources:</p>
                      <div className="sources-list">
                        {msg.sources.map((source, i) => (
                          <div key={i} className="source-item">
                            📄 {source.source} (Page {source.page})
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}

            {loading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="message-wrapper assistant"
              >
                <div className="message assistant">
                  <div className="typing-indicator">
                    <div className="dot bounce"></div>
                    <div className="dot bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="dot bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about Intelligent Systems..."
            className="glass message-input"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="gradient-bg send-button"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

export default App
