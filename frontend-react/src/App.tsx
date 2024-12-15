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

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Navigation />
      <Routes>
        <Route path="/" element={<ChatAssistant />} />
        <Route path="/recommender" element={<Recommender />} />
        <Route path="/visualizations" element={<Visualizations />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/admin" element={<Admin />} />
      </Routes>
    </ThemeProvider>
  );
};

export default App;