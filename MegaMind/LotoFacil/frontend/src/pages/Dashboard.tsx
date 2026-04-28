import { useEffect, useState, useCallback, useRef } from 'react';
import {
    Grid, Paper, Typography, Button, Box, Snackbar, Alert, CircularProgress, Chip,
} from '@mui/material';
import {
    TrendingUp as TrendingUpIcon,
    Casino as CasinoIcon,
    Analytics as AnalyticsIcon,
    Sync as SyncIcon,
    CheckCircleOutline,
    SmartToy as SmartToyIcon,
} from '@mui/icons-material';
import api from '../services/api';

interface DashboardStats {
    total_contests: number;
    latest_contest: number;
    total_bets: number;
    model_accuracy: string;
}

const SILENT_REFRESH_INTERVAL = 60_000; // 60s

function Dashboard() {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [syncing, setSyncing] = useState(false);
    const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
        open: false, message: '', severity: 'success',
    });
    const lastKnownTimestamp = useRef<string | null>(null);

    const fetchStats = useCallback(async () => {
        try {
            const { data } = await api.get('/sync-results/stats');
            setStats(data);
        } catch {
            console.error('Failed to fetch stats');
        }
    }, []);

    useEffect(() => {
        fetchStats();
    }, [fetchStats]);

    // ── Silent Refresh: poll /last-update and auto-reload stats ──
    useEffect(() => {
        const checkForUpdates = async () => {
            try {
                const { data } = await api.get('/last-update');
                const newTimestamp = data.last_update;

                if (newTimestamp && lastKnownTimestamp.current && newTimestamp !== lastKnownTimestamp.current) {
                    // New data detected! Silently refresh stats
                    await fetchStats();
                    setSnackbar({
                        open: true,
                        message: '🔄 Dados atualizados automaticamente!',
                        severity: 'info',
                    });
                }

                lastKnownTimestamp.current = newTimestamp;
            } catch {
                // Silently ignore poll failures
            }
        };

        // Initial check
        checkForUpdates();

        const interval = setInterval(checkForUpdates, SILENT_REFRESH_INTERVAL);
        return () => clearInterval(interval);
    }, [fetchStats]);

    const handleSync = async () => {
        setSyncing(true);
        try {
            const { data } = await api.post('/sync-results', null, { timeout: 120_000 });
            setSnackbar({ open: true, message: data.message, severity: 'success' });
            await fetchStats();

            // Trigger the MainLayout badge refresh
            const win = window as unknown as Record<string, unknown>;
            if (typeof win.__refreshLastUpdate === 'function') {
                (win.__refreshLastUpdate as () => Promise<void>)();
            }
        } catch {
            setSnackbar({ open: true, message: 'Erro ao sincronizar resultados.', severity: 'error' });
        } finally {
            setSyncing(false);
        }
    };

    const cards = [
        {
            title: 'Concursos Analisados',
            value: stats ? stats.total_contests.toLocaleString('pt-BR') : '—',
            icon: <AnalyticsIcon />,
            color: '#6C63FF',
        },
        {
            title: 'Último Concurso',
            value: stats ? `#${stats.latest_contest.toLocaleString('pt-BR')}` : '—',
            icon: <TrendingUpIcon />,
            color: '#00D9A6',
        },
        {
            title: 'Apostas Registradas',
            value: stats ? stats.total_bets.toLocaleString('pt-BR') : '—',
            icon: <CasinoIcon />,
            color: '#FFD93D',
        },
    ];

    return (
        <>
            <Typography variant="h5" fontWeight={700} gutterBottom>
                Dashboard
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Visão geral do LotoMind Enterprise
                {lastKnownTimestamp.current && (
                    <Chip
                        icon={<CheckCircleOutline sx={{ fontSize: 14 }} />}
                        label="Auto-refresh ativo"
                        size="small"
                        variant="outlined"
                        sx={{ ml: 2, fontSize: '0.7rem', height: 22, color: '#00D9A6', borderColor: 'rgba(0,217,166,0.3)' }}
                    />
                )}
            </Typography>

            <Button
                variant="contained"
                startIcon={syncing ? <CircularProgress size={20} color="inherit" /> : <SyncIcon />}
                onClick={handleSync}
                disabled={syncing}
                sx={{
                    mb: 4,
                    background: 'linear-gradient(135deg, #6C63FF, #00D9A6)',
                    fontWeight: 600,
                    textTransform: 'none',
                    '&:hover': {
                        background: 'linear-gradient(135deg, #5A52E0, #00C494)',
                    },
                }}
            >
                {syncing ? 'Sincronizando...' : 'Sincronizar Resultados'}
            </Button>

            {/* ── Dica do Consultor (New Component) ── */}
            <Paper
                elevation={3}
                sx={{
                    p: 3,
                    mb: 4,
                    borderRadius: 3,
                    background: 'linear-gradient(135deg, rgba(0,217,166,0.08) 0%, rgba(108,99,255,0.08) 100%)',
                    border: '1px solid rgba(0,217,166,0.2)',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 2,
                }}
            >
                <SmartToyIcon sx={{ color: '#00D9A6', fontSize: 40, mt: 0.5 }} />
                <Box>
                    <Typography variant="subtitle1" fontWeight={700} sx={{ color: '#00D9A6', mb: 0.5 }}>
                        Dica do Sócio
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                        "Parceiro, lembre-se: a estratégia <strong>Equilibrada</strong> agora segue rigorosamente a regra de <strong>8 Ímpares e 7 Pares</strong>.
                        Essa é a distribuição que mais sai estatisticamente. Mantenha a constância e boa sorte!"
                    </Typography>
                </Box>
            </Paper>

            <Grid container spacing={3}>
                {cards.map(({ title, value, icon, color }) => (
                    <Grid item xs={12} sm={4} key={title}>
                        <Paper
                            sx={{
                                p: 3,
                                display: 'flex',
                                alignItems: 'center',
                                gap: 2,
                                borderRadius: 3,
                                borderLeft: `4px solid ${color}`,
                            }}
                        >
                            <Paper
                                sx={{
                                    p: 1.5,
                                    borderRadius: 2,
                                    bgcolor: `${color}20`,
                                    color,
                                    display: 'flex',
                                }}
                            >
                                {icon}
                            </Paper>
                            <div>
                                <Typography variant="body2" color="text.secondary">
                                    {title}
                                </Typography>
                                <Typography variant="h5" fontWeight={700}>
                                    {value}
                                </Typography>
                            </div>
                        </Paper>
                    </Grid>
                ))}
            </Grid>

            <Snackbar
                open={snackbar.open}
                autoHideDuration={5000}
                onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert
                    severity={snackbar.severity}
                    variant="filled"
                    onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
                >
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </>
    );
}

export default Dashboard;
