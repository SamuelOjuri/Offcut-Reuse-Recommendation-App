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
  ListItemText,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from '@mui/material';

import { DatePicker } from '@mui/x-date-pickers';
import UploadIcon from '@mui/icons-material/Upload';
import RefreshIcon from '@mui/icons-material/Refresh';
import StorageIcon from '@mui/icons-material/Storage';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import OffcutUsageHistory from './OffcutUsageHistory';
import API_URL from '../../config/api';

interface DatabaseStats {
  total_batches: number;
  total_items: number;
  total_offcuts: number;
  total_available_offcuts: number;
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
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/status`);
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
    if (event.target.files && event.target.files.length > 0) {
      // Store first file
      setFile(event.target.files[0]);
      setProcessedData(null);
      
      // Show warning if multiple files selected
      if (event.target.files.length > 1) {
        setError('Only one PDF file can be processed at a time. The first file has been selected.');
        
        // Clear error after 5 seconds
        setTimeout(() => {
          setError(null);
        }, 5000);
      }
    }
  };

  const handleProcess = async () => {
    // Clear previous states
    setError(null);
    setProcessedData(null);

    // Validate required inputs
    if (!file) {
        setError('Please select a PDF file');
        return;
    }

    if (!batchDate) {
        setError('Please select a batch date');
        return;
    }

    setLoading(true);

    try {
        // Upload file
        const formData = new FormData();
        formData.append('file', file);
        
        const uploadResponse = await fetch(`${API_URL}/api/admin/upload`, {
            method: 'POST',
            body: formData
        });

        if (!uploadResponse.ok) {
            const errorData = await uploadResponse.json();
            throw new Error(errorData.error || 'Upload failed');
        }
        const uploadData = await uploadResponse.json();

        // Process file
        const processResponse = await fetch(`${API_URL}/api/admin/process`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                batch_date: batchDate.toISOString().split('T')[0],
                filename: uploadData.filename
            })
        });

        if (processResponse.status === 409) {
            const data = await processResponse.json();
            setError(`Batch ${data.batch_code} already exists in the database. Please choose a different file.`);
            return;
        }

        if (!processResponse.ok) {
            const errorData = await processResponse.json();
            throw new Error(errorData.error || 'Processing failed');
        }

        const data = await processResponse.json();
        setProcessedData(data.preview);
        setCurrentFilename(uploadData.filename);

    } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to process file');
    } finally {
        setLoading(false);
    }
  };

  const handleIngest = async () => {
    setLoading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await fetch(`${API_URL}/api/admin/ingest`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.status === 409) {
        const data = await response.json();
        setError(`Duplicate batch codes found: ${data.existing_codes.join(', ')}. 
                 These batches already exist in the database.`);
        return;
      }

      if (!response.ok) throw new Error('Ingestion failed');

      await fetchStats(); // Refresh stats after ingestion
      
      // Set success message
      setSuccessMessage('Data successfully ingested into the database!');
      
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
    <Box sx={{ p: 4, maxWidth: 1400, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
        Data Administration
      </Typography>

      <Grid container spacing={4}>
        {/* Left Panel */}
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
              Upload and Process Cutting Instructions Batch File
            </Typography>
            
            {/* File Upload Section */}
            <Box sx={{ mb: 3 }}>
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
                id="file-upload"
              />
              
              <label htmlFor="file-upload">
                <Button
                  variant="contained"
                  component="span"
                  startIcon={<UploadIcon />}
                  size="large"
                  sx={{ minWidth: 200 }}
                >
                  Select PDF File
                </Button>
              </label>
            </Box>

            {/* File Processing Section */}
            {file && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="body1" sx={{ mb: 2, fontWeight: 500 }}>
                  Selected file: {file.name}
                </Typography>
                
                <LocalizationProvider dateAdapter={AdapterDateFns}>
                  <DatePicker
                    label="Batch Date"
                    value={batchDate}
                    onChange={(newValue) => setBatchDate(newValue)}
                    disabled={loading}
                    sx={{ mb: 3, width: '100%' }}
                  />
                </LocalizationProvider>

                <Button
                  variant="contained"
                  onClick={handleProcess}
                  disabled={loading || !batchDate}
                  startIcon={<RefreshIcon />}
                  size="large"
                  sx={{ minWidth: 200 }}
                >
                  Process File
                </Button>
              </Box>
            )}

            {/* Preview Section */}
            {processedData && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="h6" gutterBottom>
                  Preview Data
                </Typography>
                <Paper sx={{ overflow: 'auto', maxHeight: 400 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        {Object.keys(processedData[0] || {}).map((header) => (
                          <TableCell key={header}>{header}</TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {processedData.map((row, index) => (
                        <TableRow key={index}>
                          {Object.values(row).map((value: any, cellIndex) => (
                            <TableCell key={cellIndex}>
                              {typeof value === 'number' 
                                ? Number(value).toLocaleString()
                                : String(value)
                              }
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Paper>
              </Box>
            )}

            {/* Ingest Section */}
            {processedData && (
              <Box sx={{ mt: 4, p: 3, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Successfully processed: {currentFilename}
                </Typography>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleIngest}
                  disabled={loading}
                  startIcon={<StorageIcon />}
                  size="large"
                  sx={{ minWidth: 200 }}
                >
                  Ingest Data
                </Button>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Right Panel */}
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
              Database Statistics
            </Typography>
            
            {stats && (
              <>
                {/* Statistics Cards */}
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={12}>
                    <Paper elevation={0} sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 2 }}>
                      <Typography variant="overline" sx={{ opacity: 0.8 }}>
                        Total Batches
                      </Typography>
                      <Typography variant="h3">
                        {stats.total_batches}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6}>
                    <Paper elevation={0} sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 2 }}>
                      <Typography variant="overline" color="text.secondary">
                        Total Items
                      </Typography>
                      <Typography variant="h4" color="text.primary">
                        {stats.total_items}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6}>
                    <Paper elevation={0} sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 2 }}>
                      <Typography variant="overline" color="text.secondary">
                        Available Offcuts
                      </Typography>
                      <Typography variant="h4" color="text.primary">
                        {stats.total_available_offcuts}
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>

                {/* Recent Batches Section */}
                <Box sx={{ mt: 4 }}>
                  <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
                    Recent Batches
                  </Typography>
                  <Paper variant="outlined" sx={{ borderRadius: 2 }}>
                    <List dense sx={{ py: 0 }}>
                      {stats.recent_batches.map((batch, index) => (
                        <ListItem 
                          key={index} 
                          sx={{ 
                            py: 1.5,
                            borderBottom: index < stats.recent_batches.length - 1 ? 1 : 0,
                            borderColor: 'divider'
                          }}
                        >
                          <ListItemText
                            primary={
                              <Typography variant="body1" fontWeight={500}>
                                {batch.batch_code}
                              </Typography>
                            }
                            secondary={
                              <Typography variant="body2" color="text.secondary">
                                {new Date(batch.batch_date).toLocaleDateString()}
                              </Typography>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                </Box>
              </>
            )}
          </Paper>
        </Grid>

        {/* Offcut Usage History Panel */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, mt: 4 }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
              Offcut Usage History
            </Typography>
            <OffcutUsageHistory />
          </Paper>
        </Grid>
      </Grid>

      {/* Status Messages */}
      <Box sx={{ mt: 4, position: 'fixed', bottom: 24, right: 24, zIndex: 1000 }}>
        {loading && (
          <Box sx={{ mb: 2 }}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert 
            severity="error" 
            sx={{ mb: 2 }}
            variant="filled"
          >
            {error}
          </Alert>
        )}

        {successMessage && (
          <Alert 
            severity="success"
            sx={{ mb: 2 }}
            variant="filled"
          >
            {successMessage}
          </Alert>
        )}
      </Box>
    </Box>
  );
};

export default Admin;