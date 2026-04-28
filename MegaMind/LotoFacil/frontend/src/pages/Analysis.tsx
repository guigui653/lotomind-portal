import { useEffect, useState } from 'react';
import { Box, Button, Typography, ToggleButtonGroup, ToggleButton, Alert } from '@mui/material';
import HeatmapChart from '../components/Charts/HeatmapChart';
import HeatmapGrid from '../components/Charts/HeatmapGrid';
import OddEvenChart from '../components/Charts/OddEvenChart';
import SmartSuggestion from '../components/Charts/SmartSuggestion';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { analysisService } from '../services/analysisService';
import { useAnalysisStore } from '../store/useAnalysisStore';

function Analysis() {
    const { heatmap, oddEven, isLoading, error, setHeatmap, setOddEven, setLoading, setError } = useAnalysisStore();
    const [lastContests, setLastContests] = useState(15);
    const [viewMode, setViewMode] = useState<'grid' | 'bar'>('grid');

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [heatmapData, oddEvenData] = await Promise.all([
                analysisService.getHeatmapDirect(lastContests),
                analysisService.getOddEven(lastContests),
            ]);
            setHeatmap(heatmapData);
            setOddEven(oddEvenData);
        } catch {
            setError('Falha ao carregar análises. Verifique se os dados estão sincronizados.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [lastContests]);

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Header */}
            <Box>
                <Typography variant="h5" fontWeight={700} gutterBottom>
                    📊 Análise Estatística Avançada
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Mapa de calor, distribuição ímpar/par e sugestões baseadas em probabilidade
                </Typography>
            </Box>

            {/* Controls Row */}
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
                <Typography variant="body2" fontWeight={600} color="text.secondary">
                    Período:
                </Typography>
                {[10, 15, 20, 50, 100].map((n) => (
                    <Button
                        key={n}
                        variant={lastContests === n ? 'contained' : 'outlined'}
                        size="small"
                        onClick={() => setLastContests(n)}
                        sx={{
                            fontWeight: lastContests === n ? 800 : 400,
                            ...(n <= 15 && lastContests !== n ? {
                                borderColor: '#6C63FF',
                                color: '#6C63FF',
                            } : {}),
                        }}
                    >
                        {n} jogos
                    </Button>
                ))}

                <Box sx={{ flexGrow: 1 }} />

                <ToggleButtonGroup
                    value={viewMode}
                    exclusive
                    onChange={(_e, v) => v && setViewMode(v)}
                    size="small"
                >
                    <ToggleButton value="grid">Grade 5×5</ToggleButton>
                    <ToggleButton value="bar">Barras</ToggleButton>
                </ToggleButtonGroup>
            </Box>

            {/* Loading & Error */}
            {isLoading && <LoadingSpinner message="Calculando estatísticas com dados reais..." />}
            {error && <Alert severity="error">{error}</Alert>}

            {/* ══ Section 1: Heatmap ══════════════════════════════ */}
            {heatmap && !isLoading && (
                viewMode === 'grid'
                    ? <HeatmapGrid data={heatmap} />
                    : <HeatmapChart data={heatmap} />
            )}

            {/* ══ Section 2: Odd/Even Analysis ════════════════════ */}
            {oddEven && !isLoading && (
                <OddEvenChart data={oddEven} />
            )}

            {/* ══ Section 3: Smart Suggestion ═════════════════════ */}
            {!isLoading && (
                <SmartSuggestion />
            )}
        </Box>
    );
}

export default Analysis;
