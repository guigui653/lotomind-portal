import api from './api';
import { apiPython } from './api';
import type { HeatmapResponse, PredictionResponse, OddEvenResponse, SmartSuggestionResponse, GameAnalysisResponse } from '../types';

export const analysisService = {
    async getHeatmap(lastContests: number = 15): Promise<HeatmapResponse> {
        const { data } = await api.get<HeatmapResponse>('/lottery/heatmap', {
            params: { lastContests },
        });
        return data;
    },

    async getHeatmapDirect(lastContests: number = 15): Promise<HeatmapResponse> {
        const { data } = await apiPython.get<HeatmapResponse>('/heatmap', {
            params: { lastContests },
        });
        return data;
    },

    async getOddEven(lastContests: number = 15): Promise<OddEvenResponse> {
        const { data } = await apiPython.get<OddEvenResponse>('/odd-even', {
            params: { lastContests },
        });
        return data;
    },

    async getSmartSuggestion(): Promise<SmartSuggestionResponse> {
        const { data } = await apiPython.get<SmartSuggestionResponse>('/smart-suggestion');
        return data;
    },

    async getPredictions(topN: number = 10): Promise<PredictionResponse> {
        const { data } = await api.get<PredictionResponse>('/lottery/predictions', {
            params: { topN },
        });
        return data;
    },

    async analyzeMyGame(numbers: number[]): Promise<GameAnalysisResponse> {
        const { data } = await apiPython.post<GameAnalysisResponse>('/analyze-my-game', { numbers });
        return data;
    },
};
