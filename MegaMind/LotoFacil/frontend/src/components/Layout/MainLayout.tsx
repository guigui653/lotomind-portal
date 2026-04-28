import { useEffect, useState, useCallback } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import {
    AppBar,
    Box,
    Chip,
    Drawer,
    List,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Toolbar,
    Tooltip,
    Typography,
} from '@mui/material';
import {
    Dashboard as DashboardIcon,
    Analytics as AnalyticsIcon,
    Psychology as PsychologyIcon,
    Logout as LogoutIcon,
    AutorenewRounded,
    SmartToy as SmartToyIcon,
} from '@mui/icons-material';
import { useAuthStore } from '../../store/useAuthStore';
import api from '../../services/api';

const DRAWER_WIDTH = 260;
const POLL_INTERVAL_MS = 60_000; // Poll every 60 seconds

function MainLayout() {
    const navigate = useNavigate();
    const clearUser = useAuthStore((s) => s.clearUser);
    const [lastUpdate, setLastUpdate] = useState<string | null>(null);
    const [updateType, setUpdateType] = useState<string>('');

    const fetchLastUpdate = useCallback(async () => {
        try {
            const { data } = await api.get('/last-update');
            if (data.last_update) {
                setLastUpdate(data.last_update);
                setUpdateType(data.type || 'unknown');
            }
        } catch {
            // Silently ignore — endpoint may not have data yet
        }
    }, []);

    // Poll for updates every 60 seconds
    useEffect(() => {
        fetchLastUpdate();
        const interval = setInterval(fetchLastUpdate, POLL_INTERVAL_MS);
        return () => clearInterval(interval);
    }, [fetchLastUpdate]);

    // Expose fetchLastUpdate globally so Dashboard can trigger it after manual sync
    useEffect(() => {
        (window as unknown as Record<string, unknown>).__refreshLastUpdate = fetchLastUpdate;
        return () => {
            delete (window as unknown as Record<string, unknown>).__refreshLastUpdate;
        };
    }, [fetchLastUpdate]);

    const formatDate = (iso: string) => {
        try {
            const d = new Date(iso);
            return d.toLocaleDateString('pt-BR', {
                day: '2-digit', month: '2-digit', year: 'numeric',
                hour: '2-digit', minute: '2-digit',
            });
        } catch {
            return iso;
        }
    };

    const menuItems = [
        { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
        { text: 'Análise', icon: <AnalyticsIcon />, path: '/analysis' },
        { text: 'Gerador', icon: <PsychologyIcon />, path: '/generator' },
        { text: 'Consultoria', icon: <SmartToyIcon />, path: '/analyzer' },
    ];

    const handleLogout = () => {
        clearUser();
        navigate('/login');
    };

    return (
        <Box sx={{ display: 'flex', minHeight: '100vh' }}>
            {/* ── Sidebar ───────────────────────────── */}
            <Drawer
                variant="permanent"
                sx={{
                    width: DRAWER_WIDTH,
                    '& .MuiDrawer-paper': {
                        width: DRAWER_WIDTH,
                        bgcolor: 'background.paper',
                        borderRight: '1px solid rgba(255,255,255,0.06)',
                    },
                }}
            >
                <Toolbar>
                    <Typography variant="h6" fontWeight={700} color="primary">
                        🧠 LotoMind
                    </Typography>
                </Toolbar>
                <List sx={{ flex: 1 }}>
                    {menuItems.map(({ text, icon, path }) => (
                        <ListItemButton key={path} onClick={() => navigate(path)}>
                            <ListItemIcon sx={{ color: 'primary.main' }}>{icon}</ListItemIcon>
                            <ListItemText primary={text} />
                        </ListItemButton>
                    ))}
                </List>
                <List>
                    <ListItemButton onClick={handleLogout}>
                        <ListItemIcon sx={{ color: 'error.main' }}>
                            <LogoutIcon />
                        </ListItemIcon>
                        <ListItemText primary="Sair" />
                    </ListItemButton>
                </List>
            </Drawer>

            {/* ── Main Content ──────────────────────── */}
            <Box component="main" sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                <AppBar position="static" elevation={0} sx={{ bgcolor: 'background.paper' }}>
                    <Toolbar sx={{ justifyContent: 'space-between' }}>
                        <Typography variant="h6" fontWeight={600}>
                            LotoMind Enterprise
                        </Typography>

                        {/* ── Auto-Update Badge ── */}
                        {lastUpdate && (
                            <Tooltip
                                title={`Tipo: ${updateType === 'automatic' ? 'Automático (Scheduler)' : 'Manual'}`}
                                arrow
                            >
                                <Chip
                                    icon={<AutorenewRounded sx={{ fontSize: 16 }} />}
                                    label={`Atualizado em: ${formatDate(lastUpdate)}`}
                                    size="small"
                                    variant="outlined"
                                    sx={{
                                        borderColor: updateType === 'automatic'
                                            ? 'rgba(0,217,166,0.5)'
                                            : 'rgba(108,99,255,0.5)',
                                        color: updateType === 'automatic' ? '#00D9A6' : '#6C63FF',
                                        fontWeight: 600,
                                        fontSize: '0.75rem',
                                        animation: 'none',
                                        '& .MuiChip-icon': {
                                            color: 'inherit',
                                        },
                                    }}
                                />
                            </Tooltip>
                        )}
                    </Toolbar>
                </AppBar>
                <Box sx={{ p: 3, flexGrow: 1 }}>
                    <Outlet />
                </Box>
            </Box>
        </Box>
    );
}

export default MainLayout;
