import { useState } from 'react';
import { Box, Button, Paper, TextField, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import { useAuthStore } from '../store/useAuthStore';

function Login() {
    const navigate = useNavigate();
    const setUser = useAuthStore((s) => s.setUser);

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await authService.login({ email, password });
            setUser(response);
            navigate('/dashboard');
        } catch {
            setError('Credenciais inválidas. Tente novamente.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box
            sx={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'linear-gradient(135deg, #0F0F1A 0%, #1A1A2E 50%, #16213E 100%)',
            }}
        >
            <Paper
                component="form"
                onSubmit={handleSubmit}
                sx={{
                    p: 5,
                    width: 400,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 3,
                    borderRadius: 4,
                }}
            >
                <Typography variant="h4" fontWeight={700} textAlign="center" color="primary">
                    🧠 LotoMind
                </Typography>
                <Typography variant="body2" textAlign="center" color="text.secondary">
                    Enterprise Analytics Platform
                </Typography>

                <TextField
                    label="Email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    fullWidth
                />
                <TextField
                    label="Senha"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    fullWidth
                />

                {error && (
                    <Typography variant="body2" color="error" textAlign="center">
                        {error}
                    </Typography>
                )}

                <Button
                    type="submit"
                    variant="contained"
                    size="large"
                    disabled={loading}
                    fullWidth
                    sx={{ py: 1.5, fontWeight: 600 }}
                >
                    {loading ? 'Entrando...' : 'Entrar'}
                </Button>
            </Paper>
        </Box>
    );
}

export default Login;
