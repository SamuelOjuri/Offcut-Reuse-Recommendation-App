import React, { useState, useEffect, useCallback } from 'react';
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
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

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

interface BatchReport {
  batch_code: string;
  batch_date: string;
  saw_name: string;
  item_code: string;
  item_description: string;
  quantity: number;
  input_length: number;
  bar_length: number;
  used_length: number;
  offcut_length: number;
  total_offcut_length: number;
  double_cut: boolean;
  waste_percentage: number;
  efficiency: number;
  source_file: string;
}

const Reports: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [summaryMetrics, setSummaryMetrics] = useState<SummaryMetrics[]>([]);
  const [offcuts, setOffcuts] = useState<OffcutInventory[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<string>('All');
  const [materialProfiles, setMaterialProfiles] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [itemsList, setItemsList] = useState<Array<{item_code: string, item_description: string}>>([]);
  const [batchReport, setBatchReport] = useState<BatchReport[]>([]);
  const [dateRange, setDateRange] = useState<{
    start: Date | null;
    end: Date | null;
  }>({
    start: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
    end: new Date()
  });

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

  // Fetch items list
  const fetchItemsList = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/reports/items`);
      if (!response.ok) throw new Error('Failed to fetch items list');
      const data = await response.json();
      setItemsList(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Fetch batch report
  const fetchBatchReport = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const start = dateRange.start?.toISOString().split('T')[0];
      const end = dateRange.end?.toISOString().split('T')[0];
      const response = await fetch(
        `${API_URL}/api/reports/batches?start_date=${start}&end_date=${end}`
      );
      if (!response.ok) throw new Error('Failed to fetch batch report');
      const data = await response.json();
      setBatchReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [dateRange]);

  useEffect(() => {
    if (tabValue === 0) fetchSummaryMetrics();
    if (tabValue === 1) fetchOffcuts();
    if (tabValue === 2) fetchItemsList();
    if (tabValue === 3) fetchBatchReport();
  }, [tabValue, dateRange, fetchBatchReport]);

  const handleDownload = (data: any[], filename: string) => {
    // Custom headers and order for batch report
    const batchReportFields = [
      'batch_code',
      'batch_date',
      'saw_name',
      'item_code',
      'item_description',
      'quantity',
      'input_length',
      'bar_length',
      'used_length',
      'offcut_length',
      'total_offcut_length',
      'double_cut',
      'waste_percentage',
      'efficiency',
      'source_file'
    ];

    const batchReportHeaders = {
      batch_code: 'Batch Code',
      batch_date: 'Date',
      saw_name: 'Saw Name',
      item_code: 'Item Code',
      item_description: 'Item Description',
      quantity: 'Quantity',
      input_length: 'Input Bar Length (mm)',
      bar_length: 'Bar Length Used (mm)',
      used_length: 'Total Length Used (mm)',
      offcut_length: 'Offcut Length (mm)',
      total_offcut_length: 'Total Offcut (mm)',
      double_cut: 'Double Cut',
      waste_percentage: 'Waste %',
      efficiency: 'Efficiency %',
      source_file: 'Source File'
    };

    const csvContent = 
      'data:text/csv;charset=utf-8,' + 
      (filename === 'batch_report' 
        ? batchReportFields.map(field => batchReportHeaders[field as keyof typeof batchReportHeaders]).join(',')
        : Object.keys(data[0]).join(',')
      ) + '\n' +
      data.map(row => 
        filename === 'batch_report'
          ? batchReportFields.map(field => row[field]).join(',')
          : Object.values(row).join(',')
      ).join('\n');
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${filename}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadPDF = (data: BatchReport[], filename: string) => {
    // Create PDF in landscape mode for better table fitting
    const doc = new jsPDF('landscape');
    
    // Add title with better positioning
    doc.setFontSize(20);
    doc.text('Batch Report', 14, 15);
    
    // Add date range and generation info with better spacing
    doc.setFontSize(11);
    doc.text(`Date Range: ${dateRange.start?.toLocaleDateString()} - ${dateRange.end?.toLocaleDateString()}`, 14, 25);
    doc.text(`Generated: ${new Date().toLocaleDateString()}`, 14, 32);

    // Create table with batch data - simplified columns for better readability
    const tableData = data.map(row => [
      row.batch_code,
      new Date(row.batch_date).toLocaleDateString(),
      row.saw_name,
      row.item_code,
      row.item_description.substring(0, 30), // Limit description length
      row.quantity.toString(),
      row.input_length.toString(),
      row.bar_length.toString(),
      row.used_length.toString(),
      row.offcut_length.toString(),
      row.total_offcut_length.toString(),
      row.double_cut ? 'Yes' : 'No',
      `${row.waste_percentage.toFixed(1)}%`,
      `${row.efficiency.toFixed(1)}%`
    ]);

    autoTable(doc, {
      head: [['Batch Code', 'Date', 'Saw', 'Item Code', 'Description', 'Qty', 'Input', 'Bar', 'Used', 'Offcut', 'Total Off.', 'D.Cut', 'Waste', 'Eff.']],
      body: tableData,
      startY: 40,
      styles: {
        fontSize: 8,
        cellPadding: 2,
        overflow: 'linebreak',
        halign: 'center'
      },
      headStyles: {
        fillColor: [66, 66, 66],
        fontSize: 8,
        fontStyle: 'bold',
        halign: 'center'
      },
      columnStyles: {
        0: { cellWidth: 25 }, // Batch Code
        1: { cellWidth: 20 }, // Date
        2: { cellWidth: 20 }, // Saw
        3: { cellWidth: 25 }, // Item Code
        4: { cellWidth: 35 }, // Description
        5: { cellWidth: 12 }, // Qty
        6: { cellWidth: 18 }, // Input
        7: { cellWidth: 18 }, // Bar
        8: { cellWidth: 18 }, // Used
        9: { cellWidth: 18 }, // Offcut
        10: { cellWidth: 18 }, // Total Offcut
        11: { cellWidth: 15 }, // Double Cut
        12: { cellWidth: 15 }, // Waste
        13: { cellWidth: 15 }  // Efficiency
      },
      theme: 'grid',
      tableWidth: 'auto',
      margin: { left: 10, right: 10 }
    });

    doc.save(`${filename}.pdf`);
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
        <Tab label="Items List" />
        <Tab label="Batch Report" />
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
                  { field: 'legacy_offcut_id', headerName: 'Offcut ID', type: 'string', flex: 1 },
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
              <DataGrid
                rows={itemsList.map((row, index) => ({ id: index, ...row }))}
                columns={[
                  { field: 'item_code', headerName: 'Item Code', flex: 1 },
                  { field: 'item_description', headerName: 'Item Description', flex: 2 }
                ]}
                autoHeight
                pageSizeOptions={[5, 10, 25, 50]}
                initialState={{
                  pagination: { paginationModel: { pageSize: 25 } },
                }}
              />
              
              <Button 
                variant="outlined" 
                onClick={() => handleDownload(itemsList, 'items_list')}
                sx={{ mt: 2 }}
              >
                Download Items List
              </Button>
            </Box>
          )}

          {tabValue === 3 && (
            <Box sx={{ mt: 3 }}>
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={12} sm={6}>
                  <LocalizationProvider dateAdapter={AdapterDateFns}>
                    <DatePicker
                      label="Start Date"
                      value={dateRange.start}
                      onChange={(newValue) => setDateRange(prev => ({ ...prev, start: newValue }))}
                      sx={{ width: '100%' }}
                    />
                  </LocalizationProvider>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <LocalizationProvider dateAdapter={AdapterDateFns}>
                    <DatePicker
                      label="End Date"
                      value={dateRange.end}
                      onChange={(newValue) => setDateRange(prev => ({ ...prev, end: newValue }))}
                      sx={{ width: '100%' }}
                    />
                  </LocalizationProvider>
                </Grid>
              </Grid>

              <DataGrid
                rows={batchReport.map((row, index) => ({ id: index, ...row }))}
                columns={[
                  { field: 'batch_code', headerName: 'Batch Code', flex: 1 },
                  { field: 'batch_date', headerName: 'Date', flex: 1 },
                  { field: 'saw_name', headerName: 'Saw Name', flex: 1 },
                  { field: 'item_code', headerName: 'Item Code', flex: 1 },
                  { field: 'item_description', headerName: 'Item Description', flex: 1.5 },
                  { field: 'quantity', headerName: 'Quantity', type: 'number', flex: 0.8 },
                  { field: 'input_length', headerName: 'Input Bar Length (mm)', type: 'number', flex: 1 },
                  { field: 'bar_length', headerName: 'Bar Length Used (mm)', type: 'number', flex: 1 },
                  { field: 'used_length', headerName: 'Total Length Used(mm)', type: 'number', flex: 1 },
                  { field: 'offcut_length', headerName: 'Offcut Length (mm)', type: 'number', flex: 1 },
                  { field: 'total_offcut_length', headerName: 'Total Offcut (mm)', type: 'number', flex: 1 },
                  { field: 'double_cut', headerName: 'Double Cut', type: 'boolean', flex: 0.8 },
                  { field: 'waste_percentage', headerName: 'Waste %', type: 'number', flex: 0.8 },
                  { field: 'efficiency', headerName: 'Efficiency %', type: 'number', flex: 0.8 },
                  { field: 'source_file', headerName: 'Source File', flex: 1.5 }
                ]}
                autoHeight
                pageSizeOptions={[10, 25, 50, 100]}
                initialState={{
                  pagination: { paginationModel: { pageSize: 25 } },
                }}
              />
              
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                <Button 
                  variant="outlined" 
                  onClick={() => handleDownload(batchReport, 'batch_report')}
                  sx={{ 
                    mx: 1,
                    minWidth: 180,
                    height: 45
                  }}
                >
                  Download CSV
                </Button>
                <Button 
                  variant="contained" 
                  onClick={() => handleDownloadPDF(batchReport, 'batch_report')}
                  sx={{ 
                    mx: 1,
                    minWidth: 180,
                    height: 45
                  }}
                >
                  Download PDF Report
                </Button>
              </Box>
            </Box>
          )}
        </>
      )}
    </Box>
  );
};

export default Reports; 