import React from 'react';
import { AppBar, Toolbar, Button, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './Auth/AuthContext';

const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const { isAdmin, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/');
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
          {isAdmin ? (
            <>
              <Button color="inherit" onClick={() => navigate('/admin')}>
                Admin
              </Button>
              <Button color="inherit" onClick={handleLogout}>
                Logout
              </Button>
            </>
          ) : (
            <Button color="inherit" onClick={() => navigate('/login')}>
              Admin Login
            </Button>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navigation; 