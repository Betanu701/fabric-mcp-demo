/**
 * Chat page component
 */
import React, { useState } from 'react';
import { apiClient } from '../api/client';
import { useTenant } from '../context/TenantContext';

const Chat: React.FC = () => {
  const { tenantId } = useTenant();
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = { role: 'user', content: message };
    setMessages((prev) => [...prev, userMessage]);
    setMessage('');
    setLoading(true);

    try {
      const response = await apiClient.post('/api/chat', {
        message: message,
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.message,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your message.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', padding: '20px' }}>
      <h1>Enterprise MCP Chat</h1>
      <p className="text-secondary">Tenant: {tenantId}</p>

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          marginTop: '20px',
          marginBottom: '20px',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          padding: '16px',
        }}
      >
        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              marginBottom: '12px',
              padding: '12px',
              backgroundColor:
                msg.role === 'user' ? 'var(--color-primary)' : 'var(--color-surface)',
              color: msg.role === 'user' ? 'white' : 'var(--color-text)',
              borderRadius: 'var(--radius-sm)',
              maxWidth: '80%',
              marginLeft: msg.role === 'user' ? 'auto' : '0',
            }}
          >
            <strong>{msg.role === 'user' ? 'You' : 'Assistant'}:</strong> {msg.content}
          </div>
        ))}
        {loading && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <div className="loading"></div>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          type="text"
          className="input"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
          disabled={loading}
        />
        <button className="button" onClick={sendMessage} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
};

export default Chat;
