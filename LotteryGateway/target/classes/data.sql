-- ═══════════════════════════════════════════════════════
--  LotteryGateway — Seed Data
-- ═══════════════════════════════════════════════════════

-- Usuário admin padrão (senha: admin123)
-- BCrypt hash de "admin123"
INSERT INTO usuarios (email, password_hash, full_name, role, active, created_at, updated_at)
SELECT 'admin@lottery.com',
       '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy',
       'Administrador',
       'ADMIN',
       true,
       CURRENT_TIMESTAMP,
       CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'admin@lottery.com');

-- Alguns concursos de exemplo da Mega-Sena
INSERT INTO concursos (numero, data_sorteio, dezenas, tipo_loteria, soma, pares, impares)
SELECT 2984, '2025-03-15', '06,11,15,28,42,60', 'MEGA_SENA', 162, 4, 2
WHERE NOT EXISTS (SELECT 1 FROM concursos WHERE numero = 2984 AND tipo_loteria = 'MEGA_SENA');

INSERT INTO concursos (numero, data_sorteio, dezenas, tipo_loteria, soma, pares, impares)
SELECT 2983, '2025-03-12', '03,17,24,35,41,58', 'MEGA_SENA', 178, 2, 4
WHERE NOT EXISTS (SELECT 1 FROM concursos WHERE numero = 2983 AND tipo_loteria = 'MEGA_SENA');
