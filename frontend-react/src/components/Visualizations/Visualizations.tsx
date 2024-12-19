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

// interface VisualizationOptions {
//   [key: string]: string | null;
// }



const Visualizations: React.FC = () => {
  const [selectedViz, setSelectedViz] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [plotData, setPlotData] = useState<any>(null);
  const [isDebouncing, setIsDebouncing] = useState(false);
  const MAX_RETRIES = 3;
  const TIMEOUT_MS = 30000; // 30 seconds

  const vizOptions: { [key: string]: string } = {
    "Material Usage Trends": "Create a line chart showing total material usage over time",
    "Top Materials": "Create a bar chart showing the top 10 materials by Total Length Used",
    "Top Offcuts": "Create a bar chart showing top 10 items by total offcut length",
    "Material Efficiency": "Create a visualization of top and bottom 5 materials by efficiency"
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

  const generateVisualization = async () => {
    setError(null);
    setLoading(true);
    setPlotData(null);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

    try {
      const response = await fetch(`${API_URL}/api/visualizations/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          query: vizOptions[selectedViz]
        }),
        signal: controller.signal
      });

      if (!response.ok) throw new Error('Failed to fetch visualization data');

      const reader = response.body?.getReader();
      if (!reader) throw new Error('Streaming not supported');

      let result = '';
      while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        result += new TextDecoder().decode(value);
      }

      const data = JSON.parse(result);
      if (!data.figure || !validatePlotData(data.figure)) {
        throw new Error('Invalid visualization data');
      }

      setPlotData(data.figure);
    } catch (err) {
      console.error('Visualization error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      clearTimeout(timeoutId);
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

      <Button 
        variant="contained" 
        onClick={debouncedGenerateVisualization}
        disabled={loading || !selectedViz}
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