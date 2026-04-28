import { useMemo } from 'react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
    PieChart, Pie, Cell
} from 'recharts';
import { Paper, Typography, Box, Grid } from '@mui/material';
import type { OddEvenResponse } from '../../types';

interface OddEvenChartProps {
    data: OddEvenResponse;
}

const PIE_COLORS = ['#AB47BC', '#26A69A']; // Purple for Odd, Teal for Even

function OddEvenChart({ data }: OddEvenChartProps) {
    const barData = useMemo(() =>
        data.contests
            .slice()
            .reverse()
            .map((c) => ({
                name: `#${c.concurso}`,
                Ímpares: c.odd_count,
                Pares: c.even_count,
            })),
        [data.contests]
    );

    const pieData = useMemo(() => {
        if (!data.summary) return [];
        return [
            { name: 'Ímpares', value: data.summary.avg_odd },
            { name: 'Pares', value: data.summary.avg_even },
        ];
    }, [data.summary]);

    const patternData = useMemo(() => {
        if (!data.summary?.pattern_distribution) return [];
        return Object.entries(data.summary.pattern_distribution)
            .map(([pattern, count]) => ({ pattern, count: count as number }))
            .sort((a, b) => b.count - a.count);
    }, [data.summary]);

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* ── Stacked Bar Chart: Odd/Even per Contest ── */}
            <Paper sx={{ p: 3, borderRadius: 3 }}>
                <Typography variant="h6" fontWeight={700} gutterBottom>
                    📊 Distribuição Ímpar/Par por Concurso
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Últimos {data.summary.total_contests ?? data.contests.length} concursos •
                    Padrão mais comum: <strong>{data.summary.most_common_pattern}</strong>
                </Typography>

                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={barData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                        <XAxis
                            dataKey="name"
                            tick={{ fill: '#8888A0', fontSize: 10 }}
                            angle={-45}
                            textAnchor="end"
                            height={60}
                        />
                        <YAxis tick={{ fill: '#8888A0', fontSize: 12 }} domain={[0, 15]} />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1A1A2E',
                                border: '1px solid rgba(255,255,255,0.1)',
                                borderRadius: 8,
                            }}
                            labelStyle={{ color: '#E8E8F0' }}
                        />
                        <Legend />
                        <Bar dataKey="Ímpares" stackId="a" fill="#AB47BC" radius={[0, 0, 0, 0]} />
                        <Bar dataKey="Pares" stackId="a" fill="#26A69A" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </Paper>

            <Grid container spacing={3}>
                {/* ── Pie Chart: Average Odd/Even ── */}
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center' }}>
                        <Typography variant="h6" fontWeight={700} gutterBottom>
                            🥧 Proporção Média Ímpar vs Par
                        </Typography>

                        <ResponsiveContainer width="100%" height={250}>
                            <PieChart>
                                <Pie
                                    data={pieData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={100}
                                    dataKey="value"
                                    label={({ name, value }) => `${name}: ${value.toFixed(1)}`}
                                    labelLine={false}
                                >
                                    {pieData.map((_entry, index) => (
                                        <Cell key={index} fill={PIE_COLORS[index]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>

                        <Typography variant="body2" color="text.secondary">
                            Média: <strong style={{ color: '#AB47BC' }}>{data.summary.avg_odd} Ímpares</strong> /
                            <strong style={{ color: '#26A69A' }}> {data.summary.avg_even} Pares</strong>
                        </Typography>
                    </Paper>
                </Grid>

                {/* ── Pattern Distribution ── */}
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, borderRadius: 3 }}>
                        <Typography variant="h6" fontWeight={700} gutterBottom>
                            📈 Padrões de Distribuição
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            Frequência de cada combinação ímpar/par
                        </Typography>

                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                            {patternData.map(({ pattern, count }) => {
                                const maxCount = patternData[0]?.count || 1;
                                const pct = (count / maxCount) * 100;
                                return (
                                    <Box key={pattern}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                                            <Typography variant="body2" fontWeight={600}>
                                                {pattern}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                {count}× ({((count / (data.summary.total_contests ?? data.contests.length)) * 100).toFixed(0)}%)
                                            </Typography>
                                        </Box>
                                        <Box sx={{
                                            height: 8,
                                            borderRadius: 4,
                                            bgcolor: 'rgba(255,255,255,0.05)',
                                            overflow: 'hidden',
                                        }}>
                                            <Box sx={{
                                                height: '100%',
                                                width: `${pct}%`,
                                                borderRadius: 4,
                                                background: 'linear-gradient(90deg, #AB47BC, #26A69A)',
                                                transition: 'width 0.5s ease',
                                            }} />
                                        </Box>
                                    </Box>
                                );
                            })}
                        </Box>
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
}

export default OddEvenChart;
