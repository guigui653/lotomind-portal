/**
 * LotoMind Portal — JavaScript Utilities
 */

// Conferidor Mega-Sena
function conferirJogo() {
    const input = document.getElementById('inputConferir');
    const container = document.getElementById('resultadoConferir');
    const nums = input.value.trim().replace(/,/g, ' ').split(/\s+/).filter(n => n && !isNaN(n)).map(Number);

    if (nums.length < 6) {
        container.innerHTML = '<div class="alert alert-warning">⚠️ Digite pelo menos 6 números.</div>';
        return;
    }

    container.innerHTML = '<div class="text-center"><div class="spinner-border text-success"></div></div>';

    fetch('/megasena/conferir', {
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
        html += '<div class="dezenas-container mb-2">';
        data.sorteio.forEach(n => {
            const ac = data.acertos.includes(n);
            html += `<span class="dezena-ball small-ball ${ac ? 'dezena-acerto' : ''}">${n.toString().padStart(2, '0')}</span>`;
        });
        html += '</div>';
        html += `<div class="text-center mt-3">`;
        html += `<span class="badge ${data.qtd_acertos >= 4 ? 'bg-success' : 'bg-secondary'} fs-5 p-2">${data.qtd_acertos} acerto(s) — ${data.premio}</span>`;
        html += '</div></div>';
        container.innerHTML = html;
    })
    .catch(err => {
        container.innerHTML = `<div class="alert alert-danger">Erro: ${err.message}</div>`;
    });
}

// Validar jogo (estatísticas)
function validarJogo() {
    const input = document.getElementById('inputValidar');
    const container = document.getElementById('resultadoValidar');
    const nums = input.value.trim().replace(/,/g, ' ').split(/\s+/).filter(n => n && !isNaN(n)).map(Number);

    if (nums.length !== 6) {
        container.innerHTML = '<div class="alert alert-warning">⚠️ Digite exatamente 6 números.</div>';
        return;
    }

    container.innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div></div>';

    fetch('/megasena/validar', {
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
        // Display result
        let html = `<div class="jogo-resultado ${data.aprovado ? 'jogo-valido' : 'jogo-parcial'}">`;
        html += `<h6>${data.classificacao} — Score: ${data.score}/100</h6>`;
        html += '<div class="text-center mb-2">';
        data.jogo.forEach(n => {
            html += `<span class="dezena-ball small-ball dezena-acerto">${n.toString().padStart(2, '0')}</span>`;
        });
        html += '</div>';

        // Detalhes
        const d = data.detalhes;
        html += '<div class="row g-1 justify-content-center">';
        if (d.soma) html += `<div class="col-auto"><span class="badge bg-dark border">${d.soma.valido ? '✅' : '❌'} Soma: ${d.soma.valor} (${d.soma.pontos}pts)</span></div>`;
        if (d.desvio_padrao) html += `<div class="col-auto"><span class="badge bg-dark border">${d.desvio_padrao.valido ? '✅' : '❌'} σ: ${d.desvio_padrao.valor} (${d.desvio_padrao.pontos}pts)</span></div>`;
        if (d.paridade) html += `<div class="col-auto"><span class="badge bg-dark border">${d.paridade.valido ? '✅' : '❌'} ${d.paridade.formato} (${d.paridade.pontos}pts)</span></div>`;
        if (d.primos) html += `<div class="col-auto"><span class="badge bg-dark border">${d.primos.valido ? '✅' : '❌'} Primos: ${d.primos.quantidade} (${d.primos.pontos}pts)</span></div>`;
        html += '</div></div>';
        container.innerHTML = html;
    })
    .catch(err => {
        container.innerHTML = `<div class="alert alert-danger">Erro: ${err.message}</div>`;
    });
}
