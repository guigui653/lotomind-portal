import React from 'react';
import ReactDOM from 'react-dom/client';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import App from './App';
import './styles/global.css';

const darkTheme = createTheme({
    palette: {
        mode: 'dark',
        primary: { main: '#6C63FF' },
        secondary: { main: '#00D9A6' },
        background: {
            default: '#0F0F1A',
            paper: '#1A1A2E',
        },
    },
    typography: {
        fontFamily: '"Inter", sans-serif',
    },
    shape: {
        borderRadius: 12,
    },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <ThemeProvider theme={darkTheme}>
            <CssBaseline />
            <App />
        </ThemeProvider>
    </React.StrictMode>,
);
