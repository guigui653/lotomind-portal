import { useMemo } from 'react';
import { Box, Paper, Typography, Tooltip as MuiTooltip } from '@mui/material';
import type { HeatmapResponse } from '../../types';

interface HeatmapGridProps {
    data: HeatmapResponse;
}

function HeatmapGrid({ data }: HeatmapGridProps) {
    const gridData = useMemo(() => {
        const maxFreq = Math.max(...data.frequencies, 1);
        const minFreq = Math.min(...data.frequencies);
        const range = maxFreq - minFreq || 1;

        return data.numbers.map((num, idx) => {
            const freq = data.frequencies[idx];
            const intensity = (freq - minFreq) / range;
            const isOdd = num % 2 !== 0;

            return { num, freq, intensity, isOdd };
        });
    }, [data]);

    const getColor = (intensity: number): string => {
        // Cold (blue) → Warm (yellow) → Hot (red)
        if (intensity > 0.75) return `rgba(244, 67, 54, ${0.6 + intensity * 0.4})`;
        if (intensity > 0.50) return `rgba(255, 152, 0, ${0.5 + intensity * 0.4})`;
        if (intensity > 0.25) return `rgba(255, 235, 59, ${0.4 + intensity * 0.3})`;
        return `rgba(33, 150, 243, ${0.3 + intensity * 0.3})`;
    };

    const contestsAnalyzed = data.metadata.contests_analyzed as number ?? '?';

    return (
        <Paper sx={{ p: 3, borderRadius: 3, bgcolor: 'background.paper' }}>
            <Typography variant="h6" fontWeight={700} gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                🔥 Mapa de Calor — Grade 5×5
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Frequência nos últimos {contestsAnalyzed} concursos •
                <Box component="span" sx={{ color: '#2196f3', fontWeight: 600 }}> Azul = Frio</Box> →
                <Box component="span" sx={{ color: '#f44336', fontWeight: 600 }}> Vermelho = Quente</Box>
            </Typography>

            {/* Legenda Par/Ímpar */}
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Box sx={{ width: 12, height: 12, borderRadius: '50%', border: '2px solid #AB47BC' }} />
                    <Typography variant="caption" color="text.secondary">Ímpar</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Box sx={{ width: 12, height: 12, borderRadius: 1, border: '2px solid #26A69A' }} />
                    <Typography variant="caption" color="text.secondary">Par</Typography>
                </Box>
            </Box>

            <Box sx={{
                display: 'grid',
                gridTemplateColumns: 'repeat(5, 1fr)',
                gap: 1.5,
                maxWidth: 420,
            }}>
                {gridData.map(({ num, freq, intensity, isOdd }) => (
                    <MuiTooltip
                        key={num}
                        title={
                            <Box sx={{ textAlign: 'center', p: 0.5 }}>
                                <Typography variant="body2" fontWeight={700}>
                                    Número {num.toString().padStart(2, '0')}
                                </Typography>
                                <Typography variant="body2">
                                    Saiu <strong>{freq}×</strong> nos últimos {contestsAnalyzed} concursos
                                </Typography>
                                <Typography variant="caption" sx={{ color: isOdd ? '#CE93D8' : '#80CBC4' }}>
                                    {isOdd ? '● Ímpar' : '■ Par'}
                                </Typography>
                            </Box>
                        }
                        arrow
                        placement="top"
                    >
                        <Box sx={{
                            position: 'relative',
                            aspectRatio: '1',
                            borderRadius: isOdd ? '50%' : 2,
                            bgcolor: getColor(intensity),
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                            border: `2px solid ${isOdd ? 'rgba(171,71,188,0.5)' : 'rgba(38,166,154,0.5)'}`,
                            transition: 'all 0.2s ease',
                            '&:hover': {
                                transform: 'scale(1.12)',
                                boxShadow: `0 4px 16px ${getColor(intensity)}`,
                                zIndex: 2,
                            },
                        }}>
                            <Typography
                                variant="h6"
                                fontWeight={800}
                                sx={{ color: intensity > 0.5 ? '#fff' : '#333', lineHeight: 1 }}
                            >
                                {num.toString().padStart(2, '0')}
                            </Typography>
                            <Typography
                                variant="caption"
                                sx={{
                                    fontSize: '0.6rem',
                                    color: intensity > 0.5 ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.5)',
                                    fontWeight: 600,
                                }}
                            >
                                {freq}×
                            </Typography>
                        </Box>
                    </MuiTooltip>
                ))}
            </Box>
        </Paper>
    );
}

export default HeatmapGrid;
