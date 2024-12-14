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

interface VisualizationOptions {
  [key: string]: string | null;
}

const Visualizations: React.FC = () => {
  const [selectedViz, setSelectedViz] = useState('');
  const [customQuery, setCustomQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [plotData, setPlotData] = useState<any>(null);

  const vizOptions: VisualizationOptions = {
    "Material Usage Trends": "Create a line chart showing total material usage over time",
    "Top Materials": "Create a bar chart showing the top 10 materials by Total Length Used",
    "Top Offcuts": "Create a bar chart showing top 10 items by total offcut length",
    "Material Efficiency": "Create a visualization of top and bottom 5 materials by efficiency",
    "Create a Visualisation": null
  };

  const generateVisualization = async () => {
    setError(null);
    setLoading(true);
    setPlotData(null);

    try {
      const queryPrompt = selectedViz === "Create a Visualisation" 
        ? customQuery 
        : vizOptions[selectedViz];

      if (!queryPrompt) {
        throw new Error("Please provide a visualization query");
      }

      const response = await fetch('http://localhost:5000/api/visualizations/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ query_prompt: queryPrompt }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate visualization');
      }

      const data = await response.json();
      if (data.figure) {
        setPlotData(data.figure);
      } else {
        throw new Error('No visualization data received');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
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
        <TextField
          fullWidth
          multiline
          rows={3}
          value={customQuery}
          onChange={(e) => setCustomQuery(e.target.value)}
          placeholder="Example: Show me bar plots of the monthly trend of materials usage by total length used"
          sx={{ mb: 2 }}
        />
      )}

      <Button 
        variant="contained" 
        onClick={generateVisualization}
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