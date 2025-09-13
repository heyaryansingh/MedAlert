import React, { useState, useEffect, useRef } from 'react';

interface ChatMessage {
  _id?: string;
  sender: 'patient' | 'ai';
  message: string;
  timestamp: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const SimplifiedPatientDashboard: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Mock patient ID for demo purposes
  const patientId = '650d7f3e7b1f8c9d0e1f2a3b'; 

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const fetchChatHistory = async () => {
      try {
        const chatResponse = await fetch(`${API_BASE_URL}/patient/chat_history`);
        if (chatResponse.ok) {
          const chatHistory = await chatResponse.json();
          setMessages(chatHistory);
        }
      } catch (error) {
        console.error('Error fetching chat history:', error);
      }
    };
    fetchChatHistory();
  }, [patientId]);

  const handleSendMessage = async () => {
    if (inputMessage.trim() === '') return;

    const newMessage: ChatMessage = {
      sender: 'patient',
      message: inputMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, newMessage]);
    setInputMessage('');

    try {
      const response = await fetch(`${API_BASE_URL}/patient/chatbot_message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ patient_id: patientId, message: inputMessage }),
      });

      if (response.ok) {
        const aiMessage: ChatMessage = await response.json();
        setMessages((prev) => [...prev, aiMessage]);
      } else {
        console.error('Failed to get AI response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  return (
    <div className="patient-dashboard">
      <h2>Simplified Patient Dashboard</h2>

      <div className="chatbot-section">
        <h3>AI Chatbot</h3>
        <div className="chat-window">
          {messages.map((msg, index) => (
            <div key={index} className={`chat-message ${msg.sender}`}>
              <strong>{msg.sender === 'patient' ? 'You' : 'MedAlert AI'}:</strong> {msg.message}
              <span className="timestamp">{new Date(msg.timestamp).toLocaleTimeString()}</span>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <div className="chat-input">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Type your message..."
          />
          <button onClick={handleSendMessage}>Send</button>
        </div>
      </div>
    </div>
  );
};

export default SimplifiedPatientDashboard;