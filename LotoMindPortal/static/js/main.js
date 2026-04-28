/**
 * LotoMind Portal — Visual Engine v3.0
 * Partículas flutuantes · Tilt 3D · Glow sweep · Micro-interações
 */

// ── 1. CANVAS DE PARTÍCULAS (fundo animado global) ─────────────

(function () {
  'use strict';

  const canvas = document.createElement('canvas');
  canvas.id = 'lm-canvas';
  document.body.insertBefore(canvas, document.body.firstChild);

  const ctx = canvas.getContext('2d');
  let mouse = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
  let particles = [];
  let spheres = [];
  let raf;

  // Paleta neon
  const COLORS = [
    'rgba(0, 212, 255,',
    'rgba(240, 180, 41,',
    'rgba(0, 208, 132,',
    'rgba(155, 89, 182,',
  ];

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  // ── Partículas flutuantes ────────────────────────────────────
  function createParticle() {
    const color = COLORS[Math.floor(Math.random() * COLORS.length)];
    return {
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 1.5 + 0.3,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      alpha: Math.random() * 0.5 + 0.1,
      color,
    };
  }

  // ── Esferas flutuantes grandes ───────────────────────────────
  function createSphere() {
    const color = COLORS[Math.floor(Math.random() * COLORS.length)];
    const r = Math.random() * 80 + 30;
    return {
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r,
      vx: (Math.random() - 0.5) * 0.15,
      vy: (Math.random() - 0.5) * 0.15,
      alpha: 0.04 + Math.random() * 0.04,
      color,
      phase: Math.random() * Math.PI * 2,
    };
  }

  function initParticles() {
    const count = Math.min(Math.floor((canvas.width * canvas.height) / 14000), 90);
    particles = Array.from({ length: count }, createParticle);
    spheres = Array.from({ length: 6 }, createSphere);
  }

  function drawParticle(p) {
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = p.color + p.alpha + ')';
    ctx.fill();
  }

  function drawSphere(s, t) {
    const pulse = Math.sin(t * 0.0008 + s.phase) * 0.015;
    const alpha = s.alpha + pulse;
    const grd = ctx.createRadialGradient(
      s.x - s.r * 0.3, s.y - s.r * 0.3, s.r * 0.1,
      s.x, s.y, s.r
    );
    grd.addColorStop(0, s.color + (alpha * 2.5) + ')');
    grd.addColorStop(0.5, s.color + alpha + ')');
    grd.addColorStop(1,   s.color + '0)');
    ctx.beginPath();
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
    ctx.fillStyle = grd;
    ctx.fill();
  }

  function drawConnections() {
    const threshold = 140;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < threshold) {
          const opacity = (1 - dist / threshold) * 0.07;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(0, 212, 255, ${opacity})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  }

  function update(p, isParticle) {
    if (isParticle) {
      // leve atração pelo mouse
      const dx = mouse.x - p.x;
      const dy = mouse.y - p.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 200) {
        p.vx += dx / dist * 0.005;
        p.vy += dy / dist * 0.005;
      }
      // amortecimento
      p.vx *= 0.995;
      p.vy *= 0.995;
    }
    p.x += p.vx;
    p.y += p.vy;

    // wrap
    if (p.x < -p.r) p.x = canvas.width  + p.r;
    if (p.x > canvas.width  + p.r) p.x = -p.r;
    if (p.y < -p.r) p.y = canvas.height + p.r;
    if (p.y > canvas.height + p.r) p.y = -p.r;
  }

  let lastTime = 0;
  function loop(time) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    spheres.forEach(s => { update(s, false); drawSphere(s, time); });
    drawConnections();
    particles.forEach(p => { update(p, true); drawParticle(p); });

    raf = requestAnimationFrame(loop);
  }

  // Init
  resize();
  initParticles();
  requestAnimationFrame(loop);

  window.addEventListener('resize', () => { resize(); initParticles(); });
  window.addEventListener('mousemove', e => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });
}());

// ── 2. TILT 3D (cards interativos) ────────────────────────────

