import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Navigation from './components/Navigation';
import ChatAssistant from './components/Chat/ChatAssistant';
import Recommender from './components/Recommender/Recommender';
import Visualizations from './components/Visualizations/Visualizations';
import Reports from './components/Reports/Reports';
import Admin from './components/Admin/Admin';
import { theme } from './styles/theme';
import { AuthProvider } from './components/Auth/AuthContext';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import Login from './components/Auth/Login';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Navigation />
        <Routes>
          <Route path="/" element={<ChatAssistant />} />
          <Route path="/recommender" element={<Recommender />} />
          <Route path="/visualizations" element={<Visualizations />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/login" element={<Login />} />
          <Route 
            path="/admin" 
            element={
              <ProtectedRoute>
                <Admin />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </ThemeProvider>
    </AuthProvider>
  );
};

export default App;