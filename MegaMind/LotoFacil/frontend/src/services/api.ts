/**
 * Axios instances for LotoMind Enterprise.
 *
 * - apiJava: connects to Spring Boot (auth, lottery, bets)
 * - apiPython: connects to FastAPI (analysis, heatmap)
 * - Both use JWT interceptors and timeout handling
 */
import axios from 'axios';

// ── Base URLs (proxied through Nginx — no CORS) ─────
const JAVA_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const PYTHON_BASE_URL = import.meta.env.VITE_API_PYTHON_URL || '/api/v1/analysis';

// ── Factory: create an axios instance with interceptors ──
function createApiInstance(baseURL: string) {
    const instance = axios.create({
        baseURL,
        timeout: 15_000,
        headers: {
            'Content-Type': 'application/json',
        },
    });

    // Request: attach JWT token
    instance.interceptors.request.use(
        (config) => {
            const token = localStorage.getItem('lotomind_token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        },
        (error) => Promise.reject(error),
    );

    // Response: handle 401 and timeout errors
    instance.interceptors.response.use(
        (response) => response,
        (error) => {
            if (error.response?.status === 401) {
                localStorage.removeItem('lotomind_token');
                window.location.href = '/login';
            }
            if (error.code === 'ECONNABORTED') {
                console.error('[API] Request timeout:', error.config?.url);
            }
            return Promise.reject(error);
        },
    );

    return instance;
}

// ── Instances ────────────────────────────────────────
export const apiJava = createApiInstance(JAVA_BASE_URL);
export const apiPython = createApiInstance(PYTHON_BASE_URL);

// Default export for backward compatibility (points to Java)
const api = apiJava;
export default api;
