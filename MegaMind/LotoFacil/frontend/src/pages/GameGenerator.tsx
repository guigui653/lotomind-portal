import { useState, useEffect } from 'react';
import {
    Box,
    Button,
    Grid,
    Paper,
    Typography,
    CircularProgress,
    Chip,
    Alert,
    Snackbar,
    List,
    ListItem,
    Divider,
    ToggleButton,
    ToggleButtonGroup
} from '@mui/material';
import {
    Psychology,
    AutoAwesome,
    Save as SaveIcon,
    History as HistoryIcon,
    TrendingUp,
    Casino,
    Balance,
    LocalFireDepartment,
    AcUnit,
    SmartToy
} from '@mui/icons-material';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../services/api';

interface ChartData {
    name: string;
    freq: number;
}

interface PredictionResponse {
    game: number[];
    analysis: {
        hot: number[];
        cold: number[];
        medium: number[];
        charts?: {
            hot: ChartData[];
            cold: ChartData[];
        };
    };
    strategy: {
        description: string;
        composition: {
            hot: number;
            medium: number;
            cold: number;
        };
    };
    analise_do_consultor?: string;
    error?: string;
}

interface SavedGame {
    id: number;
    numbers: number[];
    concurso_alvo?: number;
    created_at: string;
    strategy_name?: string;
}

