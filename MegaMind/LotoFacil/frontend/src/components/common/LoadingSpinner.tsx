import { Box, CircularProgress, Typography } from '@mui/material';

interface LoadingSpinnerProps {
    message?: string;
}

function LoadingSpinner({ message = 'Carregando...' }: LoadingSpinnerProps) {
    return (
        <Box
            sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                py: 8,
                gap: 2,
            }}
        >
            <CircularProgress size={48} />
            <Typography variant="body2" color="text.secondary">
                {message}
            </Typography>
        </Box>
    );
}

export default LoadingSpinner;
