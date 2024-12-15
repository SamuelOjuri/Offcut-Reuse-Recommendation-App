import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  Button, 
  Paper, 
  Typography, 
  CircularProgress, 
  Alert,
  Avatar,
  IconButton,
  Fade
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import SendIcon from '@mui/icons-material/Send';
import userAvatar from '../../assets/user.png';  // Changed from '../assets/user.png'
import assistantAvatar from '../../assets/chatbot.png';  // Changed from '../assets/chatbot.png'

const ChatAssistant: React.FC = () => {
  const [messages, setMessages] = useState<Array<{role: string, content: string}>>(() => {
    const saved = localStorage.getItem('chatHistory');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    localStorage.setItem('chatHistory', JSON.stringify(messages));
  }, [messages]);

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const streamResponse = async (prompt: string) => {
    try {
      const response = await fetch('http://localhost:5000/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response from server');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response stream available');

      let accumulatedMessage = '';
      
      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = new TextDecoder().decode(value);
        accumulatedMessage += text;
        
        // Create a new constant to avoid the closure issue
        const currentMessage = accumulatedMessage;
        
        setMessages(prev => [
          ...prev.slice(0, -1),
          { role: 'assistant', content: currentMessage }
        ]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setMessages(prev => prev.slice(0, -1));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    setError(null);
    setIsLoading(true);

    setMessages(prev => [...prev, { role: 'user', content: input }]);
    const userInput = input;
    setInput('');

    try {
      await streamResponse(userInput);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    setMessages([]);
    setError(null);
  };

  return (
    <Box sx={{ 
      p: 3, 
      maxWidth: 1200, 
      mx: 'auto',
      height: '90vh',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        mb: 2,
        borderBottom: '1px solid',
        borderColor: 'divider',
        pb: 2
      }}>
        <Typography variant="h4">
          Materials Usage Chat Assistant
        </Typography>
        <IconButton 
          onClick={handleClearHistory}
          color="primary"
          title="Clear chat history"
        >
          <DeleteIcon />
        </IconButton>
      </Box>

      <Fade in={!!error}>
        <Box sx={{ mb: 2 }}>
          {error && (
            <Alert 
              severity="error" 
              onClose={() => setError(null)}
              variant="filled"
            >
              {error}
            </Alert>
          )}
        </Box>
      </Fade>
      
      <Paper sx={{ 
        p: 2, 
        mb: 2, 
        flexGrow: 1,
        overflow: 'auto',
        bgcolor: 'grey.50',
        boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.1)'
      }}>
        {messages.map((msg, idx) => (
          <Box 
            key={idx} 
            sx={{ 
              mb: 2,
              display: 'flex',
              flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              alignItems: 'flex-start',
              gap: 1
            }}
          >
            <Avatar 
              sx={{ 
                width: 32,
                height: 32
              }}
              src={msg.role === 'user' ? userAvatar : assistantAvatar}
              alt={msg.role === 'user' ? 'User' : 'Assistant'}
            >
              {msg.role === 'user' ? 'U' : 'A'}
            </Avatar>
            <Paper 
                sx={{ 
                  p: 1.5,
                  maxWidth: '70%',
                  bgcolor: msg.role === 'user' ? '#cbcbcb' : '#f1f5f9',
                  color: '#1e293b',
                  borderRadius: msg.role === 'user' ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                  boxShadow: 2,
                  marginLeft: msg.role === 'user' ? 'auto' : 'inherit'
                }}
              >
            {/* <Paper 
              sx={{ 
                p: 1.5,
                maxWidth: '70%',
                bgcolor: msg.role === 'user' ? 'primary.light' : 'white',
                color: msg.role === 'user' ? 'white' : 'text.primary',
                borderRadius: msg.role === 'user' ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                boxShadow: 2
              }}
            > */}
              <Typography sx={{ whiteSpace: 'pre-wrap' }}>
                {msg.content}
              </Typography>
            </Paper>
          </Box>
        ))}
        <div ref={messagesEndRef} />
      </Paper>

      <Paper 
        component="form" 
        onSubmit={handleSubmit}
        sx={{ 
          p: 2,
          boxShadow: 3,
          bgcolor: 'background.paper'
        }}
      >
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your database..."
            variant="outlined"
            disabled={isLoading}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: '12px',
              }
            }}
          />
          <Button 
            type="submit" 
            variant="contained"
            disabled={isLoading || !input.trim()}
            sx={{ 
              borderRadius: '12px',
              minWidth: '100px'
            }}
          >
            {isLoading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              <SendIcon />
            )}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default ChatAssistant; 