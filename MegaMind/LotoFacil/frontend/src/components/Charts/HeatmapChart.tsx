import { useEffect, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Paper, Typography } from '@mui/material';
import type { HeatmapResponse } from '../../types';

interface HeatmapChartProps {
    data: HeatmapResponse;
}

function HeatmapChart({ data }: HeatmapChartProps) {
    const chartData = useMemo(() => {
        const maxFreq = Math.max(...data.frequencies);
        const minFreq = Math.min(...data.frequencies);
        const range = maxFreq - minFreq || 1;

        return data.numbers.map((num, idx) => ({
            number: `${num}`,
            frequency: data.frequencies[idx],
            intensity: (data.frequencies[idx] - minFreq) / range,
        }));
    }, [data]);

    const getBarColor = (intensity: number): string => {
        if (intensity > 0.7) return '#FF6B6B';       // Hot — red
        if (intensity > 0.4) return '#FFD93D';       // Warm — yellow
        return '#6BCB77';                             // Cold — green
    };

    return (
        <Paper sx={{ p: 3, bgcolor: 'background.paper', borderRadius: 3 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
                🔥 Mapa de Calor — Frequência dos Números
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
                Últimos {data.metadata.contests_analyzed as number ?? '?'} concursos analisados
            </Typography>

            <ResponsiveContainer width="100%" height={350}>
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="number" tick={{ fill: '#8888A0', fontSize: 12 }} />
                    <YAxis tick={{ fill: '#8888A0', fontSize: 12 }} />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#1A1A2E', border: '1px solid rgba(255,255,255,0.1)' }}
                        labelStyle={{ color: '#E8E8F0' }}
                    />
                    <Bar dataKey="frequency" radius={[4, 4, 0, 0]}>
                        {chartData.map((entry, index) => (
                            <Cell key={index} fill={getBarColor(entry.intensity)} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </Paper>
    );
}

export default HeatmapChart;
