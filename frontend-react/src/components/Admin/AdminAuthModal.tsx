import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Alert
} from '@mui/material';

interface AdminAuthModalProps {
  open: boolean;
  onClose: () => void;
  onAuthenticate: (password: string) => Promise<boolean>;
}

const AdminAuthModal: React.FC<AdminAuthModalProps> = ({ open, onClose, onAuthenticate }) => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const success = await onAuthenticate(password);
      if (success) {
        onClose();
      } else {
        setError('Invalid admin password');
      }
    } catch (err) {
      setError('Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Admin Authentication Required</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <TextField
            autoFocus
            margin="dense"
            label="Admin Password"
            type="password"
            fullWidth
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={loading}>
            Authenticate
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default AdminAuthModal;