(function () {
  'use strict';

  const INTENSITY    = 8;     // graus máx
  const GLOW_OPACITY = 0.15;

  function applyTilt(card) {
    card.style.transition = 'transform 0.1s ease, box-shadow 0.1s ease';

    card.addEventListener('mousemove', e => {
      const rect = card.getBoundingClientRect();
      const cx = rect.left + rect.width  / 2;
      const cy = rect.top  + rect.height / 2;
      const dx = (e.clientX - cx) / (rect.width  / 2);
      const dy = (e.clientY - cy) / (rect.height / 2);
      const rx = -dy * INTENSITY;
      const ry =  dx * INTENSITY;

      card.style.transform = `
        perspective(900px)
        rotateX(${rx}deg)
        rotateY(${ry}deg)
        translateZ(6px)
      `;

      // Reflexo de luz seguindo o mouse
      const gx = (dx + 1) / 2 * 100;
      const gy = (dy + 1) / 2 * 100;
      card.style.background = `
        radial-gradient(
          circle at ${gx}% ${gy}%,
          rgba(255,255,255,${GLOW_OPACITY}) 0%,
          transparent 60%
        ),
        rgba(13, 22, 41, 0.82)
      `;
    });

    card.addEventListener('mouseleave', () => {
      card.style.transition = 'transform 0.4s ease, box-shadow 0.4s ease, background 0.4s ease';
      card.style.transform  = 'perspective(900px) rotateX(0) rotateY(0) translateZ(0)';
      card.style.background = '';
    });
  }

  function initTilt() {
    document.querySelectorAll('.glass-card, .jogo-card, .metric-card, .stat-card, .module-card')
      .forEach(applyTilt);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTilt);
  } else {
    initTilt();
  }

  // Re-aplicar para cards gerados dinamicamente
  window.lmApplyTilt = () => {
    document.querySelectorAll('.glass-card:not([data-tilt]), .jogo-card:not([data-tilt])')
      .forEach(c => { applyTilt(c); c.dataset.tilt = '1'; });
  };
}());

// ── 3. GRADIENT BORDER nos cards ao hover ─────────────────────

(function () {
  'use strict';

  // Já tratado via CSS :before mask. Nada extra necessário.
  // Este bloco reservado para extensões futuras.
}());

// ── 4. GLOW SWEEP nos botões CTA ──────────────────────────────

(function () {
  'use strict';

  function addSweep(btn) {
    if (btn.dataset.sweep) return;
    btn.dataset.sweep = '1';
    const shine = document.createElement('span');
    shine.style.cssText = `
      position:absolute; top:0; left:-100%;
      width:60%; height:100%; pointer-events:none;
      background:linear-gradient(90deg,transparent,rgba(255,255,255,0.22),transparent);
      transition:left 0.55s ease; border-radius:inherit;
    `;
    if (getComputedStyle(btn).position === 'static') btn.style.position = 'relative';
    btn.style.overflow = 'hidden';
    btn.appendChild(shine);

    btn.addEventListener('mouseenter', () => { shine.style.left = '150%'; });
    btn.addEventListener('mouseleave', () => {
      shine.style.transition = 'none';
      shine.style.left = '-100%';
      requestAnimationFrame(() => { shine.style.transition = 'left 0.55s ease'; });
    });
  }

  function initSweep() {
    document.querySelectorAll(
      '.btn-success, .btn-warning, .btn-primary, .btn-lotomind, .btn-execute, .btn-login'
    ).forEach(addSweep);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSweep);
  } else {
    initSweep();
  }

  window.lmInitSweep = initSweep;
}());

// ── 5. COUNTERS (animação de entrada dos números KPI) ─────────

(function () {
  'use strict';

  function animateCounter(el) {
    const target = parseFloat(el.dataset.count || el.textContent.replace(/[^\d.]/g, ''));
    if (isNaN(target)) return;

    const duration = 800;
    const start = performance.now();
    const isFloat = el.textContent.includes('.');

    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = target * eased;
      el.textContent = isFloat ? value.toFixed(1) : Math.round(value).toLocaleString('pt-BR');
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  function initCounters() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.2 });

    document.querySelectorAll('.metric-value, .stat-value, .quadrant-count')
      .forEach(el => observer.observe(el));
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCounters);
  } else {
    initCounters();
  }
}());

// ── 6. CONFERIDOR MEGA-SENA (mantido do main.js anterior) ────

