import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Button, 
  Typography, 
  Paper, 
  CircularProgress,
  Alert,
  Grid,
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import { Upload, Database, RefreshCw } from 'react-feather';
import { DatePicker } from '@mui/x-date-pickers';
import { TextField } from '@mui/material';

interface DatabaseStats {
  total_batches: number;
  total_items: number;
  total_offcuts: number;
  recent_batches: Array<{
    batch_code: string;
    batch_date: string;
  }>;
}

const Admin: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [processedData, setProcessedData] = useState<any[] | null>(null);
  const [batchDate, setBatchDate] = useState<Date | null>(null);
  const [currentFilename, setCurrentFilename] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/status');
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError('Failed to fetch database statistics');
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0]);
      setProcessedData(null);
    }
  };

  const handleProcess = async () => {
    if (!file || !batchDate) {
      setError('Both file and batch date are required');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Upload file
      const uploadResponse = await fetch('/api/admin/upload', {
        method: 'POST',
        body: formData
      });

      if (!uploadResponse.ok) throw new Error('Upload failed');
      const uploadData = await uploadResponse.json();

      // Process file with batch date
      const processResponse = await fetch('/api/admin/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          batch_date: batchDate.toISOString().split('T')[0],
          filename: uploadData.filename
        })
      });

      const processData = await processResponse.json();
      
      if (processResponse.status === 409) {
        setError(`Duplicate batch codes found: ${processData.existing_codes.join(', ')}. 
                 These batches already exist in the database.`);
        return;
      }

      setProcessedData(processData.preview);
      setCurrentFilename(uploadData.filename);

    } catch (err) {
      setError('Failed to process file');
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/admin/ingest', {
        method: 'POST'
      });

      if (response.status === 409) {
        const data = await response.json();
        setError(`Duplicate batch codes found: ${data.existing_codes.join(', ')}. 
                 These batches already exist in the database.`);
        return;
      }

      if (!response.ok) throw new Error('Ingestion failed');

      const data = await response.json();
      await fetchStats(); // Refresh stats after ingestion
      
      // Clear processed data after successful ingestion
      setProcessedData(null);
      setFile(null);
      setBatchDate(null);
      setCurrentFilename(null);
      
    } catch (err) {
      setError('Failed to ingest data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Data Administration
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Upload and Process Files
            </Typography>
            
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
              id="file-upload"
            />
            
            <Box sx={{ mb: 2 }}>
              <label htmlFor="file-upload">
                <Button
                  variant="contained"
                  component="span"
                  startIcon={<Upload />}
                >
                  Select PDF File
                </Button>
              </label>
            </Box>

            {file && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2">
                  Selected file: {file.name}
                </Typography>
                <Button
                  variant="contained"
                  onClick={handleProcess}
                  disabled={loading}
                  startIcon={<RefreshCw />}
                >
                  Process File
                </Button>
              </Box>
            )}

            {processedData && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2">
                  Successfully processed: {currentFilename}
                </Typography>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleIngest}
                  disabled={loading}
                  startIcon={<Database />}
                >
                  Ingest Data
                </Button>
              </Box>
            )}

            <Box sx={{ mb: 2 }}>
              <DatePicker
                label="Batch Date"
                value={batchDate}
                onChange={(newValue) => setBatchDate(newValue)}
              />
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Database Statistics
            </Typography>
            
            {stats && (
              <List>
                <ListItem>
                  <ListItemText 
                    primary="Total Batches"
                    secondary={stats.total_batches}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Total Items"
                    secondary={stats.total_items}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Total Offcuts"
                    secondary={stats.total_offcuts}
                  />
                </ListItem>
              </List>
            )}
          </Paper>
        </Grid>
      </Grid>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
};

export default Admin;
