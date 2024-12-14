import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#5E81AC',
    },
    background: {
      default: '#FFFFFF',
      paper: '#FFFFFF',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '5px',
          textTransform: 'none',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '10px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        },
      },
    },
  },
}); 