function conferirJogo() {
  const input = document.getElementById('inputConferir');
  const container = document.getElementById('resultadoConferir');
  const nums = input.value.trim().replace(/,/g, ' ')
    .split(/\s+/).filter(n => n && !isNaN(n)).map(Number);

  if (nums.length < 6) {
    container.innerHTML = '<div class="alert alert-warning">⚠️ Digite pelo menos 6 números.</div>';
    return;
  }
  container.innerHTML = '<div class="text-center"><div class="spinner-border"></div></div>';

  fetch('/megasena/conferir', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ numeros: nums }),
  })
  .then(r => r.json())
  .then(data => {
    if (data.erro) { container.innerHTML = `<div class="alert alert-danger">${data.erro}</div>`; return; }
    let html = '<div class="jogo-resultado">';
    html += `<h6>Concurso #${data.concurso} — ${data.data}</h6>`;
    html += '<div class="dezenas-container mb-2">';
    data.sorteio.forEach(n => {
      const ac = data.acertos.includes(n);
      html += `<span class="dezena-ball small-ball ${ac ? 'dezena-acerto' : ''}">${n.toString().padStart(2,'0')}</span>`;
    });
    html += '</div>';
    html += `<div class="text-center mt-3">`;
    html += `<span class="badge ${data.qtd_acertos >= 4 ? 'bg-success' : 'bg-secondary'} fs-5 p-2">${data.qtd_acertos} acerto(s) — ${data.premio}</span>`;
    html += '</div></div>';
    container.innerHTML = html;
  })
  .catch(err => { container.innerHTML = `<div class="alert alert-danger">Erro: ${err.message}</div>`; });
}

// ── 7. VALIDAR JOGO (mantido) ─────────────────────────────────

function validarJogo() {
  const input = document.getElementById('inputValidar');
  const container = document.getElementById('resultadoValidar');
  const nums = input.value.trim().replace(/,/g, ' ')
    .split(/\s+/).filter(n => n && !isNaN(n)).map(Number);

  if (nums.length !== 6) {
    container.innerHTML = '<div class="alert alert-warning">⚠️ Digite exatamente 6 números.</div>';
    return;
  }
  container.innerHTML = '<div class="text-center"><div class="spinner-border"></div></div>';

  fetch('/megasena/validar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ numeros: nums }),
  })
  .then(r => r.json())
  .then(data => {
    if (data.erro) { container.innerHTML = `<div class="alert alert-danger">${data.erro}</div>`; return; }
    let html = `<div class="jogo-resultado ${data.aprovado ? 'jogo-valido' : 'jogo-parcial'}">`;
    html += `<h6>${data.classificacao} — Score: ${data.score}/100</h6>`;
    html += '<div class="text-center mb-2">';
    data.jogo.forEach(n => {
      html += `<span class="dezena-ball small-ball dezena-acerto">${n.toString().padStart(2,'0')}</span>`;
    });
    html += '</div>';
    const d = data.detalhes;
    html += '<div class="row g-1 justify-content-center">';
    if (d.soma)          html += `<div class="col-auto"><span class="badge bg-dark border">${d.soma.valido          ? '✅' : '❌'} Soma: ${d.soma.valor} (${d.soma.pontos}pts)</span></div>`;
    if (d.desvio_padrao) html += `<div class="col-auto"><span class="badge bg-dark border">${d.desvio_padrao.valido ? '✅' : '❌'} s: ${d.desvio_padrao.valor} (${d.desvio_padrao.pontos}pts)</span></div>`;
    if (d.paridade)      html += `<div class="col-auto"><span class="badge bg-dark border">${d.paridade.valido      ? '✅' : '❌'} ${d.paridade.formato} (${d.paridade.pontos}pts)</span></div>`;
    if (d.primos)        html += `<div class="col-auto"><span class="badge bg-dark border">${d.primos.valido        ? '✅' : '❌'} Primos: ${d.primos.quantidade} (${d.primos.pontos}pts)</span></div>`;
    html += '</div></div>';
    container.innerHTML = html;
  })
  .catch(err => { container.innerHTML = `<div class="alert alert-danger">Erro: ${err.message}</div>`; });
}
