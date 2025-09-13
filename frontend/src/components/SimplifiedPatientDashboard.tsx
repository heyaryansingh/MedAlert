import React, { useState, useEffect, useRef } from 'react';

interface ChatMessage {
  _id?: string;
  sender: 'patient' | 'ai';
  message: string;
  timestamp: string;
  image_url?: string; // allow image messages
  requires_image_upload?: boolean; // AI can request an image upload
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const SimplifiedPatientDashboard: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false); // Add loading state
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Mock patient ID for demo purposes
  const patientId = '650d7f3e7b1f8c9d0e1f2a3b';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedImage(event.target.files[0]); // store only the first file
    }
  };

  const handleCheckupDone = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/patient/generate_notes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ patient_id: patientId }),
      });

      if (response.ok) {
        alert('Checkup complete! Your notes have been sent to your doctor.');
        setMessages([]); // Clear chat for a new session
      } else {
        console.error('Failed to generate AI notes');
        alert('Failed to complete checkup. Please try again.');
      }
    } catch (error) {
      console.error('Error during checkup completion:', error);
      alert('An error occurred. Please try again.');
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const fetchChatHistory = async () => {
      try {
        const chatResponse = await fetch(`${API_BASE_URL}/patient/chat_history?patient_id=${patientId}`);
        if (chatResponse.ok) {
          const chatHistory = await chatResponse.json();
          setMessages(chatHistory);

          // If no chat history, add an initial message from the AI
          if (chatHistory.length === 0) {
            setMessages((prev) => [
              ...prev,
              {
                sender: 'ai',
                message: 'Hello! I am MedAlert AI. How are you feeling today?',
                timestamp: new Date().toISOString(),
              },
            ]);
          }
        }
      } catch (error) {
        console.error('Error fetching chat history:', error);
      }
    };
    fetchChatHistory();
  }, [patientId]);

  const handleSendMessage = async () => {
      if (inputMessage.trim() === '' && !selectedImage) return;

      setLoading(true); // Start loading

      const patientMessage: ChatMessage = {
          sender: 'patient',
          message: inputMessage || (selectedImage ? 'Uploaded an image' : ''),
          timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, patientMessage]);
      setInputMessage('');

      let imageUrl: string | undefined;

      try {
          // 1. Handle image upload first if selected
          if (selectedImage) {
              const formData = new FormData();
              formData.append('file', selectedImage);
              formData.append('patient_id', patientId);
              formData.append('description', `Image uploaded by patient with message: ${inputMessage}`);

              const imageUploadResponse = await fetch(`${API_BASE_URL}/patient/upload_image`, {
                  method: 'POST',
                  body: formData,
              });

              if (imageUploadResponse.ok) {
                  const result = await imageUploadResponse.json();
                  imageUrl = result.image_url;
                  // Add image message to chat
                  setMessages((prev) => [
                      ...prev.slice(0, prev.length - 1), // Remove placeholder patient message
                      {
                          ...patientMessage,
                          message: `Image uploaded: ${selectedImage.name}`,
                          image_url: imageUrl,
                      },
                  ]);
              } else {
                  console.error('Failed to upload image');
                  alert('Failed to upload image. Please try again.');
                  setLoading(false);
                  return;
              }
              setSelectedImage(null); // Clear selected image
          }

          // 2. Send text message (and optional image_url) to chatbot
          const response = await fetch(`${API_BASE_URL}/patient/chatbot_message`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                  patient_id: patientId,
                  message: inputMessage,
                  image_url: imageUrl, // Pass the uploaded image URL
              }),
          });

          if (response.ok) {
              const aiMessage: ChatMessage = await response.json();
              setMessages((prev) => [...prev, aiMessage]);

              if (aiMessage.requires_image_upload) {
                  alert('The AI has requested an image related to your symptoms. Please upload one using the file input.');
              }
          } else {
              console.error('Failed to get AI response');
              alert('Failed to get AI response. Please try again.');
          }
      } catch (error) {
          console.error('Error sending message or uploading image:', error);
          alert('An error occurred. Please try again.');
      } finally {
          setLoading(false); // End loading
      }
  };

  return (
    <div className="patient-dashboard-container">
      <header className="dashboard-header">
        <h1>MedAlert Patient Chat</h1>
        <button className="checkup-done-button" onClick={handleCheckupDone} disabled={loading}>
          Checkup Done
        </button>
      </header>

      <div className="chat-area">
        <div className="chat-messages-display">
          {messages.map((msg, index) => (
            <div key={index} className={`chat-bubble ${msg.sender}`}>
              <div className="message-content">
                {msg.message}
                {msg.image_url && (
                  <img src={msg.image_url} alt="Uploaded" className="chat-image" />
                )}
              </div>
              <span className="message-timestamp">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder={loading ? "Sending..." : "Type your message or symptom..."}
            disabled={loading}
            className="message-input"
          />
          <label htmlFor="image-upload" className="image-upload-label" style={{ cursor: loading ? 'not-allowed' : 'pointer' }}>
            📸
            <input
              id="image-upload"
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              disabled={loading}
              style={{ display: 'none' }}
            />
          </label>
          <button onClick={handleSendMessage} disabled={loading} className="send-button">
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SimplifiedPatientDashboard;
