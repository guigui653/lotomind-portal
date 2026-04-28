import { useState } from 'react';
import {
    Box,
    Button,
    Grid,
    Paper,
    Typography,
    CircularProgress,
    Alert,
    LinearProgress,
    Chip,
} from '@mui/material';
import {
    SmartToy,
    CheckCircle,
    Warning,
    TrendingUp,
    Refresh,
} from '@mui/icons-material';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    Cell,
    PieChart,
    Pie,
} from 'recharts';
import { analysisService } from '../services/analysisService';
import type { GameAnalysisResponse } from '../types';

const ALL_NUMBERS = Array.from({ length: 25 }, (_, i) => i + 1);
const MAX_SELECTION = 15;

function GameAnalyzer() {
    const [selected, setSelected] = useState<number[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [result, setResult] = useState<GameAnalysisResponse | null>(null);

    const toggleNumber = (n: number) => {
        setSelected((prev) => {
            if (prev.includes(n)) return prev.filter((x) => x !== n);
            if (prev.length >= MAX_SELECTION) return prev;
            return [...prev, n].sort((a, b) => a - b);
        });
        setResult(null);
    };

    const analyzeGame = async () => {
        if (selected.length !== 15) return;
        setLoading(true);
        setError('');
        setResult(null);
        try {
            const data = await analysisService.analyzeMyGame(selected);
            setResult(data);
        } catch {
            setError('Erro ao analisar o jogo. Verifique se o servidor está online.');
        } finally {
            setLoading(false);
        }
    };

    const clearSelection = () => {
        setSelected([]);
        setResult(null);
        setError('');
    };

    const getScoreColor = (score: number) => {
        if (score >= 80) return '#00D9A6';
        if (score >= 60) return '#6C63FF';
        if (score >= 40) return '#FF9800';
        return '#f44336';
    };

    const PIE_COLORS = ['#6C63FF', '#00D9A6'];

    return (
        <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3, alignItems: 'center' }}>
                <Typography variant="h5" fontWeight={700} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <SmartToy color="primary" /> Simulador de Apostas
                </Typography>
                <Chip
                    label={`${selected.length} / 15 selecionados`}
                    color={selected.length === 15 ? 'success' : 'default'}
                    variant="outlined"
                    sx={{ fontWeight: 700 }}
                />
            </Box>

            <Grid container spacing={4}>
                {/* ── Left Column: Number Selector ── */}
                <Grid item xs={12} md={5}>
                    <Paper elevation={3} sx={{ p: 3, borderRadius: 2, mb: 3 }}>
                        <Typography variant="subtitle2" gutterBottom fontWeight={600} color="text.secondary">
                            SELECIONE 15 NÚMEROS
                        </Typography>
                        <Box sx={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(5, 1fr)',
                            gap: 1.5,
                            my: 2,
                        }}>
                            {ALL_NUMBERS.map((n) => {
                                const isSelected = selected.includes(n);
                                return (
                                    <Box
                                        key={n}
                                        onClick={() => toggleNumber(n)}
                                        sx={{
                                            width: 50,
                                            height: 50,
                                            borderRadius: '50%',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            fontWeight: 800,
                                            fontSize: '1rem',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s ease',
                                            bgcolor: isSelected
                                                ? 'primary.main'
                                                : 'rgba(255,255,255,0.05)',
                                            color: isSelected ? '#fff' : 'text.secondary',
                                            border: isSelected
                                                ? '2px solid transparent'
                                                : '2px solid rgba(255,255,255,0.1)',
                                            boxShadow: isSelected
                                                ? '0 4px 12px rgba(108,99,255,0.4)'
                                                : 'none',
                                            transform: isSelected ? 'scale(1.1)' : 'scale(1)',
                                            '&:hover': {
                                                transform: 'scale(1.15)',
                                                bgcolor: isSelected
                                                    ? 'primary.dark'
                                                    : 'rgba(108,99,255,0.15)',
                                            },
                                        }}
                                    >
                                        {n.toString().padStart(2, '0')}
                                    </Box>
                                );
                            })}
                        </Box>

                        <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
                            <Button
                                variant="contained"
                                fullWidth
                                onClick={analyzeGame}
                                disabled={selected.length !== 15 || loading}
                                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SmartToy />}
                                sx={{
                                    background: 'linear-gradient(45deg, #6C63FF 30%, #00D9A6 90%)',
                                    py: 1.5,
                                    fontWeight: 800,
                                    boxShadow: '0 3px 5px 2px rgba(108, 99, 255, .3)',
                                }}
                            >
                                {loading ? 'ANALISANDO...' : 'ANALISAR JOGO'}
                            </Button>
                            <Button
                                variant="outlined"
                                onClick={clearSelection}
                                startIcon={<Refresh />}
                                sx={{ minWidth: 120 }}
                            >
                                Limpar
                            </Button>
                        </Box>
                    </Paper>

                    {/* ── Selected Numbers Summary ── */}
                    {selected.length > 0 && (
                        <Paper elevation={2} sx={{ p: 2, borderRadius: 2 }}>
                            <Typography variant="subtitle2" fontWeight={600} color="text.secondary" gutterBottom>
                                SEUS NÚMEROS
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 0.8, flexWrap: 'wrap' }}>
                                {selected.map((n) => (
                                    <Box key={n} sx={{
                                        width: 32, height: 32, borderRadius: '50%',
                                        bgcolor: 'primary.main', color: '#fff',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        fontWeight: 700, fontSize: '0.8rem',
                                    }}>
                                        {n.toString().padStart(2, '0')}
                                    </Box>
                                ))}
                            </Box>
                        </Paper>
                    )}
                </Grid>

                {/* ── Right Column: Results ── */}
                <Grid item xs={12} md={7}>
                    {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

                    {result ? (
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                            {/* ── Score Card ── */}
                            <Paper
                                elevation={3}
                                sx={{
                                    p: 4,
                                    borderRadius: 3,
                                    textAlign: 'center',
                                    position: 'relative',
                                    overflow: 'hidden',
                                    background: `linear-gradient(135deg, ${getScoreColor(result.score)}10 0%, transparent 100%)`,
                                    border: `2px solid ${getScoreColor(result.score)}40`,
                                }}
                            >
                                <Typography variant="overline" color="text.secondary" fontWeight={600}>
                                    VEREDITO DO PARCEIRO
                                </Typography>
                                <Box sx={{ position: 'relative', display: 'inline-flex', my: 2 }}>
                                    <CircularProgress
                                        variant="determinate"
                                        value={result.score}
                                        size={120}
                                        thickness={6}
                                        sx={{ color: getScoreColor(result.score) }}
                                    />
                                    <Box sx={{
                                        position: 'absolute', top: 0, left: 0, bottom: 0, right: 0,
                                        display: 'flex', flexDirection: 'column',
                                        alignItems: 'center', justifyContent: 'center',
                                    }}>
                                        <Typography variant="h3" fontWeight={800} sx={{ color: getScoreColor(result.score) }}>
                                            {result.score}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">/100</Typography>
                                    </Box>
                                </Box>
                                <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 400, mx: 'auto' }}>
                                    {result.score >= 80
                                        ? 'Excelente alinhamento com as tendências!'
                                        : result.score >= 60
                                            ? 'Bom potencial, com espaço para melhorias.'
                                            : result.score >= 40
                                                ? 'Precisa de ajustes para melhorar.'
                                                : 'Considere revisar sua seleção.'}
                                </Typography>
                            </Paper>

                            {/* ── Strengths & Weaknesses ── */}
                            <Grid container spacing={2}>
                                <Grid item xs={12} md={6}>
                                    <Paper elevation={2} sx={{ p: 2.5, borderRadius: 2, height: '100%' }}>
                                        <Typography variant="subtitle2" fontWeight={700} sx={{
                                            display: 'flex', alignItems: 'center', gap: 1, mb: 2,
                                            color: '#00D9A6',
                                        }}>
                                            <CheckCircle fontSize="small" /> Pontos Fortes
                                        </Typography>
                                        {result.pontos_fortes.length > 0 ? (
                                            result.pontos_fortes.map((p, i) => (
                                                <Box key={i} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'flex-start' }}>
                                                    <Box sx={{
                                                        width: 6, height: 6, borderRadius: '50%',
                                                        bgcolor: '#00D9A6', mt: 0.8, flexShrink: 0,
                                                    }} />
                                                    <Typography variant="body2" color="text.secondary">{p}</Typography>
                                                </Box>
                                            ))
                                        ) : (
                                            <Typography variant="body2" color="text.disabled">Nenhum ponto forte identificado</Typography>
                                        )}
                                    </Paper>
                                </Grid>
                                <Grid item xs={12} md={6}>
                                    <Paper elevation={2} sx={{ p: 2.5, borderRadius: 2, height: '100%' }}>
                                        <Typography variant="subtitle2" fontWeight={700} sx={{
                                            display: 'flex', alignItems: 'center', gap: 1, mb: 2,
                                            color: '#f44336',
                                        }}>
                                            <Warning fontSize="small" /> Pontos Fracos
                                        </Typography>
                                        {result.pontos_fracos.length > 0 ? (
                                            result.pontos_fracos.map((p, i) => (
                                                <Box key={i} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'flex-start' }}>
                                                    <Box sx={{
                                                        width: 6, height: 6, borderRadius: '50%',
                                                        bgcolor: '#f44336', mt: 0.8, flexShrink: 0,
                                                    }} />
                                                    <Typography variant="body2" color="text.secondary">{p}</Typography>
                                                </Box>
                                            ))
                                        ) : (
                                            <Typography variant="body2" color="text.disabled">Nenhum ponto fraco identificado</Typography>
                                        )}
                                    </Paper>
                                </Grid>
                            </Grid>

                            {/* ── Score Breakdown ── */}
                            {result.graficos.score_breakdown.length > 0 && (
                                <Paper elevation={2} sx={{ p: 3, borderRadius: 2 }}>
                                    <Typography variant="subtitle2" fontWeight={700} gutterBottom sx={{
                                        display: 'flex', alignItems: 'center', gap: 1, mb: 2,
                                    }}>
                                        <TrendingUp fontSize="small" color="primary" /> Detalhamento do Score
                                    </Typography>
                                    {result.graficos.score_breakdown.map((item) => (
                                        <Box key={item.name} sx={{ mb: 2 }}>
                                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                                                <Typography variant="body2" fontWeight={600}>{item.name}</Typography>
                                                <Typography variant="body2" color="text.secondary">
                                                    {item.score}/{item.max}
                                                </Typography>
                                            </Box>
                                            <LinearProgress
                                                variant="determinate"
                                                value={((item.score ?? 0) / (item.max ?? 25)) * 100}
                                                sx={{
                                                    height: 8,
                                                    borderRadius: 4,
                                                    bgcolor: 'rgba(255,255,255,0.05)',
                                                    '& .MuiLinearProgress-bar': {
                                                        borderRadius: 4,
                                                        background: (item.score ?? 0) >= 20
                                                            ? 'linear-gradient(90deg, #00D9A6, #6C63FF)'
                                                            : (item.score ?? 0) >= 10
                                                                ? 'linear-gradient(90deg, #FF9800, #FFB74D)'
                                                                : 'linear-gradient(90deg, #f44336, #ff7961)',
                                                    },
                                                }}
                                            />
                                        </Box>
                                    ))}
                                </Paper>
                            )}

                            {/* ── Heat Match Chart ── */}
                            {result.graficos.heat_match.length > 0 && (
                                <Paper elevation={2} sx={{ p: 3, borderRadius: 2 }}>
                                    <Typography variant="subtitle2" fontWeight={700} gutterBottom sx={{
                                        display: 'flex', alignItems: 'center', gap: 1, mb: 2,
                                    }}>
                                        🔥 Match com a Estatística
                                    </Typography>
                                    <Box sx={{ height: 250, width: '100%' }}>
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={result.graficos.heat_match} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                                                <XAxis dataKey="name" stroke="#888" fontSize={11} />
                                                <YAxis domain={[0, 100]} stroke="#888" fontSize={11} />
                                                <Tooltip
                                                    cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                                                    contentStyle={{
                                                        borderRadius: 8,
                                                        border: 'none',
                                                        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                                                        background: '#1e1e2e',
                                                    }}
                                                />
                                                <Bar dataKey="seu_calor" name="Score Calor" fill="#6C63FF" radius={[4, 4, 0, 0]} barSize={20} />
                                                <Bar dataKey="media" name="Média Geral" fill="#00D9A6" radius={[4, 4, 0, 0]} barSize={20} opacity={0.5} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </Box>
                                </Paper>
                            )}

                            {/* ── Composition Pie ── */}
                            {result.graficos.composicao.length > 0 && (
                                <Grid container spacing={2}>
                                    <Grid item xs={12} md={4}>
                                        <Paper elevation={2} sx={{ p: 3, borderRadius: 2, textAlign: 'center' }}>
                                            <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                                                Par / Ímpar
                                            </Typography>
                                            <Box sx={{ height: 150 }}>
                                                <ResponsiveContainer width="100%" height="100%">
                                                    <PieChart>
                                                        <Pie
                                                            data={result.graficos.composicao}
                                                            cx="50%"
                                                            cy="50%"
                                                            innerRadius={35}
                                                            outerRadius={60}
                                                            dataKey="value"
                                                            label={({ name, value }) => `${name}: ${value}`}
                                                            labelLine={false}
                                                        >
                                                            {result.graficos.composicao.map((_entry, idx) => (
                                                                <Cell key={`cell-${idx}`} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                                                            ))}
                                                        </Pie>
                                                        <Tooltip />
                                                    </PieChart>
                                                </ResponsiveContainer>
                                            </Box>
                                        </Paper>
                                    </Grid>
                                    <Grid item xs={12} md={8}>
                                        <Paper elevation={2} sx={{ p: 3, borderRadius: 2 }}>
                                            <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                                                📊 Métricas Rápidas
                                            </Typography>
                                            <Grid container spacing={1.5} sx={{ mt: 1 }}>
                                                {[
                                                    { label: 'Soma', value: result.metricas.soma, sub: `Média: ${result.metricas.soma_media}` },
                                                    { label: 'Primos', value: result.metricas.primos, sub: 'Ideal: 5-6' },
                                                    { label: 'Repetições', value: result.metricas.repeticoes_ultimo, sub: `Conc. #${result.metricas.ultimo_concurso}` },
                                                    { label: 'Calor Médio', value: `${result.metricas.calor_medio}%`, sub: 'Dos últimos 15 conc.' },
                                                ].map((m) => (
                                                    <Grid item xs={6} key={m.label}>
                                                        <Box sx={{
                                                            p: 1.5,
                                                            borderRadius: 2,
                                                            bgcolor: 'rgba(108,99,255,0.05)',
                                                            border: '1px solid rgba(108,99,255,0.1)',
                                                        }}>
                                                            <Typography variant="caption" color="text.secondary">{m.label}</Typography>
                                                            <Typography variant="h6" fontWeight={700}>{m.value}</Typography>
                                                            <Typography variant="caption" color="text.disabled">{m.sub}</Typography>
                                                        </Box>
                                                    </Grid>
                                                ))}
                                            </Grid>
                                        </Paper>
                                    </Grid>
                                </Grid>
                            )}

                            {/* ── Partner Opinion ── */}
                            <Paper
                                elevation={3}
                                sx={{
                                    p: 3,
                                    borderRadius: 3,
                                    background: 'linear-gradient(135deg, rgba(0,217,166,0.06) 0%, rgba(108,99,255,0.06) 100%)',
                                    border: '1px solid rgba(0,217,166,0.2)',
                                }}
                            >
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                                    <SmartToy sx={{ color: '#00D9A6', fontSize: 28 }} />
                                    <Typography variant="subtitle1" fontWeight={700} sx={{ color: '#00D9A6' }}>
                                        🧠 Opinião do Parceiro
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
                                        __html: result.opiniao_do_parceiro
                                            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                    }}
                                />
                            </Paper>
                        </Box>
                    ) : (
                        !loading && !error && (
                            <Box sx={{
                                height: 400,
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                border: '3px dashed #e0e0e0',
                                borderRadius: 4,
                                color: 'text.secondary',
                                bgcolor: 'rgba(255,255,255,0.02)',
                            }}>
                                <SmartToy sx={{ fontSize: 60, mb: 2, color: 'rgba(255,255,255,0.1)' }} />
                                <Typography variant="h6" color="text.disabled">Selecione 15 números ao lado</Typography>
                                <Typography variant="body2" color="text.disabled">e clique em "Analisar Jogo" para receber o veredito</Typography>
                            </Box>
                        )
                    )}
                </Grid>
            </Grid>
        </Box>
    );
}

export default GameAnalyzer;
