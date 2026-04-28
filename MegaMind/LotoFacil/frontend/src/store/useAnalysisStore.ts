import { create } from 'zustand';
import type { HeatmapResponse, PredictionResponse, OddEvenResponse } from '../types';

interface AnalysisState {
    heatmap: HeatmapResponse | null;
    oddEven: OddEvenResponse | null;
    predictions: PredictionResponse | null;
    isLoading: boolean;
    error: string | null;
    setHeatmap: (data: HeatmapResponse) => void;
    setOddEven: (data: OddEvenResponse) => void;
    setPredictions: (data: PredictionResponse) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
    heatmap: null,
    oddEven: null,
    predictions: null,
    isLoading: false,
    error: null,

    setHeatmap: (data) => set({ heatmap: data, error: null }),
    setOddEven: (data) => set({ oddEven: data, error: null }),
    setPredictions: (data) => set({ predictions: data, error: null }),
    setLoading: (loading) => set({ isLoading: loading }),
    setError: (error) => set({ error, isLoading: false }),
}));
