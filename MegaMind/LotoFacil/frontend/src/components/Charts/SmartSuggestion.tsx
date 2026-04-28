import { useState } from 'react';
import {
    Paper, Typography, Box, Button, CircularProgress, Alert, Chip, Grid,
    Tooltip as MuiTooltip
} from '@mui/material';
import {
    Psychology, AutoAwesome, CheckCircle, TrendingUp
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import type { SmartSuggestionResponse } from '../../types';
import { analysisService } from '../../services/analysisService';

const PIE_COLORS = ['#AB47BC', '#26A69A'];

function SmartSuggestion() {
    const [suggestion, setSuggestion] = useState<SmartSuggestionResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const generateSuggestion = async () => {
        setLoading(true);
        setError('');
        try {
            const data = await analysisService.getSmartSuggestion();
            setSuggestion(data);
        } catch {
            setError('Erro ao gerar sugestão. Verifique se os dados estão sincronizados.');
        } finally {
            setLoading(false);
        }
    };

    const getBallColor = (num: number) => {
        if (!suggestion) return '#e0e0e0';
        const score = suggestion.metrics.heat_scores[String(num)] ?? 0;
        if (score > 0.7) return '#f44336';
        if (score > 0.4) return '#ff9800';
        return '#2196f3';
    };

    const pieData = suggestion ? [
        { name: 'Ímpares', value: suggestion.metrics.odd_count },
        { name: 'Pares', value: suggestion.metrics.even_count },
    ] : [];

    return (
        <Paper sx={{ p: 3, borderRadius: 3, position: 'relative', overflow: 'hidden' }}>
            {/* Background decoration */}
            <Box sx={{ position: 'absolute', top: -30, right: -30, opacity: 0.06 }}>
                <Psychology sx={{ fontSize: 200, color: 'primary.main' }} />
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, position: 'relative' }}>
                <Box>
                    <Typography variant="h6" fontWeight={700} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        🧠 Sugestão Inteligente por Probabilidade
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        Análise baseada em frequência, atraso, ímpar/par e repetição
                    </Typography>
                </Box>
                <Button
                    variant="contained"
                    onClick={generateSuggestion}
                    disabled={loading}
                    startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <AutoAwesome />}
                    sx={{
                        background: 'linear-gradient(45deg, #6C63FF 30%, #00D9A6 90%)',
                        fontWeight: 800,
                        px: 3,
                        py: 1.5,
                        boxShadow: '0 3px 8px rgba(108, 99, 255, .3)',
                    }}
                >
                    {loading ? 'CALCULANDO...' : 'GERAR SUGESTÃO'}
                </Button>
            </Box>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            {suggestion ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, position: 'relative' }}>
                    {/* Confidence Badge */}
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <Chip
                            icon={<TrendingUp />}
                            label={`Confiança: ${(suggestion.confidence * 100).toFixed(0)}%`}
                            color={suggestion.confidence >= 0.75 ? 'success' : suggestion.confidence >= 0.5 ? 'warning' : 'error'}
                            sx={{ fontWeight: 700 }}
                        />
                        <Chip
                            label={`Soma: ${suggestion.metrics.sum} (ideal: ${suggestion.metrics.sum_ideal_range[0]}-${suggestion.metrics.sum_ideal_range[1]})`}
                            variant="outlined"
                            size="small"
                        />
                        <Chip
                            label={`${suggestion.metrics.repetitions_from_last} repetições do #${suggestion.metrics.last_contest}`}
                            variant="outlined"
                            size="small"
                        />
                    </Box>

                    {/* The Game Numbers */}
                    <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', justifyContent: 'center', py: 2 }}>
                        {suggestion.game.map((num) => {
                            const isRepeated = suggestion.metrics.repeated_numbers.includes(num);
                            const isOdd = num % 2 !== 0;
                            return (
                                <MuiTooltip
                                    key={num}
                                    title={
                                        <Box sx={{ textAlign: 'center' }}>
                                            <Typography variant="body2" fontWeight={700}>Nº {num}</Typography>
                                            <Typography variant="caption">
                                                {isOdd ? 'Ímpar' : 'Par'} •
                                                Score: {(suggestion.metrics.combined_scores[String(num)] * 100).toFixed(0)}%
                                                {isRepeated && ' • 🔁 Repetido'}
                                            </Typography>
                                        </Box>
                                    }
                                    arrow
                                >
                                    <Box sx={{
                                        width: 52, height: 52,
                                        borderRadius: '50%',
                                        bgcolor: getBallColor(num),
                                        color: '#fff',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontWeight: 800,
                                        fontSize: '1.1rem',
                                        boxShadow: isRepeated
                                            ? '0 0 0 3px rgba(255,215,0,0.6), 0 4px 8px rgba(0,0,0,0.2)'
                                            : '0 4px 8px rgba(0,0,0,0.2)',
                                        border: isRepeated ? '2px solid #FFD700' : '2px solid rgba(255,255,255,0.2)',
                                        cursor: 'pointer',
                                        transition: 'transform 0.2s',
                                        '&:hover': { transform: 'scale(1.15)' },
                                    }}>
                                        {num.toString().padStart(2, '0')}
                                    </Box>
                                </MuiTooltip>
                            );
                        })}
                    </Box>

                    <Grid container spacing={3}>
                        {/* Pie Chart */}
                        <Grid item xs={12} md={4}>
                            <Box sx={{ textAlign: 'center' }}>
                                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                                    Ímpar vs Par
                                </Typography>
                                <ResponsiveContainer width="100%" height={180}>
                                    <PieChart>
                                        <Pie
                                            data={pieData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={40}
                                            outerRadius={70}
                                            dataKey="value"
                                            label={({ name, value }) => `${name}: ${value}`}
                                            labelLine={false}
                                        >
                                            {pieData.map((_entry, index) => (
                                                <Cell key={index} fill={PIE_COLORS[index]} />
                                            ))}
                                        </Pie>
                                        <Tooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            </Box>
                        </Grid>

                        {/* Filters Applied */}
                        <Grid item xs={12} md={8}>
                            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                                Filtros Aplicados
                            </Typography>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                {suggestion.filters_applied.map((filter, i) => (
                                    <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <CheckCircle sx={{ fontSize: 16, color: filter.startsWith('✅') ? '#4caf50' : '#ff9800' }} />
                                        <Typography variant="body2">{filter}</Typography>
                                    </Box>
                                ))}
                            </Box>
                        </Grid>
                    </Grid>

                    {/* Explanation */}
                    <Alert
                        severity="info"
                        icon={<Psychology fontSize="inherit" />}
                        sx={{ bgcolor: 'rgba(33, 150, 243, 0.08)', '& .MuiAlert-message': { width: '100%' } }}
                    >
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
                            {suggestion.explanation}
                        </Typography>
                    </Alert>
                </Box>
            ) : (
                !loading && !error && (
                    <Box sx={{
                        height: 200, display: 'flex', flexDirection: 'column',
                        alignItems: 'center', justifyContent: 'center',
                        border: '2px dashed rgba(255,255,255,0.1)', borderRadius: 3, color: 'text.secondary',
                    }}>
                        <Psychology sx={{ fontSize: 50, mb: 1, opacity: 0.3 }} />
                        <Typography variant="body2" color="text.disabled">
                            Clique em "Gerar Sugestão" para análise probabilística
                        </Typography>
                    </Box>
                )
            )}
        </Paper>
    );
}

export default SmartSuggestion;
