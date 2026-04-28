import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/Layout/MainLayout';
import Dashboard from './pages/Dashboard';
import Analysis from './pages/Analysis';
import GameGenerator from './pages/GameGenerator';
import GameAnalyzer from './pages/GameAnalyzer';
import Login from './pages/Login';

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route element={<MainLayout />}>
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/analysis" element={<Analysis />} />
                    <Route path="/generator" element={<GameGenerator />} />
                    <Route path="/analyzer" element={<GameAnalyzer />} />
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Route>
            </Routes>
        </BrowserRouter>
    );
}

export default App;
