import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Checkbox,
  Button,
  Alert,
  CircularProgress,
  FormControlLabel,
  TextField
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import API_URL from '../../config/api';



interface Offcut {
  offcut_id: number;
  legacy_offcut_id: number;
  length_mm: number;
  material_profile: string;
  created_in_batch_detail_id: number;
  reuse_count: number;
}

const OffcutUsageHistory: React.FC = () => {
  const [offcuts, setOffcuts] = useState<Offcut[]>([]);
  const [selectedOffcuts, setSelectedOffcuts] = useState<number[]>([]);
  const [reuseDate, setReuseDate] = useState<Date | null>(new Date());
  const [batchCode, setBatchCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchAvailableOffcuts();
  }, []);

  const fetchAvailableOffcuts = async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/available-offcuts`);
      if (!response.ok) throw new Error('Failed to fetch offcuts');
      const data = await response.json();
      setOffcuts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch offcuts');
    }
  };

  const handleToggleOffcut = (offcutId: number) => {
    setSelectedOffcuts(prev => 
      prev.includes(offcutId)
        ? prev.filter(id => id !== offcutId)
        : [...prev, offcutId]
    );
  };

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

  const handleSubmit = async () => {
    const formattedCode = formatBatchCode(batchCode);

    if (!isValidBatchCode(formattedCode)) {
      setError('Invalid batch code format. Please use format "BO003643" or just "3643"');
      return;
    }

    if (!batchCode.trim() || !reuseDate || selectedOffcuts.length === 0) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Check if batch exists
      const exists = await checkBatchExists(formattedCode);
      if (!exists) {
        setError(`Batch code ${formattedCode} not found in database`);
        return;
      }

      const response = await fetch(`${API_URL}/api/admin/update-offcut-usage`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          offcut_ids: selectedOffcuts,
          batch_code: formattedCode,
          reuse_date: reuseDate.toISOString().split('T')[0],
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to update offcut usage');
      }

      setSuccess('Offcut usage history updated successfully');
      setSelectedOffcuts([]);
      setBatchCode('');
      fetchAvailableOffcuts(); // Refresh the list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Update Offcut Usage History
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            label="Batch Code"
            placeholder="e.g., BO003643"
            value={batchCode}
            onChange={(e) => setBatchCode(e.target.value)}
            onBlur={(e) => setBatchCode(formatBatchCode(e.target.value))}
            sx={{ mb: 2 }}
          />
          
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DatePicker
              label="Reuse Date"
              value={reuseDate}
              onChange={(newValue) => setReuseDate(newValue)}
              sx={{ width: '100%' }}
            />
          </LocalizationProvider>
        </Box>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox">
                  <Checkbox
                    indeterminate={selectedOffcuts.length > 0 && selectedOffcuts.length < offcuts.length}
                    checked={selectedOffcuts.length === offcuts.length}
                    onChange={() => {
                      if (selectedOffcuts.length === offcuts.length) {
                        setSelectedOffcuts([]);
                      } else {
                        setSelectedOffcuts(offcuts.map(o => o.offcut_id));
                      }
                    }}
                  />
                </TableCell>
                <TableCell>Legacy ID</TableCell>
                <TableCell>Material Profile</TableCell>
                <TableCell>Length (mm)</TableCell>
                <TableCell>Reuse Count</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {offcuts.map((offcut) => (
                <TableRow key={offcut.offcut_id}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedOffcuts.includes(offcut.offcut_id)}
                      onChange={() => handleToggleOffcut(offcut.offcut_id)}
                    />
                  </TableCell>
                  <TableCell>{offcut.legacy_offcut_id}</TableCell>
                  <TableCell>{offcut.material_profile}</TableCell>
                  <TableCell>{offcut.length_mm}</TableCell>
                  <TableCell>{offcut.reuse_count}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Box sx={{ mt: 3 }}>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={loading || selectedOffcuts.length === 0}
          >
            {loading ? <CircularProgress size={24} /> : 'Update Usage History'}
          </Button>
        </Box>
      </Paper>

      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}
    </Box>
  );
};

export default OffcutUsageHistory;