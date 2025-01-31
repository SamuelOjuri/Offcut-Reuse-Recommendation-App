import React, { useState } from 'react';
import { AppBar, Toolbar, Button, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import AdminAuthModal from './Admin/AdminAuthModal';

const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const { currentUser, logout, isAdmin, checkAdminPassword } = useAuth();
  const [showAdminAuth, setShowAdminAuth] = useState(false);

  const handleAdminClick = () => {
    if (isAdmin) {
      navigate('/admin');
    } else {
      setShowAdminAuth(true);
    }
  };

  const handleAdminAuth = async (password: string) => {
    const success = await checkAdminPassword(password);
    if (success) {
      navigate('/admin');
    }
    return success;
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <Box sx={{ flexGrow: 1, display: 'flex', gap: 2 }}>
          <Button color="inherit" onClick={() => navigate('/')}>
            Chat Assistant
          </Button>
          <Button color="inherit" onClick={() => navigate('/recommender')}>
            Recommender
          </Button>
          <Button color="inherit" onClick={() => navigate('/visualizations')}>
            Visualizations
          </Button>
          <Button color="inherit" onClick={() => navigate('/reports')}>
            Reports
          </Button>
          {currentUser && (
            <Button color="inherit" onClick={handleAdminClick}>
              Admin
            </Button>
          )}
        </Box>
        {currentUser && (
          <Button color="inherit" onClick={logout}>
            Logout
          </Button>
        )}
        <AdminAuthModal
          open={showAdminAuth}
          onClose={() => setShowAdminAuth(false)}
          onAuthenticate={handleAdminAuth}
        />
      </Toolbar>
    </AppBar>
  );
};

export default Navigation; 