import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Navigation from './components/Navigation';
import ChatAssistant from './components/Chat/ChatAssistant';
import Recommender from './components/Recommender/Recommender';
import Visualizations from './components/Visualizations/Visualizations';
import Reports from './components/Reports/Reports';
import { theme } from './styles/theme';
import { AuthProvider } from './contexts/AuthContext';
import Login from './components/Auth/Login';
import PrivateRoute from './components/Auth/PrivateRoute';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import SignUp from './components/Auth/SignUp';
import Admin from './components/Admin/Admin';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Navigation />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/" element={
            <PrivateRoute>
              <ChatAssistant />
            </PrivateRoute>
          } />
          <Route path="/recommender" element={
            <PrivateRoute>
              <Recommender />
            </PrivateRoute>
          } />
          <Route path="/visualizations" element={
            <PrivateRoute>
              <Visualizations />
            </PrivateRoute>
          } />
          <Route path="/reports" element={
            <PrivateRoute>
              <Reports />
            </PrivateRoute>
          } />
          <Route path="/admin" element={
            <ProtectedRoute>
              <Admin />
            </ProtectedRoute>
          } />
        </Routes>
      </ThemeProvider>
    </AuthProvider>
  );
};

export default App;