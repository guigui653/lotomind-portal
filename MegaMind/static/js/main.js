/**
 * MegaMind — JavaScript principal
 * Funções utilitárias, conferidor e validação de jogos
 */

// ── Atualizar Dados ──────────────────────────

function atualizarDados() {
    fetch('/atualizar')
        .then(r => r.json())
        .then(data => {
            if (data.status === 'ok') {
                showToast('✅ Dados atualizados! Recarregando...', 'success');
                setTimeout(() => location.reload(), 1000);
            }
        })
        .catch(err => showToast('❌ Erro ao atualizar: ' + err.message, 'danger'));
}

// ── Conferir Jogo (Dashboard) ────────────────

function conferirJogo() {
    const input = document.getElementById('inputConferir');
    const container = document.getElementById('resultadoConferir');

    if (!input || !container) return;

    const nums = input.value.trim().replace(/,/g, ' ').split(/\s+/)
        .filter(n => n && !isNaN(n))
        .map(Number);

    if (nums.length < 6) {
        container.innerHTML = '<div class="alert alert-warning">⚠️ Digite pelo menos 6 números.</div>';
        return;
    }

    container.innerHTML = '<div class="text-center"><div class="spinner-border text-success"></div></div>';

    fetch('/conferir', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ numeros: nums })
    })
    .then(r => r.json())
    .then(data => {
        if (data.erro) {
            container.innerHTML = `<div class="alert alert-danger">${data.erro}</div>`;
            return;
        }

        let html = '<div class="jogo-resultado">';
        html += `<h6>Concurso #${data.concurso} — ${data.data}</h6>`;

        // Sorteio oficial
        html += '<p class="mb-1 small text-muted">Sorteio Oficial:</p>';
        html += '<div class="dezenas-container mb-2">';
        data.sorteio.forEach(n => {
            const acertou = data.acertos.includes(n);
            html += `<span class="dezena-ball small-ball ${acertou ? 'dezena-acerto' : ''}">${n.toString().padStart(2, '0')}</span>`;
        });
        html += '</div>';

        // Resultado
        const premio = data.premio;
        const cor = data.qtd_acertos >= 4 ? 'success' : 'secondary';
        html += `<div class="text-center mt-3">`;
        html += `<span class="badge bg-${cor} fs-5 p-2">${data.qtd_acertos} acerto(s) — ${premio}</span>`;
        html += `</div>`;

        if (data.acertos.length > 0) {
            html += '<p class="mt-2 mb-1 small text-muted">Números acertados:</p>';
            html += '<div class="dezenas-container">';
            data.acertos.forEach(n => {
                html += `<span class="dezena-ball small-ball dezena-acerto">${n.toString().padStart(2, '0')}</span>`;
            });
            html += '</div>';
        }

        html += '</div>';
        container.innerHTML = html;
    })
    .catch(err => {
        container.innerHTML = `<div class="alert alert-danger">Erro: ${err.message}</div>`;
    });
}

// ── Validar Jogo (Estatísticas) ──────────────

function validarJogo() {
    const input = document.getElementById('inputValidar');
    const container = document.getElementById('resultadoValidar');

    if (!input || !container) return;

    const nums = input.value.trim().replace(/,/g, ' ').split(/\s+/)
        .filter(n => n && !isNaN(n))
        .map(Number);

    if (nums.length !== 6) {
        container.innerHTML = '<div class="alert alert-warning">⚠️ Digite exatamente 6 números entre 1 e 60.</div>';
        return;
    }

    container.innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div></div>';

    fetch('/validar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ numeros: nums })
    })
    .then(r => r.json())
    .then(data => {
        if (data.erro) {
            container.innerHTML = `<div class="alert alert-danger">${data.erro}</div>`;
            return;
        }

        const scoreColor = data.score >= 70 ? '#00b894' : (data.score >= 50 ? '#fdcb6e' : '#e17055');

        let html = '<div class="jogo-resultado">';

        // Dezenas
        html += '<div class="text-center mb-3">';
        data.jogo.forEach(n => {
            html += `<span class="dezena-ball ${data.aprovado ? 'dezena-acerto' : ''}">${n.toString().padStart(2, '0')}</span>`;
        });
        html += '</div>';

        // Score
        html += `<div class="text-center mb-3">`;
        html += `<span style="font-size: 2.5rem; font-weight: 900; color: ${scoreColor}">${data.score}</span>`;
        html += `<span style="color: rgba(255,255,255,0.4)" class="ms-1">/100</span>`;
        html += `<div style="color: rgba(255,255,255,0.6)">${data.classificacao}</div>`;
        html += `</div>`;

        // Detalhes
        const d = data.detalhes;
        html += '<div class="row g-2 justify-content-center">';
        html += makeDetailBadge('Soma', d.soma);
        html += makeDetailBadge('σ Desvio', d.desvio_padrao);
        html += makeDetailBadge('Paridade', d.paridade, d.paridade.formato);
        html += makeDetailBadge('Primos', d.primos, d.primos.quantidade);
        if (d.calor) html += `<div class="col-auto"><span class="badge bg-dark border">🌡️ Calor: ${d.calor.media} (${d.calor.pontos}pts)</span></div>`;
        if (d.quadrantes) html += `<div class="col-auto"><span class="badge bg-dark border">📊 ${d.quadrantes.presentes} quadrantes (${d.quadrantes.pontos}pts)</span></div>`;
        html += '</div>';

        // Status
        html += `<div class="text-center mt-3">`;
        if (data.aprovado) {
            html += '<span class="badge bg-success fs-6 p-2">✅ JOGO APROVADO — Dentro da normalidade</span>';
        } else {
            html += '<span class="badge bg-warning text-dark fs-6 p-2">⚠️ ABAIXO DO PADRÃO</span>';
        }
        html += '</div>';

        html += '</div>';
        container.innerHTML = html;
    })
    .catch(err => {
        container.innerHTML = `<div class="alert alert-danger">Erro: ${err.message}</div>`;
    });
}

function makeDetailBadge(label, detail, displayVal) {
    const icon = detail.valido ? '✅' : '❌';
    const val = displayVal !== undefined ? displayVal : (typeof detail.valor === 'number' ? detail.valor.toFixed ? detail.valor : detail.valor : detail.valor);
    return `<div class="col-auto"><span class="badge bg-dark border">${icon} ${label}: ${val} (${detail.pontos}pts)</span></div>`;
}

// ── Toast ────────────────────────────────────

function showToast(msg, type) {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
    toast.style.zIndex = 9999;
    toast.style.minWidth = '300px';
    toast.style.animation = 'fadeIn 0.3s ease-out';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ── Enter Key Support ────────────────────────

document.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        if (document.activeElement.id === 'inputConferir') conferirJogo();
        if (document.activeElement.id === 'inputValidar') validarJogo();
    }
});
