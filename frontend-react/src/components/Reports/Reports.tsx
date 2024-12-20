import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Tabs, 
  Tab, 
  Paper,
  Grid,
  Select,
  MenuItem,
  Button,
  CircularProgress,
  Alert
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import API_URL from '../../config/api';

interface SummaryMetrics {
  item_code: string;
  item_description: string;
  total_input_length: number;
  total_used_length: number;
  total_offcut_length: number;
  avg_efficiency: number;
  avg_waste: number;
}

interface OffcutInventory {
  material_profile: string;
  length_mm: number;
  legacy_offcut_id: number;
  quantity: number;
}

const Reports: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [summaryMetrics, setSummaryMetrics] = useState<SummaryMetrics[]>([]);
  const [offcuts, setOffcuts] = useState<OffcutInventory[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<string>('All');
  const [materialProfiles, setMaterialProfiles] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch summary metrics
  const fetchSummaryMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/reports/summary`);
      if (!response.ok) throw new Error('Failed to fetch summary metrics');
      const data = await response.json();
      setSummaryMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Fetch offcuts inventory
  const fetchOffcuts = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/reports/offcuts`);
      if (!response.ok) throw new Error('Failed to fetch offcuts inventory');
      const data = await response.json();
      setOffcuts(data);
      const uniqueProfiles = Array.from(new Set(data.map((item: OffcutInventory) => item.material_profile))) as string[];
      const profiles = ['All', ...uniqueProfiles];
      setMaterialProfiles(profiles);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (tabValue === 0) fetchSummaryMetrics();
    if (tabValue === 1) fetchOffcuts();
  }, [tabValue]);

  const handleDownload = (data: any[], filename: string) => {
    const csvContent = 
      'data:text/csv;charset=utf-8,' + 
      Object.keys(data[0]).join(',') + '\n' +
      data.map(row => Object.values(row).join(',')).join('\n');
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${filename}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filteredOffcuts = selectedProfile === 'All' 
    ? offcuts 
    : offcuts.filter(item => item.material_profile === selectedProfile);

  const summaryColumns: GridColDef[] = [
    { field: 'item_code', headerName: 'Item Code', flex: 1 },
    { field: 'item_description', headerName: 'Item Description', flex: 1 },
    { field: 'total_input_length', headerName: 'Total Input Length (mm)', type: 'number', flex: 1 },
    { field: 'total_used_length', headerName: 'Total Used Length (mm)', type: 'number', flex: 1 },
    { field: 'total_offcut_length', headerName: 'Total Offcut Length (mm)', type: 'number', flex: 1 },
    { field: 'avg_efficiency', headerName: 'Average Efficiency (%)', type: 'number', flex: 1 },
    { field: 'avg_waste', headerName: 'Average Waste (%)', type: 'number', flex: 1 }
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Materials Usage Reports
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
        <Tab label="Summary Metrics" />
        <Tab label="Available Offcuts" />
        <Tab label="Detailed Analysis" />
      </Tabs>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {tabValue === 0 && summaryMetrics.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={4}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h6">Total Input Length</Typography>
                    <Typography variant="h4">
                      {(summaryMetrics.reduce((acc, curr) => acc + curr.total_input_length, 0) / 1000).toFixed(1)}m
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={4}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h6">Total Used Length</Typography>
                    <Typography variant="h4">
                      {(summaryMetrics.reduce((acc, curr) => acc + curr.total_used_length, 0) / 1000).toFixed(1)}m
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={4}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h6">Total Offcut Length</Typography>
                    <Typography variant="h4">
                      {(summaryMetrics.reduce((acc, curr) => acc + curr.total_offcut_length, 0) / 1000).toFixed(1)}m
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
              
              <DataGrid
                rows={summaryMetrics.map((row, index) => ({ id: index, ...row }))}
                columns={summaryColumns}
                autoHeight
                pageSizeOptions={[5, 10, 25]}
                initialState={{
                  pagination: { paginationModel: { pageSize: 10 } },
                }}
              />
              
              <Button 
                variant="outlined" 
                onClick={() => handleDownload(summaryMetrics, 'summary_metrics')}
                sx={{ mt: 2 }}
              >
                Download Summary Data
              </Button>
            </Box>
          )}

          {tabValue === 1 && (
            <Box sx={{ mt: 3 }}>
              <Select
                value={selectedProfile}
                onChange={(e) => setSelectedProfile(e.target.value)}
                sx={{ mb: 2, minWidth: 200 }}
              >
                {materialProfiles.length > 0 ? (
                  materialProfiles.map((profile) => (
                    <MenuItem key={profile} value={profile}>
                      {profile}
                    </MenuItem>
                  ))
                ) : (
                  <MenuItem value="All">All</MenuItem>
                )}
              </Select>

              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={6}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h6">Total Available Offcuts</Typography>
                    <Typography variant="h4">
                      {filteredOffcuts.reduce((acc, curr) => acc + curr.quantity, 0)}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h6">Unique Lengths</Typography>
                    <Typography variant="h4">
                      {new Set(filteredOffcuts.map(item => item.length_mm)).size}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>

              <DataGrid
                rows={filteredOffcuts.map((row, index) => ({ id: index, ...row }))}
                columns={[
                  { field: 'material_profile', headerName: 'Material Profile', flex: 1 },
                  { 
                    field: 'legacy_offcut_id', 
                    headerName: 'Offcut ID', 
                    type: 'number', 
                    flex: 1,
                    valueFormatter: (params: { value: number }) => Number(params.value).toFixed(0)
                  },
                  { field: 'length_mm', headerName: 'Length (mm)', type: 'number', flex: 1 },
                  { field: 'quantity', headerName: 'Quantity Available', type: 'number', flex: 1 }
                ]}
                autoHeight
                pageSizeOptions={[5, 10, 25]}
                initialState={{
                  pagination: { paginationModel: { pageSize: 10 } },
                }}
              />

              <Button 
                variant="outlined" 
                onClick={() => handleDownload(filteredOffcuts, `offcuts_inventory_${selectedProfile.toLowerCase()}`)}
                sx={{ mt: 2 }}
              >
                Download Offcuts Data
              </Button>
            </Box>
          )}

          {tabValue === 2 && (
            <Box sx={{ mt: 3 }}>
              <Alert severity="info">
                Detailed analysis features coming soon!
              </Alert>
            </Box>
          )}
        </>
      )}
    </Box>
  );
};

export default Reports; 