function GameGenerator() {
    const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [savedGames, setSavedGames] = useState<SavedGame[]>([]);
    const [showHistory, setShowHistory] = useState(false);
    const [snackbar, setSnackbar] = useState<{ open: boolean, message: string, severity: 'success' | 'error' }>({ open: false, message: '', severity: 'success' });
    const [strategy, setStrategy] = useState('balanced');

    useEffect(() => {
        fetchHistory();
    }, []);

    const fetchHistory = async () => {
        try {
            const { data } = await api.get('/predictions');
            setSavedGames(data);
        } catch (err) {
            console.error('Erro ao buscar histórico', err);
        }
    };

    const generateGame = async () => {
        setLoading(true);
        setError('');
        setPrediction(null);
        try {
            const { data } = await api.get(`/generate-prediction?strategy=${strategy}`);
            if (data.error) {
                setError(data.error);
            } else {
                setPrediction(data);
            }
        } catch {
            setError('Erro ao gerar palpite. Verifique se o servidor está online.');
        } finally {
            setLoading(false);
        }
    };

    const saveGame = async () => {
        if (!prediction) return;
        setSaving(true);
        try {
            await api.post('/predictions', {
                numbers: prediction.game,
                strategy_name: strategy
            });
            setSnackbar({ open: true, message: 'Palpite salvo com sucesso!', severity: 'success' });
            fetchHistory();
        } catch {
            setSnackbar({ open: true, message: 'Erro ao salvar palpite.', severity: 'error' });
        } finally {
            setSaving(false);
        }
    };

    const getBallColor = (num: number) => {
        if (!prediction) return '#e0e0e0';
        // Strategy specific colors or general logic
        if (prediction.analysis.hot.includes(num)) return '#f44336'; // Red (Hot)
        if (prediction.analysis.cold.includes(num)) return '#2196f3'; // Blue (Cold)
        return '#9e9e9e'; // Grey (Medium)
    };

    const handleStrategyChange = (
        event: React.MouseEvent<HTMLElement>,
        newStrategy: string,
    ) => {
        if (newStrategy !== null) {
            setStrategy(newStrategy);
        }
    };

    return (
        <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h5" fontWeight={700} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Psychology color="primary" /> Gerador Inteligente
                </Typography>
                <Button
                    startIcon={<HistoryIcon />}
                    variant="outlined"
                    onClick={() => setShowHistory(!showHistory)}
                >
                    {showHistory ? 'Ocultar Histórico' : 'Ver Histórico'}
                </Button>
            </Box>

            <Grid container spacing={4}>
                {/* ── Left Column: Controls & History ──────────────── */}
                <Grid item xs={12} md={4}>
                    <Paper elevation={3} sx={{ p: 3, mb: 3, textAlign: 'center', borderRadius: 2 }}>
                        <Typography variant="subtitle2" gutterBottom fontWeight={600} color="text.secondary">
                            ESCOLHA SUA ESTRATÉGIA
                        </Typography>

                        <ToggleButtonGroup
                            value={strategy}
                            exclusive
                            onChange={handleStrategyChange}
                            orientation="vertical"
                            fullWidth
                            sx={{ mb: 3 }}
                        >
                            <ToggleButton value="balanced" aria-label="balanced" sx={{ justifyContent: 'flex-start', py: 1.5 }}>
                                <Balance sx={{ mr: 1.5 }} />
                                <Box sx={{ textAlign: 'left' }}>
                                    <Typography variant="body2" fontWeight={700}>Equilibrada</Typography>
                                    <Typography variant="caption" color="text.secondary">Mix Ideal</Typography>
                                </Box>
                            </ToggleButton>

                            <ToggleButton value="aggressive" aria-label="aggressive" sx={{ justifyContent: 'flex-start', py: 1.5 }}>
                                <LocalFireDepartment sx={{ mr: 1.5, color: '#f44336' }} />
                                <Box sx={{ textAlign: 'left' }}>
                                    <Typography variant="body2" fontWeight={700}>Agressiva</Typography>
                                    <Typography variant="caption" color="text.secondary">Foco nas Quentes</Typography>
                                </Box>
                            </ToggleButton>

                            <ToggleButton value="hot_cold" aria-label="hot_cold" sx={{ justifyContent: 'flex-start', py: 1.5 }}>
                                <AcUnit sx={{ mr: 1.5, color: '#2196f3' }} />
                                <Box sx={{ textAlign: 'left' }}>
                                    <Typography variant="body2" fontWeight={700}>Extremos</Typography>
                                    <Typography variant="caption" color="text.secondary">Apenas Quentes e Frias</Typography>
                                </Box>
                            </ToggleButton>

                            <ToggleButton value="random" aria-label="random" sx={{ justifyContent: 'flex-start', py: 1.5 }}>
                                <Casino sx={{ mr: 1.5 }} />
                                <Box sx={{ textAlign: 'left' }}>
                                    <Typography variant="body2" fontWeight={700}>Surpresinha</Typography>
                                    <Typography variant="caption" color="text.secondary">Aleatório Puro</Typography>
                                </Box>
                            </ToggleButton>
                        </ToggleButtonGroup>

                        <Button
                            variant="contained"
                            size="large"
                            fullWidth
                            onClick={generateGame}
                            disabled={loading}
                            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <AutoAwesome />}
                            sx={{
                                background: 'linear-gradient(45deg, #6C63FF 30%, #00D9A6 90%)',
                                py: 1.5,
                                fontWeight: 800,
                                fontSize: '1rem',
                                boxShadow: '0 3px 5px 2px rgba(108, 99, 255, .3)'
                            }}
                        >
                            {loading ? 'ANALISANDO...' : 'GERAR PALPITE'}
                        </Button>
                    </Paper>

                    {showHistory && savedGames.length > 0 && (
                        <Paper elevation={2} sx={{ p: 2, maxHeight: 400, overflowY: 'auto', borderRadius: 2 }}>
                            <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                                <HistoryIcon fontSize="small" /> Histórico Recente
                            </Typography>
                            <List dense disablePadding>
                                {savedGames.map((game, i) => (
                                    <Box key={game.id}>
                                        <ListItem sx={{ flexDirection: 'column', alignItems: 'flex-start', px: 0, py: 1.5 }}>
                                            <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', mb: 0.5 }}>
                                                <Typography variant="caption" color="text.secondary">
                                                    {new Date(game.created_at).toLocaleDateString()}
                                                </Typography>
                                                {game.strategy_name && (
                                                    <Chip label={game.strategy_name} size="small" variant="outlined" sx={{ height: 20, fontSize: '0.65rem' }} />
                                                )}
                                            </Box>
                                            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                                                {game.numbers.map(n => (
                                                    <Box key={n} sx={{
                                                        width: 22, height: 22, borderRadius: '50%',
                                                        bgcolor: '#f5f5f5', border: '1px solid #ddd',
                                                        fontSize: 10, display: 'flex', fontWeight: 'bold',
                                                        alignItems: 'center', justifyContent: 'center'
                                                    }}>
                                                        {n}
                                                    </Box>
                                                ))}
                                            </Box>
                                        </ListItem>
                                        {i < savedGames.length - 1 && <Divider />}
                                    </Box>
                                ))}
                            </List>
                        </Paper>
                    )}
                </Grid>

                {/* ── Right Column: Results & Charts ──────────────── */}
                <Grid item xs={12} md={8}>
                    {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

                    {prediction ? (
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                            {/* ── The Game ── */}
                            <Paper elevation={3} sx={{ p: 4, borderRadius: 2, position: 'relative', overflow: 'hidden' }}>
                                {/* Background decoration */}
                                <Box sx={{ position: 'absolute', top: -20, right: -20, opacity: 0.1, transform: 'rotate(15deg)' }}>
                                    <AutoAwesome sx={{ fontSize: 150, color: 'primary.main' }} />
                                </Box>

                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, position: 'relative' }}>
                                    <Chip
                                        label={prediction.strategy.description.split(':')[0]}
                                        color="primary"
                                        icon={<Psychology />}
                                        sx={{ fontWeight: 'bold' }}
                                    />
                                    <Button
                                        variant="outlined"
                                        startIcon={saving ? <CircularProgress size={16} /> : <SaveIcon />}
                                        onClick={saveGame}
                                        disabled={saving}
                                    >
                                        Salvar
                                    </Button>
                                </Box>

                                <Grid container spacing={2} justifyContent="center" sx={{ mb: 4, position: 'relative' }}>
                                    {prediction.game.map((num) => (
                                        <Grid item key={num}>
                                            <Box sx={{
                                                width: 50, height: 50, borderRadius: '50%',
                                                bgcolor: getBallColor(num), color: '#fff',
                                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                fontWeight: 800, fontSize: '1.2rem',
                                                boxShadow: '0 4px 6px rgba(0,0,0,0.2)',
                                                border: '2px solid rgba(255,255,255,0.2)'
                                            }}>
                                                {num.toString().padStart(2, '0')}
                                            </Box>
                                        </Grid>
                                    ))}
                                </Grid>

                                <Alert severity="info" icon={<Psychology fontSize="inherit" />} sx={{ bgcolor: 'rgba(33, 150, 243, 0.08)' }}>
                                    <Typography variant="body2" fontWeight={500}>{prediction.strategy.description}</Typography>
                                </Alert>
                            </Paper>

                            {/* ── Papo do Consultor ── */}
                            {prediction.analise_do_consultor && (
                                <Paper
                                    elevation={3}
                                    sx={{
                                        p: 3,
                                        borderRadius: 3,
                                        position: 'relative',
                                        background: 'linear-gradient(135deg, rgba(0,217,166,0.06) 0%, rgba(108,99,255,0.06) 100%)',
                                        border: '1px solid rgba(0,217,166,0.2)',
                                        '&::before': {
                                            content: '""',
                                            position: 'absolute',
                                            top: -10,
                                            left: 30,
                                            width: 20,
                                            height: 20,
                                            background: 'inherit',
                                            borderLeft: '1px solid rgba(0,217,166,0.2)',
                                            borderTop: '1px solid rgba(0,217,166,0.2)',
                                            transform: 'rotate(45deg)',
                                        }
                                    }}
                                >
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                                        <SmartToy sx={{ color: '#00D9A6', fontSize: 28 }} />
                                        <Typography variant="subtitle1" fontWeight={700} sx={{ color: '#00D9A6' }}>
                                            🧠 Papo do Consultor
                                        </Typography>
                                    </Box>
                                    <Typography
                                        variant="body2"
                                        sx={{
                                            lineHeight: 1.8,
                                            color: 'text.secondary',
                                            whiteSpace: 'pre-line',
                                            '& strong': { color: 'text.primary' },
                                        }}
                                        dangerouslySetInnerHTML={{
                                            __html: prediction.analise_do_consultor
                                                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                        }}
                                    />
                                </Paper>
                            )}

                            {/* ── Analysis Charts (only if relevant) ── */}
                            {strategy !== 'random' && prediction.analysis.charts?.hot && (
                                <Paper elevation={2} sx={{ p: 3, borderRadius: 2 }}>
                                    <Typography variant="h6" fontWeight={700} gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                                        <TrendingUp color="error" /> Frequência dos Números Quentes
                                    </Typography>

                                    <Box sx={{ height: 250, width: '100%' }}>
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={prediction.analysis.charts.hot} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                                                <XAxis dataKey="name" stroke="#8884d8" />
                                                <YAxis />
                                                <Tooltip
                                                    cursor={{ fill: '#f5f5f5' }}
                                                    contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
                                                />
                                                <Bar dataKey="freq" name="Frequência" fill="#f44336" radius={[4, 4, 0, 0]} barSize={40} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </Box>
                                </Paper>
                            )}
                        </Box>
                    ) : (
                        !loading && !error && (
                            <Box sx={{
                                height: 400, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                                border: '3px dashed #e0e0e0', borderRadius: 4, color: 'text.secondary', bgcolor: '#fafafa'
                            }}>
                                <AutoAwesome sx={{ fontSize: 60, mb: 2, color: '#e0e0e0' }} />
                                <Typography variant="h6" color="text.disabled">Selecione uma estratégia ao lado</Typography>
                                <Typography variant="body2" color="text.disabled">e clique em "Gerar Palpite" para começar</Typography>
                            </Box>
                        )
                    )}
                </Grid>
            </Grid>

            {/* Notification Toast */}
            <Snackbar
                open={snackbar.open}
                autoHideDuration={4000}
                onClose={() => setSnackbar({ ...snackbar, open: false })}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity} sx={{ width: '100%' }}>
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </Box>
    );
}

export default GameGenerator;
