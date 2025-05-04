import React, { useState } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  TextField,
  List,
  ListItem,
  ListItemText,
  Paper,
  CircularProgress,
  Divider,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import SearchIcon from '@mui/icons-material/Search';
import axios from 'axios';

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [processingLogs, setProcessingLogs] = useState([]);

  const handleFileUpload = async (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setLoading(true);
      setProcessingLogs([]);
      
      const formData = new FormData();
      formData.append('file', selectedFile);

      try {
        const response = await axios.post('http://localhost:8000/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        setUploadStatus('Файл успешно загружен!');
        setProcessingLogs(response.data.logs);
      } catch (error) {
        setUploadStatus('Ошибка при загрузке файла');
        if (error.response?.data?.logs) {
          setProcessingLogs(error.response.data.logs);
        }
        console.error('Upload error:', error);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`http://localhost:8000/search?query=${encodeURIComponent(searchQuery)}`);
      setResults(response.data.results);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Media Search
        </Typography>

        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Box sx={{ mb: 2 }}>
            <input
              accept="audio/*,video/*"
              style={{ display: 'none' }}
              id="raised-button-file"
              type="file"
              onChange={handleFileUpload}
            />
            <label htmlFor="raised-button-file">
              <Button
                variant="contained"
                component="span"
                startIcon={<CloudUploadIcon />}
                disabled={loading}
              >
                Загрузить медиафайл
              </Button>
            </label>
            {uploadStatus && (
              <Typography color="text.secondary" sx={{ mt: 1 }}>
                {uploadStatus}
              </Typography>
            )}
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              label="Поиск"
              variant="outlined"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button
              variant="contained"
              onClick={handleSearch}
              disabled={loading}
              startIcon={<SearchIcon />}
            >
              Поиск
            </Button>
          </Box>
        </Paper>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
            <CircularProgress />
          </Box>
        )}

        {processingLogs.length > 0 && (
          <Paper elevation={3} sx={{ p: 2, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Лог обработки файла
            </Typography>
            <List>
              {processingLogs.map((log, index) => (
                <React.Fragment key={index}>
                  <ListItem>
                    <ListItemText
                      primary={log.message}
                      secondary={`${log.stage} - ${formatTimestamp(log.timestamp)}`}
                    />
                  </ListItem>
                  {index < processingLogs.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </Paper>
        )}

        {results.length > 0 && (
          <Paper elevation={3} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Результаты поиска
            </Typography>
            <List>
              {results.map((result, index) => (
                <ListItem key={index}>
                  <ListItemText
                    primary={result.filename}
                    secondary={result.transcription}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        )}
      </Box>
    </Container>
  );
}

export default App; 