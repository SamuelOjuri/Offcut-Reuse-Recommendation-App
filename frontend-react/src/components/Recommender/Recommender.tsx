import React, { useState } from 'react';
import { 
  Box, 
  TextField, 
  Button, 
  Typography, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import API_URL from '../../config/api';

interface Recommendation {
  is_double_cut: boolean;
  matched_profile: string;
  legacy_offcut_id: string;
  related_legacy_offcut_id?: string;
  reasoning: string;
  suggested_length: number;
}

const Recommender: React.FC = () => {
  const [batchCode, setBatchCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const formatBatchCode = (code: string): string => {
    const formattedCode = code.trim().toUpperCase();
    if (formattedCode.match(/^\d+$/)) {
      return `BO${formattedCode.padStart(6, '0')}`;
    }
    return formattedCode;
  };

  const isValidBatchCode = (code: string): boolean => {
    return /^BO\d{6}$/.test(code);
  };

  const checkBatchExists = async (code: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URL}/api/batches/check/${code}`);
      const data = await response.json();
      return data.exists;
    } catch (err) {
      throw new Error('Failed to check batch code');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);
    setRecommendations([]);

    const formattedCode = formatBatchCode(batchCode);

    if (!isValidBatchCode(formattedCode)) {
      setError('Invalid batch code format. Please use format "BO003643" or just "3643"');
      return;
    }

    setLoading(true);
    try {
      const exists = await checkBatchExists(formattedCode);
      if (!exists) {
        setError(`Batch code ${formattedCode} not found in database`);
        return;
      }

      const response = await fetch(`${API_URL}/api/recommendations/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ batch_code: formattedCode }),
      });

      const data = await response.json();
      if (response.ok) {
        setSuccessMessage(data.message);
        setRecommendations(data.recommendations || []);
      } else {
        throw new Error(data.error || 'Failed to get recommendations');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    const headers = ['Double Cut', 'Matched Profile', 'Offcut ID', 'Related Offcut ID', 'Reasoning', 'Suggested Length (mm)'];
    const csvContent = [
      headers.join(','),
      ...recommendations.map(rec => [
        rec.is_double_cut,
        rec.matched_profile,
        rec.legacy_offcut_id,
        rec.related_legacy_offcut_id || '',
        `"${rec.reasoning}"`,
        rec.suggested_length
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `recommendations_${batchCode}.csv`;
    link.click();
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        Offcut Reuse Recommendation System
      </Typography>

      <Typography variant="body1" sx={{ mb: 3 }}>
        Get recommendations for reusing material offcuts based on batch requirements.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {successMessage && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <TextField
          fullWidth
          value={batchCode}
          onChange={(e) => setBatchCode(e.target.value)}
          label="Batch Code"
          placeholder="e.g., BO003643"
          variant="outlined"
          sx={{ mb: 2 }}
          disabled={loading}
        />
        <Button 
          type="submit" 
          variant="contained" 
          disabled={loading || !batchCode.trim()}
        >
          {loading ? <CircularProgress size={24} /> : 'Get Recommendations'}
        </Button>
      </form>

      {recommendations.length > 0 && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h5" gutterBottom>
            Recommended Offcuts
          </Typography>

          <TableContainer component={Paper} sx={{ mb: 3 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Double Cut</TableCell>
                  <TableCell>Matched Profile</TableCell>
                  <TableCell>Offcut ID</TableCell>
                  <TableCell>Related Offcut ID</TableCell>
                  <TableCell>Suggested Length (mm)</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recommendations.map((rec, index) => (
                  <TableRow key={index}>
                    <TableCell>{rec.is_double_cut ? 'Yes' : 'No'}</TableCell>
                    <TableCell>{rec.matched_profile}</TableCell>
                    <TableCell>{rec.legacy_offcut_id}</TableCell>
                    <TableCell>{rec.related_legacy_offcut_id || '-'}</TableCell>
                    <TableCell>{rec.suggested_length}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h5" gutterBottom>
            Detailed Recommendations
          </Typography>

          {recommendations.map((rec, index) => (
            <Accordion key={index} sx={{ mb: 1 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Recommendation {index + 1}</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <pre style={{ whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(rec, null, 2)}
                </pre>
              </AccordionDetails>
            </Accordion>
          ))}

          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={6}>
              <Button 
                fullWidth 
                variant="outlined" 
                onClick={handleDownload}
              >
                Download Recommendations
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button 
                fullWidth 
                variant="contained" 
                onClick={() => alert('Confirmation functionality to be implemented')}
              >
                Confirm Selected Recommendations
              </Button>
            </Grid>
          </Grid>
        </Box>
      )}
    </Box>
  );
};

export default Recommender; 