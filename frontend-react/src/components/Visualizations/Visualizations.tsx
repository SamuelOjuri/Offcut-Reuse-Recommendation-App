import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Typography,
  CircularProgress,
  Alert
} from '@mui/material';
import Plot from 'react-plotly.js';
import API_URL from '../../config/api';

type VizOption = "Top Materials" | "Top Offcuts" | "Monthly Material Usage" | "Material Efficiency";

const Visualizations: React.FC = () => {
  const [selectedViz, setSelectedViz] = useState<VizOption>('Top Materials');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [plotData, setPlotData] = useState<any>(null);
  const [isDebouncing, setIsDebouncing] = useState(false);
  const MAX_RETRIES = 3;
  const TIMEOUT_MS = 30000; // 30 seconds

  const vizOptions = useMemo(() => ({
    "Top Materials": "Create a bar chart showing the top 10 materials by Total Length Used",
    "Top Offcuts": "Create a bar chart showing top 10 items by total offcut length",
    "Monthly Material Usage": "Create bar charts showing total material usage over time",
    "Material Efficiency": "Create a visualization of top and bottom 5 materials by efficiency"
  } as const), []);

  const validatePlotData = (data: any): boolean => {
    if (!data || typeof data !== 'object') return false;
    if (!Array.isArray(data.data)) return false;
    if (typeof data.layout !== 'object') return false;
    
    return data.data.every((trace: any) => (
      typeof trace === 'object' && 
      (Array.isArray(trace.x) || Array.isArray(trace.y))
    ));
  };

  const generateVisualization = useCallback(async () => {
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
          'Accept': 'application/json'
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
        const { done, value } = await reader.read();
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
  }, [selectedViz, vizOptions]);

  const debouncedGenerateVisualization = useCallback(async () => {
    if (isDebouncing) return;
    setIsDebouncing(true);
    
    let retries = 0;
    while (retries < MAX_RETRIES) {
      try {
        await generateVisualization();
        break;
      } catch (err) {
        retries++;
        if (retries === MAX_RETRIES) {
          setError('Failed to generate visualization after multiple attempts');
        }
      }
    }
    
    setTimeout(() => setIsDebouncing(false), 1000);
  }, [isDebouncing, generateVisualization]);

  useEffect(() => {
    debouncedGenerateVisualization();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Box sx={{ 
      p: 4, 
      display: 'flex', 
      justifyContent: 'center', 
      background: 'linear-gradient(135deg, #f8fafc, #e9eff5)' 
    }}>
      <Card sx={{ width: '100%', maxWidth: 1200, borderRadius: 3, boxShadow: 3 }}>
        <CardContent>
          <Typography variant="h4" gutterBottom align="center" sx={{ fontWeight: 'bold', mb: 3 }}>
            Material Usage Analysis
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Box sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 2,
            alignItems: 'center',
            justifyContent: 'center',
            mb: 3
          }}>
            <FormControl sx={{ minWidth: 250 }}>
              <InputLabel id="visualization-select-label">Select Visualization</InputLabel>
              <Select
                labelId="visualization-select-label"
                value={selectedViz}
                label="Select Visualization"
                onChange={(e) => {
                  setSelectedViz(e.target.value as VizOption);
                  setPlotData(null);
                }}
              >
                {Object.keys(vizOptions).map((option) => (
                  <MenuItem key={option} value={option}>
                    {option}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button
              variant="contained"
              color="primary"
              onClick={debouncedGenerateVisualization}
              disabled={loading || !selectedViz}
              sx={{
                minWidth: { xs: '100%', sm: 200 },
                height: 56
              }}
            >
              {loading ? <CircularProgress size={24} color="inherit" /> : 'Generate'}
            </Button>
          </Box>

          {plotData && (
            <Box sx={{ mt: 4 }}>
              <Plot
                data={plotData.data}
                layout={{
                  ...plotData.layout,
                  autosize: true,
                  margin: { t: 50, b: 50, l: 50, r: 50 }
                }}
                style={{ width: '100%', height: '600px' }}
                useResizeHandler={true}
              />
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default Visualizations; 