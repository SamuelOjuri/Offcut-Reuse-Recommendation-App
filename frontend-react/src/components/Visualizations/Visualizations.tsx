import React, { useState } from 'react';
import { 
  Box, 
  Select, 
  MenuItem, 
  Button, 
  Typography, 
  TextField,
  CircularProgress,
  Alert
} from '@mui/material';
import Plot from 'react-plotly.js';
import API_URL from '../../config/api';

interface VisualizationOptions {
  [key: string]: string | null;
}



const Visualizations: React.FC = () => {
  const [selectedViz, setSelectedViz] = useState('');
  const [customQuery, setCustomQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [plotData, setPlotData] = useState<any>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [isDebouncing, setIsDebouncing] = useState(false);
  const MAX_RETRIES = 3;
  const TIMEOUT_MS = 30000; // 30 seconds

  const vizOptions: VisualizationOptions = {
    "Material Usage Trends": "Create a line chart showing total material usage over time",
    "Top Materials": "Create a bar chart showing the top 10 materials by Total Length Used",
    "Top Offcuts": "Create a bar chart showing top 10 items by total offcut length",
    "Material Efficiency": "Create a visualization of top and bottom 5 materials by efficiency",
    "Create a Visualisation": null
  };

  
  const validatePlotData = (data: any): boolean => {
    if (!data || typeof data !== 'object') return false;
    if (!Array.isArray(data.data)) return false;
    if (typeof data.layout !== 'object') return false;
    
    // Check if data array contains valid trace objects
    return data.data.every((trace: any) => (
      typeof trace === 'object' && 
      (Array.isArray(trace.x) || Array.isArray(trace.y))
    ));
  };

  // const validateVisualizationQuery = (query: string): { isValid: boolean; error: string | null } => {
  //   if (!query.trim()) {
  //     return { isValid: false, error: 'Query cannot be empty' };
  //   }

  //   if (query.trim().length < 10) {
  //     return { isValid: false, error: 'Query must be at least 10 characters long' };
  //   }

  //   if (query.trim().length > 500) {
  //     return { isValid: false, error: 'Query cannot exceed 500 characters' };
  //   }

  //   // Check for potentially harmful SQL keywords
  //   const sqlKeywords = /\b(DELETE|DROP|TRUNCATE|ALTER|MODIFY|GRANT|REVOKE|EXEC|EXECUTE)\b/i;
  //   if (sqlKeywords.test(query)) {
  //     return { isValid: false, error: 'Query contains invalid keywords' };
  //   }

  //   return { isValid: true, error: null };
  // };

  const generateVisualization = async () => {
    setError(null);
    setLoading(true);
    setPlotData(null);

    try {
      const response = await fetch(`${API_URL}/api/visualizations/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        mode: 'no-cors',
        credentials: 'include',
        body: JSON.stringify({
          query: selectedViz === "Create a Visualisation" ? customQuery : vizOptions[selectedViz]
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.figure || !validatePlotData(data.figure)) {
        throw new Error('Invalid visualization data received');
      }

      setPlotData(data.figure);
    } catch (err) {
      console.error('Visualization error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const debouncedGenerateVisualization = async () => {
    if (isDebouncing) return;
    setIsDebouncing(true);
    
    let retries = 0;
    while (retries < MAX_RETRIES) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);
        
        await generateVisualization();
        clearTimeout(timeoutId);
        break;
      } catch (err) {
        retries++;
        if (retries === MAX_RETRIES) {
          setError('Failed to generate visualization after multiple attempts');
        }
      }
    }
    
    setTimeout(() => setIsDebouncing(false), 1000);
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        Material Usage Analysis
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Select
        fullWidth
        value={selectedViz}
        onChange={(e) => {
          setSelectedViz(e.target.value);
          setCustomQuery('');
          setPlotData(null);
        }}
        sx={{ mb: 2 }}
      >
        {Object.keys(vizOptions).map((option) => (
          <MenuItem key={option} value={option}>
            {option}
          </MenuItem>
        ))}
      </Select>

      {selectedViz === "Create a Visualisation" && (
        <>
          <TextField
            fullWidth
            multiline
            rows={3}
            value={customQuery}
            onChange={(e) => {
              setCustomQuery(e.target.value);
              setQueryError(null);
            }}
            placeholder="Example: Show me bar plots of the monthly trend of materials usage by total length used"
            error={!!queryError}
            helperText={queryError}
            sx={{ mb: 2 }}
          />
        </>
      )}

      <Button 
        variant="contained" 
        onClick={debouncedGenerateVisualization}
        disabled={loading || (!selectedViz || (selectedViz === "Create a Visualisation" && !customQuery))}
        sx={{ mb: 3 }}
      >
        {loading ? <CircularProgress size={24} /> : 'Generate Visualization'}
      </Button>

      {plotData && (
        <Box className="visualization-container">
          <Plot
            data={plotData.data}
            layout={{
              ...plotData.layout,
              width: undefined,
              height: undefined,
              autosize: true
            }}
            style={{ width: '100%', height: '600px' }}
            useResizeHandler={true}
          />
        </Box>
      )}
    </Box>
  );
};

export default Visualizations; 