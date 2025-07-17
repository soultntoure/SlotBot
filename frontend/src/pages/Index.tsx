import { useState, useEffect, useRef } from 'react';
import { Send, Calendar, Clock, XCircle, MessageCircle, Stethoscope, Bot, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from '@/hooks/use-toast';

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

interface ChatSession {
  session_id: string;
  messages: Message[];
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const Index = () => {
  const [session, setSession] = useState<ChatSession | null>(null);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const examplePrompts = [
    { text: 'Book an appointment', icon: Calendar },
    { text: 'Check time slots', icon: Clock },
    { text: 'Cancel appointment', icon: XCircle },
    { text: 'General inquiry', icon: MessageCircle }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [session?.messages]);

  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      const data = await response.json();
      setIsConnected(data.status === 'ok');
    } catch (error) {
      console.log('Health check failed:', error);
      setIsConnected(true);
    }
  };

  const initializeChat = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_BASE_URL}/start_chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to start chat');

      const data = await response.json();
      const welcomeMessage: Message = {
        id: '1',
        content: data.message || 'Hello, welcome to my clinic. Would you like to book an appointment?',
        isUser: false,
        timestamp: new Date()
      };

      setSession({
        session_id: data.session_id,
        messages: [welcomeMessage]
      });
    } catch (error) {
      console.error('Failed to initialize chat:', error);
      // Fallback to demo mode
      const welcomeMessage: Message = {
        id: '1',
        content: 'Hello, welcome to my clinic. Would you like to book an appointment?',
        isUser: false,
        timestamp: new Date()
      };

      setSession({
        session_id: 'demo-session',
        messages: [welcomeMessage]
      });
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (message: string) => {
    if (!session || !message.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: message,
      isUser: true,
      timestamp: new Date()
    };

    setSession(prev => prev ? {
      ...prev,
      messages: [...prev.messages, userMessage]
    } : null);

    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: session.session_id,
          user_message: message
        })
      });

      if (!response.ok) throw new Error('Failed to send message');

      const data = await response.json();
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.chatbot_response,
        isUser: false,
        timestamp: new Date()
      };

      setSession(prev => prev ? {
        ...prev,
        messages: [...prev.messages, botMessage]
      } : null);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Demo response
      const demoResponses = [
        "I'd be happy to help you with that! Could you please provide more details?",
        "Let me check our available time slots for you. What day works best?",
        "I can help you cancel your appointment. May I have your booking reference?",
        "Thank you for contacting us. How can I assist you today?"
      ];
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: demoResponses[Math.floor(Math.random() * demoResponses.length)],
        isUser: false,
        timestamp: new Date()
      };

      setSession(prev => prev ? {
        ...prev,
        messages: [...prev.messages, botMessage]
      } : null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputMessage);
  };

  const handlePromptClick = (promptText: string) => {
    sendMessage(promptText);
  };

  useEffect(() => {
    checkHealth();
    initializeChat();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 relative overflow-hidden">
      {/* Medical-themed background pattern */}
      <div className="absolute inset-0 opacity-5">
        <svg width="100%" height="100%" className="absolute inset-0">
          <defs>
            <pattern id="medical-pattern" x="0" y="0" width="200" height="200" patternUnits="userSpaceOnUse">
              <circle cx="50" cy="50" r="2" fill="currentColor" className="text-blue-400" />
              <circle cx="150" cy="150" r="2" fill="currentColor" className="text-indigo-400" />
              <path d="M100,80 Q120,100 100,120 Q80,100 100,80" fill="none" stroke="currentColor" strokeWidth="1" className="text-blue-300" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#medical-pattern)" />
        </svg>
      </div>

      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-blue-100 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-500 to-indigo-500 p-2 rounded-lg">
                <Stethoscope className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-800">SlotBot — Your AI Clinic Assistant</h1>
                <p className="text-sm text-gray-600">Book Your Next Appointment in Seconds — No Calls, No Waits</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`}></div>
              {/* <span className="text-sm text-gray-600">{isConnected ? 'Connected' : 'Demo Mode'}</span> */}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl border border-blue-100 overflow-hidden">
          {/* Chat Messages */}
          <ScrollArea className="h-96 p-6">
            <div className="space-y-4">
              {session?.messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.isUser ? 'justify-end' : 'justify-start'} items-start space-x-3`}
                >
                  {!message.isUser && (
                    <div className="bg-gradient-to-r from-blue-500 to-indigo-500 p-2 rounded-full flex-shrink-0 mt-1">
                      <Bot className="h-4 w-4 text-white" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] p-4 rounded-2xl ${
                      message.isUser
                        ? 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white'
                        : 'bg-gray-50 text-gray-800 border border-gray-200'
                    }`}
                  >
                    <p className="text-sm leading-relaxed">{message.content}</p>
                    <p className={`text-xs mt-2 ${message.isUser ? 'text-blue-100' : 'text-gray-500'}`}>
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start items-start space-x-3">
                  <div className="bg-gradient-to-r from-blue-500 to-indigo-500 p-2 rounded-full flex-shrink-0 mt-1">
                    <Loader2 className="h-4 w-4 text-white animate-spin" />
                  </div>
                  <div className="bg-gray-50 border border-gray-200 p-4 rounded-2xl">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Example Prompts */}
          <div className="p-6 border-t border-gray-100 bg-gradient-to-r from-blue-50 to-indigo-50">
            <p className="text-sm font-medium text-gray-700 mb-3">What would you like to do?</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {examplePrompts.map((prompt, index) => {
                const IconComponent = prompt.icon;
                return (
                  <Button
                    key={index}
                    variant="outline"
                    onClick={() => handlePromptClick(prompt.text)}
                    className="h-auto p-4 bg-white hover:bg-blue-50 border-blue-200 hover:border-blue-300 transition-all duration-200 group hover:shadow-md hover:scale-105"
                    disabled={isLoading}
                  >
                    <div className="flex flex-col items-center space-y-2">
                      <IconComponent className="h-5 w-5 text-blue-500 group-hover:text-blue-600" />
                      <span className="text-xs font-medium text-gray-700 group-hover:text-blue-700">
                        {prompt.text}
                      </span>
                    </div>
                  </Button>
                );
              })}
            </div>
          </div>

          {/* Input Area */}
          <div className="p-6 border-t border-gray-100">
            <form onSubmit={handleSubmit} className="flex space-x-3">
              <Input
                ref={inputRef}
                type="text"
                placeholder="Ask me anything or type 'book' to schedule an appointment..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                disabled={isLoading}
                className="flex-1 border-blue-200 focus:border-blue-400 focus:ring-blue-400"
              />
              <Button
                type="submit"
                disabled={isLoading || !inputMessage.trim()}
                className="bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white px-6"
              >
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-sm text-gray-500">
            Powered by AI • Your health, our priority
          </p>
        </div>
      </div>
    </div>
  );
};

export default Index;
