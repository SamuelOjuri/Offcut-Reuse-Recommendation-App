import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#8a0101',
      light: '#9B3154',
      dark: '#5C1225',
    },
    secondary: {
      main: '#2C5282',
      light: '#4A69BB',
      dark: '#1A365D',
    },
    background: {
      default: '#F8FAFC',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1A202C',
      secondary: '#4A5568',
    },
    error: {
      main: '#DC2626',
      light: '#EF4444',
      dark: '#B91C1C',
    },
    success: {
      main: '#059669',
      light: '#10B981',
      dark: '#047857',
    },
    warning: {
      main: '#D97706',
      light: '#F59E0B',
      dark: '#B45309',
    },
    info: {
      main: '#2563EB',
      light: '#3B82F6',
      dark: '#1D4ED8',
    },
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '2.5rem',
    },
    h2: {
      fontWeight: 700,
      fontSize: '2rem',
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.75rem',
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.5rem',
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.25rem',
    },
    h6: {
      fontWeight: 600,
      fontSize: '1rem',
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          borderRadius: '8px',
          padding: '8px 16px',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        },
        contained: { 
          background: 'linear-gradient(145deg, rgba(123, 31, 60, 0.95), rgba(107, 27, 52, 1)) !important',
          boxShadow: '0 4px 12px rgba(123, 31, 60, 0.25), 0 2px 6px rgba(0, 0, 0, 0.08), inset 0 1px 1px rgba(255, 255, 255, 0.1)',
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(145deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.02))',
            opacity: 0,
            transition: 'opacity 0.3s ease-in-out',
          },
          '&:hover': {
            background: 'linear-gradient(145deg, rgba(139, 35, 68, 1), rgba(123, 31, 60, 1)) !important',
            boxShadow: '0 6px 15px rgba(123, 31, 60, 0.25), 0 4px 6px rgba(0, 0, 0, 0.12)',
            transform: 'translateY(-2px)',
            '&::before': {
              opacity: 1,
            },
          },
          '&:active': {
            transform: 'translateY(0)',
            boxShadow: '0 2px 8px rgba(123, 31, 60, 0.2), 0 1px 2px rgba(0, 0, 0, 0.1)',
          },
          '&.Mui-disabled': {
            color: '#8a0101',
            background: 'linear-gradient(145deg, rgba(203, 203, 203, 1), rgba(189, 189, 189, 1)) !important',
            boxShadow: 'none',
          },
        },
        outlined: {
          borderWidth: '1.5px',
          '&:hover': {
            borderWidth: '1.5px',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '16px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.02)',
          border: '1px solid rgba(0,0,0,0.05)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          color: '#1e293b',
          boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            backgroundColor: '#FFFFFF',
            transition: 'all 0.2s ease-in-out',
            boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
            
            // Default state 
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: 'rgba(74, 85, 104, 0.3)', // Slightly darker border
              borderWidth: '1.5px', // Slightly thicker border
            },
            
            // Hover state
            '&:hover': {
              backgroundColor: '#F8FAFC',
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: '#8a0101',
              },
            },
            
            // Focused state
            '&.Mui-focused': {
              backgroundColor: '#FFFFFF',
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: '#8a0101',
                borderWidth: '2px',
                boxShadow: '0 0 0 4px rgba(123, 31, 60, 0.1)',
              },
            },
          },
          
          // Input text
          '& .MuiInputBase-input': {
            padding: '16px 14px',
            color: '#1A202C',
            fontSize: '1rem',
            '&::placeholder': {
              color: '#718096',
              opacity: 1,
            },
          },
          
          // Label styling
          '& .MuiInputLabel-root': {
            color: '#4A5568',
            fontWeight: 500,
            '&.Mui-focused': {
              color: '#8a0101',
            },
          },
          
          // Helper text
          '& .MuiFormHelperText-root': {
            marginLeft: '4px',
            fontSize: '0.875rem',
          },
          
          // Error state
          '& .Mui-error': {
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: '#DC2626',
            },
            '&.MuiInputLabel-root': {
              color: '#DC2626',
            },
          },
          
          // Disabled state
          '& .Mui-disabled': {
            backgroundColor: '#F1F5F9',
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: 'rgba(74, 85, 104, 0.1)',
            },
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: '16px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.02)',
        },
      },
    },
  },
}); 