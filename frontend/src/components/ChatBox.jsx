import React, { useState } from 'react';

const PRESET_QUESTIONS = [
  'What does this result mean?',
  'What is this test?',
  'Why is this result marked high?',
  'What does the reference range mean?',
];

export default function ChatBox({ reportId, onSendChat, isLoading }) {
  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: 'Hello! I can help answer educational questions about your medical report results using curated medical reference knowledge.',
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [chatError, setChatError] = useState('');

  const handleSendMessage = async (textToSend) => {
    const query = textToSend || inputText;
    if (!query.trim() || isLoading) return;

    const userMsg = { sender: 'user', text: query.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setChatError('');

    try {
      const response = await onSendChat(query.trim());
      const assistantMsg = {
        sender: 'assistant',
        text: response.answer || 'No response returned.',
        ragHits: response.retrieved_knowledge || [],
        status: response.llm_status || response.status,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setChatError(err.message || 'Failed to send chat message.');
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: `⚠️ Error: ${err.message || 'Unable to fetch response from server.'}`,
          isError: true,
        },
      ]);
    }
  };

  return (
    <div className="card">
      <h2 className="card-title">💬 Report Chatbot Assistant</h2>
      <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem' }}>
        Ask educational questions about your report parameters and reference ranges.
      </p>

      {/* Suggested chips */}
      <div className="chat-chips">
        {PRESET_QUESTIONS.map((q, idx) => (
          <button
            key={idx}
            className="chip"
            onClick={() => handleSendMessage(q)}
            disabled={isLoading}
          >
            {q}
          </button>
        ))}
      </div>

      <div className="chat-container">
        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div key={index} className={`chat-bubble ${msg.sender}`}>
              <p>{msg.text}</p>

              {msg.status === 'not_configured' && (
                <div
                  style={{
                    fontSize: '0.8rem',
                    color: '#92400e',
                    marginTop: '0.5rem',
                    paddingTop: '0.5rem',
                    borderTop: '1px solid #fde68a',
                  }}
                >
                  ℹ️ <em>Note: LLM provider is unconfigured in backend environment.</em>
                </div>
              )}

              {msg.ragHits && msg.ragHits.length > 0 && (
                <div
                  style={{
                    marginTop: '0.5rem',
                    paddingTop: '0.5rem',
                    borderTop: '1px solid #e2e8f0',
                    fontSize: '0.8rem',
                    color: '#0d9488',
                  }}
                >
                  📚 <strong>Supporting Reference Knowledge:</strong>
                  {msg.ragHits.map((hit, hitIdx) => (
                    <div key={hitIdx} style={{ marginTop: '0.25rem' }}>
                      • Q: {hit.question}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="chat-bubble assistant">
              <span style={{ fontStyle: 'italic', color: '#64748b' }}>
                Searching medical knowledge & generating response...
              </span>
            </div>
          )}
        </div>

        <form
          className="chat-input-row"
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
        >
          <input
            type="text"
            className="chat-input"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type your medical report question..."
            disabled={isLoading}
          />
          <button
            className="btn-primary"
            type="submit"
            disabled={isLoading || !inputText.trim()}
          >
            Send
          </button>
        </form>

        {chatError && <div className="error-alert">{chatError}</div>}
      </div>
    </div>
  );
}
