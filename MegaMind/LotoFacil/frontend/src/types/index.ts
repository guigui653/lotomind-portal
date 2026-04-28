/* ═══════════════════════════════════════════════════════════
   TypeScript interfaces for LotoMind Enterprise
   ═══════════════════════════════════════════════════════════ */

// ── Auth ─────────────────────────────────────────────────────
export interface LoginRequest {
    email: string;
    password: string;
}

export interface LoginResponse {
    token: string;
    email: string;
    fullName: string;
    role: string;
}

// ── Heatmap ──────────────────────────────────────────────────
export interface HeatmapResponse {
    numbers: number[];
    frequencies: number[];
    metadata: Record<string, unknown>;
}

// ── Odd/Even Analysis ────────────────────────────────────────
export interface OddEvenContest {
    concurso: number;
    data: string;
    odd_count: number;
    even_count: number;
    odd_numbers: number[];
    even_numbers: number[];
}

export interface OddEvenResponse {
    contests: OddEvenContest[];
    summary: {
        avg_odd: number;
        avg_even: number;
        most_common_pattern: string;
        pattern_distribution?: Record<string, number>;
        total_contests?: number;
    };
    odd_numbers_freq: Record<string, number>;
    even_numbers_freq: Record<string, number>;
}

// ── Smart Suggestion ─────────────────────────────────────────
export interface SmartSuggestionResponse {
    game: number[];
    filters_applied: string[];
    metrics: {
        odd_count: number;
        even_count: number;
        odd_numbers: number[];
        even_numbers: number[];
        sum: number;
        sum_ideal_range: number[];
        sum_mean: number;
        repetitions_from_last: number;
        last_contest: number;
        last_contest_numbers: number[];
        repeated_numbers: number[];
        heat_scores: Record<string, number>;
        combined_scores: Record<string, number>;
    };
    explanation: string;
    confidence: number;
}

// ── Bets ─────────────────────────────────────────────────────
export interface BetRequest {
    numbers: number[];
    contest?: number;
    strategy?: string;
}

export interface Bet {
    id: number;
    numbers: number[];
    contest?: number;
    strategy?: string;
    createdAt: string;
}

// ── Predictions ──────────────────────────────────────────────
export interface NumberTrend {
    number: number;
    trend: 'hot' | 'cold' | 'neutral';
    score: number;
    frequency: number;
}

export interface PredictionResponse {
    hotNumbers: NumberTrend[];
    coldNumbers: NumberTrend[];
    modelAccuracy: number;
    contestsAnalyzed: number;
}

// ── Consultant / Game Analysis ───────────────────────────────
export interface GameAnalysisRequest {
    numbers: number[];
}

export interface GameAnalysisChartItem {
    name: string;
    seu_calor?: number;
    media?: number;
    value?: number;
    score?: number;
    max?: number;
    freq?: number;
}

export interface GameAnalysisResponse {
    score: number;
    pontos_fortes: string[];
    pontos_fracos: string[];
    opiniao_do_parceiro: string;
    metricas: {
        numeros: number[];
        soma: number;
        soma_media: number;
        soma_faixa_ideal: number[];
        impares: number;
        pares: number;
        primos: number;
        repeticoes_ultimo: number;
        numeros_repetidos: number[];
        ultimo_concurso: number;
        heat_scores: Record<string, number>;
        calor_medio: number;
    };
    graficos: {
        heat_match: GameAnalysisChartItem[];
        composicao: GameAnalysisChartItem[];
        score_breakdown: GameAnalysisChartItem[];
    };
}
