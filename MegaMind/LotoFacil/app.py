import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import urllib3
import random
import urllib.parse

# Importa os módulos do sistema
from engine import LotofacilEngine
from generator import GeradorJogos
from statistical_filter import FiltroEstatistico

# --- 1. CONFIGURAÇÃO E CSS ---
st.set_page_config(
    page_title="Lotofácil Pro 2.0 - Elite Edition",
    page_icon="🍀",
    layout="wide",
    initial_sidebar_state="expanded"
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Inicializa Engine e Gerador
@st.cache_resource
def inicializar_sistema():
    """Inicializa o motor e o gerador (executado uma vez)"""
    engine = LotofacilEngine()
    gerador = GeradorJogos(engine)
    return engine, gerador


try:
    engine, gerador = inicializar_sistema()
except Exception as e:
    st.error(f"❌ Erro ao inicializar sistema: {e}")
    st.info("💡 Verifique se os arquivos engine.py e generator.py estão na mesma pasta")
    st.stop()

# ═══════════════════════════════════════════════════════════════════
# DESIGN SYSTEM — Power BI Dark-Mode Premium
# Paleta: Verde #00d084 | Laranja #ff6b35 | Azul #4ecdc4 | Branco #f0f0f0
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── Reset & Base ─────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    .stApp {
        background: linear-gradient(180deg, #0e1117 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* ── Sidebar ──────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    /* ── KPI Metric Cards — Glassmorphism ─────────────── */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px 18px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 208, 132, 0.15);
    }

    div[data-testid="stMetric"] label {
        color: rgba(240, 240, 240, 0.6) !important;
        font-weight: 500 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #f0f0f0 !important;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }

    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #00d084 !important;
        font-weight: 600 !important;
    }

    /* ── Títulos ──────────────────────────────────────── */
    h1 {
        background: linear-gradient(135deg, #00d084 0%, #4ecdc4 50%, #00d084 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 900 !important;
        letter-spacing: -0.5px;
    }

    h2, h3 {
        color: #e8e8e8 !important;
        font-weight: 700 !important;
    }

    /* ── Tabs ─────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        color: rgba(240, 240, 240, 0.5) !important;
        font-weight: 600;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0, 208, 132, 0.15), rgba(78, 205, 196, 0.1)) !important;
        color: #00d084 !important;
        border-bottom: 2px solid #00d084 !important;
    }

    /* ── Containers & Expanders ────────────────────────── */
    .stExpander {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
    }

    .stDataFrame {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }

    /* ── Dezena Circles ───────────────────────────────── */
    .dezena-circle {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: linear-gradient(135deg, #2d2d44 0%, #3d3d5c 100%);
        color: #f0f0f0;
        font-weight: 700;
        font-size: 15px;
        margin: 5px;
        border: 2px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        font-family: 'Inter', sans-serif;
    }

    .dezena-circle:hover {
        transform: scale(1.2) translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 208, 132, 0.4);
        border-color: #00d084;
    }

    .dezena-acerto {
        background: linear-gradient(135deg, #00d084 0%, #00b371 100%);
        color: #0e1117;
        border-color: rgba(0, 208, 132, 0.4);
        box-shadow: 0 4px 15px rgba(0, 208, 132, 0.4);
        font-weight: 800;
    }

    .dezena-fria {
        background: linear-gradient(135deg, #4ecdc4 0%, #44a8a0 100%);
        color: #0e1117;
        border-color: rgba(78, 205, 196, 0.4);
        box-shadow: 0 4px 15px rgba(78, 205, 196, 0.3);
    }

    /* ── Botões Premium ───────────────────────────────── */
    .stButton>button {
        border-radius: 12px;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        letter-spacing: 0.3px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 208, 132, 0.3);
    }

    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #00d084 0%, #00b371 100%) !important;
        color: #0e1117 !important;
        border: none;
        font-weight: 800;
    }

    .stButton>button[kind="primary"]:hover {
        box-shadow: 0 8px 30px rgba(0, 208, 132, 0.5);
    }

    /* ── Badges ────────────────────────────────────────── */
    .badge-valido {
        background: linear-gradient(135deg, #00d084, #00b371);
        color: #0e1117;
        padding: 6px 18px;
        border-radius: 24px;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 15px rgba(0, 208, 132, 0.4);
        font-family: 'Inter', sans-serif;
    }

    .badge-invalido {
        background: linear-gradient(135deg, #ff6b35, #e55a2b);
        color: #fff;
        padding: 6px 18px;
        border-radius: 24px;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 15px rgba(255, 107, 53, 0.4);
        font-family: 'Inter', sans-serif;
    }

    /* ── Header Custom ────────────────────────────────── */
    .dashboard-header {
        text-align: center;
        padding: 30px 0 20px 0;
    }

    .dashboard-header h1 {
        font-size: 2.8rem !important;
        margin: 0;
        background: linear-gradient(135deg, #00d084, #4ecdc4, #00d084);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .dashboard-header .subtitle {
        color: rgba(240, 240, 240, 0.45);
        font-size: 0.95rem;
        font-weight: 400;
        margin-top: 6px;
        letter-spacing: 0.3px;
    }

    /* ── KPI Card Custom ──────────────────────────────── */
    .kpi-card {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 24px;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: 18px 18px 0 0;
    }

    .kpi-card.green::before { background: linear-gradient(90deg, #00d084, #4ecdc4); }
    .kpi-card.orange::before { background: linear-gradient(90deg, #ff6b35, #ffa726); }
    .kpi-card.blue::before { background: linear-gradient(90deg, #4ecdc4, #26c6da); }
    .kpi-card.purple::before { background: linear-gradient(90deg, #7c4dff, #b388ff); }

    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
    }

    .kpi-card .kpi-icon { font-size: 28px; margin-bottom: 8px; }
    .kpi-card .kpi-value {
        font-size: 2rem;
        font-weight: 800;
        color: #f0f0f0;
        line-height: 1.2;
    }
    .kpi-card .kpi-label {
        font-size: 0.78rem;
        color: rgba(240, 240, 240, 0.5);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-top: 4px;
    }
    .kpi-card .kpi-delta {
        font-size: 0.82rem;
        color: #00d084;
        font-weight: 600;
        margin-top: 6px;
    }

    /* ── Divider ───────────────────────────────────────── */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
        margin: 24px 0;
    }

    /* ── Scrollbar ─────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0e1117; }
    ::-webkit-scrollbar-thumb { background: #2d2d44; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #3d3d5c; }

    </style>
""", unsafe_allow_html=True)


# --- 2. FUNÇÕES AUXILIARES ---

def renderizar_dezenas_circulares(jogo, tipo='normal'):
    """
    Renderiza as 15 dezenas como círculos coloridos em HTML.

    TIPOS:
    - 'normal': Roxo padrão
    - 'acerto': Verde neon
    - 'fria': Azul claro
    """
    classe = {
        'normal': 'dezena-circle',
        'acerto': 'dezena-circle dezena-acerto',
        'fria': 'dezena-circle dezena-fria'
    }

    html = '<div style="text-align: center; margin: 10px 0;">'
    for num in jogo:
        html += f'<span class="{classe.get(tipo, classe["normal"])}">{num:02d}</span>'
    html += '</div>'

    return html


def gerar_link_whatsapp(jogo, mensagem_extra=""):
    """
    Gera link da API do WhatsApp com os números do jogo.
    """
    numeros_formatados = " - ".join([f"{n:02d}" for n in jogo])

    texto = f"🍀 *Lotofácil Pro 2.0 - Elite Edition*\n\n"
    texto += f"📊 Meu Jogo: {numeros_formatados}\n"
    texto += f"➕ Soma: {sum(jogo)}\n"

    if mensagem_extra:
        texto += f"\n💡 {mensagem_extra}"

    texto_encoded = urllib.parse.quote(texto)
    link = f"https://api.whatsapp.com/send?text={texto_encoded}"

    return link


def simular_backtesting(jogo, df, concursos=50):
    """
    Simula quanto o jogo teria ganhado nos últimos N concursos.
    """
    resultados = {11: 0, 12: 0, 13: 0, 14: 0, 15: 0}
    jogo_set = set(jogo)

    for i in range(min(concursos, len(df))):
        sorteio = set(df.iloc[i]['Dezenas'])
        acertos = len(jogo_set.intersection(sorteio))

        if acertos >= 11:
            resultados[acertos] += 1

    return resultados


def inicializar_session_state():
    """
    Inicializa o Session State para persistência de dados
    """
    if 'meus_jogos' not in st.session_state:
        st.session_state.meus_jogos = []


def adicionar_jogo_salvo(jogo, nome=""):
    """
    Adiciona um jogo à lista de salvos
    """
    if nome == "":
        nome = f"Jogo {len(st.session_state.meus_jogos) + 1}"

    st.session_state.meus_jogos.append({
        'nome': nome,
        'jogo': jogo,
        'soma': sum(jogo)
    })


def remover_jogo_salvo(indice):
    """
    Remove um jogo da lista
    """
    if 0 <= indice < len(st.session_state.meus_jogos):
        st.session_state.meus_jogos.pop(indice)


# --- 3. GERADOR VALIDADO (da versão original) ---

PRIMOS = [2, 3, 5, 7, 11, 13, 17, 19, 23]


def validar_jogo_original(jogo):
    """Função de validação original (usada no Gerador Pro)"""
    validacoes = {}

    # Critério 1: Soma
    soma = sum(jogo)
    validacoes['soma'] = {
        'valor': soma,
        'valido': 180 <= soma <= 220,
        'esperado': '180-220'
    }

    # Critério 2: Sequências
    sequencias = []
    seq_atual = 1
    max_sequencia = 1

    for i in range(1, len(jogo)):
        if jogo[i] == jogo[i - 1] + 1:
            seq_atual += 1
            max_sequencia = max(max_sequencia, seq_atual)
        else:
            seq_atual = 1

    validacoes['sequencia'] = {
        'valor': max_sequencia,
        'valido': max_sequencia <= 4,
        'esperado': 'máx 4'
    }

    # Critério 3: Primos
    qtd_primos = len([n for n in jogo if n in PRIMOS])
    validacoes['primos'] = {
        'valor': qtd_primos,
        'valido': qtd_primos in [5, 6],
        'esperado': '5 ou 6'
    }

    todas_validas = all(v['valido'] for v in validacoes.values())

    return todas_validas, validacoes


def gerar_jogo_validado(estrategia, quentes, frias, max_tentativas=100):
    """Gerador validado original (usado no Gerador Pro)"""
    melhor_jogo = None
    melhor_score = 0

    for tentativa in range(max_tentativas):
        if estrategia == 'quente':
            jogo = sorted(random.sample(quentes, 15))
        elif estrategia == 'fria':
            jogo = sorted(random.sample(frias, min(10, len(frias))) + random.sample(quentes, 5))
        elif estrategia == 'equilibrado':
            jogo = sorted(random.sample(quentes, 9) + random.sample(frias, 6))
        else:  # random
            jogo = sorted(random.sample(range(1, 26), 15))

        valido, validacoes = validar_jogo_original(jogo)

        if valido:
            return jogo, True, validacoes

        score = sum(1 for v in validacoes.values() if v['valido'])
        if score > melhor_score:
            melhor_score = score
            melhor_jogo = jogo
            melhor_validacoes = validacoes

    return melhor_jogo, False, melhor_validacoes


# --- 4. INICIALIZAÇÃO ---
inicializar_session_state()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurações")
    qtd = st.slider("Qtd. Concursos (Backtesting)", 10, 100, 50)

    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    # Exibe jogos salvos
    st.header("💾 Meus Jogos Salvos")

    if len(st.session_state.meus_jogos) == 0:
        st.info("Nenhum jogo salvo ainda.\nGere jogos nas abas!")
    else:
        for idx, jogo_salvo in enumerate(st.session_state.meus_jogos):
            with st.expander(f"📌 {jogo_salvo['nome']}"):
                st.write(f"**Números:** {jogo_salvo['jogo']}")
                st.write(f"**Soma:** {jogo_salvo['soma']}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Remover", key=f"del_{idx}"):
                        remover_jogo_salvo(idx)
                        st.rerun()

                with col2:
                    link_wpp = gerar_link_whatsapp(jogo_salvo['jogo'], f"Jogo: {jogo_salvo['nome']}")
                    st.markdown(f"[📤 WhatsApp]({link_wpp})", unsafe_allow_html=True)

# Carrega dados
with st.spinner("🔄 Carregando dados da Caixa..."):
    df = engine.buscar_dados_oficiais(qtd)

# Área de estatísticas na sidebar
if df is not None and not df.empty:
    contagem, quentes, frias = engine.analisar_frequencias(df)

    with st.sidebar:
        st.write("---")
        st.header("🔥 TOP 15 QUENTES")
        st.caption(f"Últimos {qtd} jogos:")
        st.code(str(sorted(quentes)), language="python")

        st.write("---")
        st.header("❄️ TOP 10 FRIAS")
        st.code(str(sorted(frias)), language="python")

# --- 6. ÁREA PRINCIPAL ---
st.markdown("""
<div class="dashboard-header">
    <h1>🍀 Dashboard Lotofácil</h1>
    <div class="subtitle">Sistema Integrado de Análise Estatística • Fixos da Semana • Filtro Monte Carlo • Gerador Elite</div>
</div>
""", unsafe_allow_html=True)

if df is not None and not df.empty:
    # Calcula fixos da semana e probabilidades
    fixos_semana = engine.calcular_fixos_semana(df, top_n=10)
    df_prob = engine.calcular_probabilidades(df)
    tendencias = engine.tendencia_numeros(df)
    fixos_numeros = [f['numero'] for f in fixos_semana]

    # Inicializa filtro estatístico com dados históricos
    filtro_estat = FiltroEstatistico()
    filtro_estat.carregar_historico_de_dataframe(df)

    # Cria 7 abas
    aba1, aba_fixos, aba_filtro, aba2, aba3, aba4, aba5 = st.tabs([
        "📊 Dashboard",
        "📌 Fixos da Semana",
        "🧬 Filtro Estatístico",
        "🎲 Gerador Pro",
        "🎯 Gerador MESTRE",
        "🧪 Backtesting",
        "🏆 Arsenal + Conferidor"
    ])

    # ========== ABA 1: DASHBOARD ==========
    with aba1:
        ult = df.iloc[0]
        mais_quente = contagem.most_common(1)[0] if contagem else (0, 0)
        media_pares = df['Pares'].mean()
        media_impares = df['Impares'].mean()

        # ── KPI Cards Custom HTML ────────────────────────
        kpi_html = f"""
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;">
            <div class="kpi-card green">
                <div class="kpi-icon">🎰</div>
                <div class="kpi-value">#{ult['Concurso']}</div>
                <div class="kpi-label">Último Concurso</div>
                <div class="kpi-delta">{ult['Data']}</div>
            </div>
            <div class="kpi-card orange">
                <div class="kpi-icon">🔥</div>
                <div class="kpi-value">{mais_quente[0]:02d}</div>
                <div class="kpi-label">Nº Mais Quente</div>
                <div class="kpi-delta">{mais_quente[1]}× aparições</div>
            </div>
            <div class="kpi-card blue">
                <div class="kpi-icon">⚖️</div>
                <div class="kpi-value">{media_pares:.1f} / {media_impares:.1f}</div>
                <div class="kpi-label">Pares / Ímpares</div>
                <div class="kpi-delta">Média por concurso</div>
            </div>
            <div class="kpi-card purple">
                <div class="kpi-icon">📊</div>
                <div class="kpi-value">{len(df)}</div>
                <div class="kpi-label">Total Analisado</div>
                <div class="kpi-delta">{len(df) * 15} dezenas processadas</div>
            </div>
        </div>
        """
        st.markdown(kpi_html, unsafe_allow_html=True)

        st.divider()

        # ── Gráfico de Frequência com marcação dos Fixos ──────
        st.subheader("📊 Frequência de Todas as 25 Dezenas")

        df_freq_completo = pd.DataFrame({
            'Dezena': range(1, 26),
            'Freq': [contagem.get(i, 0) for i in range(1, 26)]
        })

        df_freq_completo['Categoria'] = df_freq_completo['Dezena'].apply(
            lambda x: '⭐ Fixo Semana' if x in fixos_numeros
            else ('🔥 Quente' if x in quentes[:5]
            else ('❄️ Fria' if x in frias else '● Mediana'))
        )

        fig_barras = px.bar(
            df_freq_completo,
            x='Dezena',
            y='Freq',
            color='Categoria',
            color_discrete_map={
                '⭐ Fixo Semana': '#ffa726',
                '🔥 Quente': '#00d084',
                '❄️ Fria': '#4ecdc4',
                '● Mediana': '#5c5c7a'
            },
            text='Freq',
            title=f'Análise completa dos últimos {qtd} concursos'
        )
        fig_barras.update_traces(textposition='outside', textfont=dict(size=11, color='rgba(240,240,240,0.7)'))
        fig_barras.update_layout(
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', color='#e0e0e0'),
            xaxis=dict(dtick=1, gridcolor='rgba(255,255,255,0.04)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.04)'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            margin=dict(t=60, b=40)
        )
        st.plotly_chart(fig_barras, use_container_width=True)

        st.divider()

        # ── Gráficos lado a lado: Rosca + Probabilidade ──────
        g_row1_left, g_row1_right = st.columns([1, 2])

        with g_row1_left:
            st.subheader("⚖️ Pares vs Ímpares")
            fig_rosca = px.pie(
                values=[df['Pares'].sum(), df['Impares'].sum()],
                names=['Pares', 'Ímpares'],
                color_discrete_sequence=['#00d084', '#ff6b35'],
                hole=0.65
            )
            fig_rosca.update_traces(
                textinfo='percent+label',
                textfont=dict(size=14, family='Inter'),
                marker=dict(line=dict(color='#1a1a2e', width=3))
            )
            fig_rosca.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', color='#e0e0e0'),
                showlegend=True,
                legend=dict(orientation='h', yanchor='bottom', y=-0.1, xanchor='center', x=0.5),
                margin=dict(t=20, b=40),
                annotations=[dict(
                    text=f"<b>{df['Pares'].sum() + df['Impares'].sum()}</b><br><span style='font-size:11px'>total</span>",
                    x=0.5, y=0.5, font_size=22, showarrow=False, font_color='#f0f0f0'
                )]
            )
            st.plotly_chart(fig_rosca, use_container_width=True)

        with g_row1_right:
            st.subheader("📈 Probabilidade (%) por Dezena")
            st.caption("Baseado na frequência histórica")

            fig_prob = px.bar(
                df_prob.sort_values('Probabilidade (%)', ascending=True),
                x='Probabilidade (%)',
                y='Dezena',
                color='Chance',
                color_discrete_map={
                    '🔥 Alta': '#ff6b35',
                    '🟡 Média': '#ffa726',
                    '❄️ Baixa': '#4ecdc4'
                },
                orientation='h',
                text='Probabilidade (%)',
                title=''
            )
            fig_prob.update_traces(textposition='outside', texttemplate='%{text:.1f}%', textfont=dict(size=10, color='rgba(240,240,240,0.6)'))
            fig_prob.update_layout(
                height=600,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', color='#e0e0e0'),
                yaxis=dict(dtick=1, gridcolor='rgba(255,255,255,0.04)'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.04)'),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
                margin=dict(t=40, b=20)
            )
            st.plotly_chart(fig_prob, use_container_width=True)

        st.divider()

        # ── Gráfico de Linha: Evolução da Soma ────────────────
        st.subheader("📉 Evolução da Soma das Dezenas")
        st.caption("Acompanhe o comportamento da soma ao longo dos últimos concursos")

        df_evolucao = df[['Concurso', 'Soma']].sort_values('Concurso')
        media_soma = df_evolucao['Soma'].mean()

        fig_linha = go.Figure()
        fig_linha.add_trace(go.Scatter(
            x=df_evolucao['Concurso'],
            y=df_evolucao['Soma'],
            mode='lines+markers',
            name='Soma',
            line=dict(color='#00d084', width=2.5),
            marker=dict(size=5, color='#00d084', line=dict(width=1, color='#0e1117')),
            fill='tozeroy',
            fillcolor='rgba(0, 208, 132, 0.08)'
        ))
        fig_linha.add_hline(
            y=media_soma, line_dash='dash', line_color='#ff6b35',
            annotation_text=f'Média: {media_soma:.0f}',
            annotation_position='top right',
            annotation_font=dict(color='#ff6b35', size=12, family='Inter')
        )
        fig_linha.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', color='#e0e0e0'),
            xaxis=dict(title='Concurso', gridcolor='rgba(255,255,255,0.04)'),
            yaxis=dict(title='Soma', gridcolor='rgba(255,255,255,0.04)'),
            margin=dict(t=20, b=40)
        )
        st.plotly_chart(fig_linha, use_container_width=True)

        st.divider()

        # ── Mapa de Calor + Radar lado a lado ─────────────────
        g2_left, g2_right = st.columns([3, 2])

        with g2_left:
            st.subheader("🌡️ Mapa de Calor das Dezenas")
            st.caption("Escala contínua: verde → laranja → vermelho")
            df_freq = pd.DataFrame(contagem.items(), columns=['Dezena', 'Freq']).sort_values('Dezena')

            fig_calor = px.bar(
                df_freq, x='Dezena', y='Freq',
                color='Freq',
                color_continuous_scale=['#4ecdc4', '#ffa726', '#ff6b35'],
                text='Freq',
                title=''
            )
            fig_calor.update_traces(textposition='outside', textfont=dict(size=10, color='rgba(240,240,240,0.6)'))
            fig_calor.update_layout(
                height=420,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', color='#e0e0e0'),
                xaxis=dict(dtick=1, gridcolor='rgba(255,255,255,0.04)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.04)'),
                coloraxis_colorbar=dict(title='Freq', tickfont=dict(color='#e0e0e0')),
                margin=dict(t=20, b=40)
            )
            st.plotly_chart(fig_calor, use_container_width=True)

        with g2_right:
            st.subheader("🎯 Radar: Fixos vs Frias")
            fix_freqs = [contagem.get(n, 0) for n in fixos_numeros[:8]]
            fri_freqs = [contagem.get(n, 0) for n in frias[:8]]
            labels = [f'D{n:02d}' for n in fixos_numeros[:8]]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=fix_freqs, theta=labels, fill='toself',
                name='🔥 Fixos', line=dict(color='#ffa726', width=2),
                fillcolor='rgba(255, 167, 38, 0.15)'
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=fri_freqs, theta=labels, fill='toself',
                name='❄️ Frias', line=dict(color='#4ecdc4', width=2),
                fillcolor='rgba(78, 205, 196, 0.15)'
            ))
            fig_radar.update_layout(
                polar=dict(
                    bgcolor='rgba(0,0,0,0)',
                    radialaxis=dict(gridcolor='rgba(255,255,255,0.08)', showticklabels=False),
                    angularaxis=dict(gridcolor='rgba(255,255,255,0.06)')
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', color='#e0e0e0'),
                height=420,
                legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5),
                margin=dict(t=20, b=40)
            )
            st.plotly_chart(fig_radar, use_container_width=True)

    # ========== ABA FIXOS DA SEMANA ==========
    with aba_fixos:
        st.subheader("📌 10 Fixos da Semana — Números Mais Quentes")
        st.caption(f"Os 10 números com maior frequência nos últimos {fixos_semana[0]['concursos_semana']} concursos")

        cols = st.columns(5)
        for idx, fixo in enumerate(fixos_semana):
            with cols[idx % 5]:
                tend = tendencias.get(fixo['numero'], '➡️ Estável')
                st.metric(
                    f"#{idx+1} — Dezena {fixo['numero']:02d}",
                    f"{fixo['frequencia']}x ({fixo['percentual']}%)",
                    tend
                )

        st.divider()
        st.subheader("💡 Sugestão de Jogo com os Fixos")
        complemento = [n for n in range(1, 26) if n not in fixos_numeros]
        random.shuffle(complemento)
        jogo_sugerido = sorted(fixos_numeros + complemento[:5])
        st.markdown(renderizar_dezenas_circulares(jogo_sugerido), unsafe_allow_html=True)
        col_s, col_w = st.columns(2)
        with col_s:
            if st.button("💾 Salvar Jogo Fixos", key="save_fixos", use_container_width=True):
                adicionar_jogo_salvo(jogo_sugerido, "Jogo Fixos da Semana")
                st.success("✅ Jogo salvo!")
                st.rerun()
        with col_w:
            link = gerar_link_whatsapp(jogo_sugerido, "Jogo com 10 Fixos da Semana")
            st.link_button("📤 WhatsApp", link, use_container_width=True)

    # ========== ABA FILTRO ESTATÍSTICO ==========
    with aba_filtro:
        st.subheader("🧬 Filtro de Normalidade Estatística")
        st.caption("Simulação de Monte Carlo + Análise Probabilística Avançada")

        with st.expander("⚙️ Parâmetros de Filtragem", expanded=False):
            resumo = filtro_estat.resumo_filtros()
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Soma", f"{resumo['soma']['min']}–{resumo['soma']['max']}", "Curva de Bell")
            p2.metric("Desvio Padrão (σ)", f"{resumo['desvio_padrao']['min']}–{resumo['desvio_padrao']['max']}", "Dispersão ideal")
            p3.metric("Ímpares", f"{resumo['paridade']['impares_min']}–{resumo['paridade']['impares_max']}", "Paridade ideal")
            p4.metric("Primos", f"{resumo['primos']['ideal']}", "Quantidade ideal")

        st.divider()
        st.markdown("### 🎲 Simulação de Monte Carlo")
        st.caption("Gera milhares de jogos aleatórios e filtra apenas os melhores estatisticamente")

        mc_col1, mc_col2 = st.columns([3, 1])
        with mc_col1:
            qtd_simulacao = st.select_slider(
                "Quantidade de jogos a simular:",
                options=[10_000, 50_000, 100_000, 200_000, 500_000],
                value=100_000,
                format_func=lambda x: f"{x:,}",
                key="mc_slider"
            )
        with mc_col2:
            top_k = st.number_input("Top K resultados:", min_value=5, max_value=50, value=10, key="mc_topk")

        if st.button("🚀 Iniciar Simulação Monte Carlo", type="primary", use_container_width=True, key="btn_monte_carlo"):
            with st.spinner(f"⏳ Simulando {qtd_simulacao:,} jogos..."):
                resultado_mc = filtro_estat.simulacao_monte_carlo(n=qtd_simulacao, top_k=top_k)

            if resultado_mc['status'] == 'sucesso':
                stats = resultado_mc['estatisticas']
                st.success(f"✅ Simulação concluída em {resultado_mc['tempo_segundos']:.2f}s")

                s1, s2, s3, s4 = st.columns(4)
                s1.metric("Jogos Gerados", f"{resultado_mc['total_gerado']:,}")
                s2.metric("Aprovados Soma", f"{stats['aprovados_soma']:,}", f"{stats['taxa_soma']:.1f}%")
                s3.metric("Aprovados Final", f"{stats['aprovados_desvio']:,}", f"{stats['taxa_final']:.1f}%")
                s4.metric("Tempo", f"{resultado_mc['tempo_segundos']:.2f}s", "⚡")

                st.divider()
                st.markdown(f"### 🏆 Top {len(resultado_mc['top_jogos'])} Jogos Elite")

                for idx, jogo_mc in enumerate(resultado_mc['top_jogos'], 1):
                    score = jogo_mc['score']
                    classificacao = jogo_mc['classificacao']
                    det = jogo_mc['detalhes']
                    cor_score = '#FFD700' if score >= 85 else ('#00fa9a' if score >= 70 else '#7b68ee')

                    with st.expander(f"#{idx} — Score: {score:.1f}/100 {classificacao}", expanded=(idx <= 3)):
                        html_mc = '<div style="text-align: center; margin: 10px 0;">'
                        for num in jogo_mc['jogo']:
                            html_mc += f'<span class="dezena-circle dezena-acerto">{num:02d}</span>'
                        html_mc += '</div>'
                        st.markdown(html_mc, unsafe_allow_html=True)

                        st.markdown(f'<div style="text-align:center;"><span style="font-size:36px;font-weight:900;color:{cor_score};">{score:.1f}</span><span style="font-size:16px;color:rgba(255,255,255,0.5);">/100</span></div>', unsafe_allow_html=True)

                        d1, d2, d3, d4, d5 = st.columns(5)
                        d1.metric("Soma", det['soma']['valor'], f"{'✅' if det['soma']['valido'] else '❌'} {det['soma']['pontos']}pts")
                        d2.metric("σ Desvio", f"{det['desvio_padrao']['valor']:.2f}", f"{'✅' if det['desvio_padrao']['valido'] else '❌'} {det['desvio_padrao']['pontos']}pts")
                        d3.metric("Paridade", det['paridade']['formato'], f"{'✅' if det['paridade']['valido'] else '❌'} {det['paridade']['pontos']}pts")
                        d4.metric("Primos", det['primos']['quantidade'], f"{'✅' if det['primos']['valido'] else '❌'} {det['primos']['pontos']}pts")
                        d5.metric("Calor", f"{det['calor'].get('media', 50):.0f}", f"{det['calor']['pontos']}pts")

                        col_save, col_wpp = st.columns(2)
                        with col_save:
                            if st.button(f"💾 Salvar", key=f"mc_save_{idx}", use_container_width=True):
                                adicionar_jogo_salvo(jogo_mc['jogo'], f"Monte Carlo #{idx} (Score: {score:.0f})")
                                st.success("✅ Salvo!")
                                st.rerun()
                        with col_wpp:
                            link = gerar_link_whatsapp(jogo_mc['jogo'], f"Monte Carlo #{idx} Score: {score:.0f}/100")
                            st.link_button("📤 WhatsApp", link, use_container_width=True)
            else:
                st.warning("⚠️ Nenhum jogo passou em todos os filtros. Tente com mais jogos.")

        st.divider()

        # ── Mapa de Calor Avançado das 25 Dezenas ──────────────
        st.markdown("### 🌡️ Mapa de Calor das 25 Dezenas")
        st.caption("Pontuação de calor baseada na frequência histórica")

        mapa = filtro_estat.get_mapa_calor_completo()
        df_calor = pd.DataFrame(mapa)

        fig_calor2 = px.bar(
            df_calor, x='dezena', y='calor',
            color='calor',
            color_continuous_scale=['#1e90ff', '#FFD700', '#ff4757'],
            text=df_calor['calor'].apply(lambda x: f'{x:.0f}'),
            title='Pontuação de Calor (0–100) por Dezena'
        )
        fig_calor2.update_traces(textposition='outside')
        fig_calor2.update_layout(
            height=450,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', color='white'),
            xaxis=dict(dtick=1),
            coloraxis_colorbar=dict(title='Calor')
        )
        st.plotly_chart(fig_calor2, use_container_width=True)

        st.divider()

        # ── Validação Individual ───────────────────────────────
        st.markdown("### 🔍 Validar Jogo Individual")
        entrada_validar = st.text_input(
            "Digite 15 números separados por espaço:",
            placeholder="Ex: 1 3 5 7 8 10 12 14 16 18 19 20 22 24 25",
            key="validar_filtro"
        )
        if entrada_validar:
            try:
                nums_val = sorted(list(set([int(n) for n in entrada_validar.replace(',', ' ').split() if n.strip().isdigit()])))
                if len(nums_val) == 15 and all(1 <= n <= 25 for n in nums_val):
                    resultado_val = filtro_estat.validar_jogo_completo(nums_val)
                    if 'erro' not in resultado_val:
                        score_val = resultado_val['score']
                        cor_val = '#00fa9a' if score_val >= 70 else ('#FFD700' if score_val >= 50 else '#ff4757')
                        st.markdown(renderizar_dezenas_circulares(nums_val), unsafe_allow_html=True)
                        st.markdown(f'<div style="text-align:center;"><div style="font-size:48px;font-weight:900;color:{cor_val};">{score_val:.1f}</div><div style="font-size:16px;color:rgba(255,255,255,0.6);">de 100 pontos — {resultado_val["classificacao"]}</div></div>', unsafe_allow_html=True)
                        det_val = resultado_val['detalhes']
                        v1, v2, v3, v4, v5 = st.columns(5)
                        v1.metric("Soma", det_val['soma']['valor'], f"{'✅' if det_val['soma']['valido'] else '❌'} {det_val['soma']['pontos']}pts")
                        v2.metric("σ Desvio", f"{det_val['desvio_padrao']['valor']:.2f}", f"{'✅' if det_val['desvio_padrao']['valido'] else '❌'} {det_val['desvio_padrao']['pontos']}pts")
                        v3.metric("Paridade", det_val['paridade']['formato'], f"{'✅' if det_val['paridade']['valido'] else '❌'} {det_val['paridade']['pontos']}pts")
                        v4.metric("Primos", det_val['primos']['quantidade'], f"{'✅' if det_val['primos']['valido'] else '❌'} {det_val['primos']['pontos']}pts")
                        v5.metric("Calor Médio", f"{det_val['calor'].get('media', 50):.0f}", f"{det_val['calor']['pontos']}pts")
                        if resultado_val['aprovado']:
                            st.success("✅ JOGO APROVADO — Dentro da normalidade estatística")
                        else:
                            st.warning("⚠️ JOGO ABAIXO DO PADRÃO — Fora da normalidade")
                    else:
                        st.error(f"❌ {resultado_val['erro']}")
                else:
                    st.error("❌ Digite exatamente 15 números entre 1 e 25")
            except Exception as e:
                st.error(f"❌ Formato inválido: {e}")

    # ========== ABA 2: GERADOR PRO (Original) ==========
    with aba2:
        st.subheader("🎲 Gerador de Jogos com Validação Profissional")
        st.caption("Todos os jogos passam por filtros de soma, sequência e primos")

        col1, col2 = st.columns([3, 1])

        with col1:
            estrategia = st.selectbox(
                "Escolha a Estratégia:",
                ["Quente (Top 15)", "Fria (Atrasados)", "Equilibrado (Mix)", "Aleatório"],
                help="Cada estratégia usa diferentes critérios estatísticos"
            )

        with col2:
            st.metric("🔥 Quentes", len(quentes))
            st.metric("❄️ Frias", len(frias))

        st.divider()

        # Botão de geração
        if st.button("🚀 Gerar Jogo Validado", type="primary", use_container_width=True):
            mapa_estrategia = {
                "Quente (Top 15)": "quente",
                "Fria (Atrasados)": "fria",
                "Equilibrado (Mix)": "equilibrado",
                "Aleatório": "random"
            }

            with st.spinner("Gerando jogo com validação profissional..."):
                jogo, valido, validacoes = gerar_jogo_validado(
                    mapa_estrategia[estrategia],
                    quentes,
                    frias
                )

            st.success("✅ Jogo Gerado com Sucesso!" if valido else "⚠️ Melhor jogo encontrado")

            with st.container():
                st.markdown("### 🎯 Seu Jogo")
                st.markdown(renderizar_dezenas_circulares(jogo, 'acerto' if valido else 'normal'),
                            unsafe_allow_html=True)

                st.markdown("### 📋 Validação Profissional")

                v1, v2, v3 = st.columns(3)

                with v1:
                    status_soma = "✅" if validacoes['soma']['valido'] else "❌"
                    st.metric(
                        f"{status_soma} Soma Total",
                        validacoes['soma']['valor'],
                        f"Esperado: {validacoes['soma']['esperado']}"
                    )

                with v2:
                    status_seq = "✅" if validacoes['sequencia']['valido'] else "❌"
                    st.metric(
                        f"{status_seq} Maior Sequência",
                        validacoes['sequencia']['valor'],
                        f"Esperado: {validacoes['sequencia']['esperado']}"
                    )

                with v3:
                    status_primos = "✅" if validacoes['primos']['valido'] else "❌"
                    st.metric(
                        f"{status_primos} Números Primos",
                        validacoes['primos']['valor'],
                        f"Esperado: {validacoes['primos']['esperado']}"
                    )

                if valido:
                    st.markdown('<span class="badge-valido">✅ JOGO VALIDADO</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="badge-invalido">⚠️ VALIDAÇÃO PARCIAL</span>', unsafe_allow_html=True)

                st.divider()

                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    nome_jogo = st.text_input("Nome do jogo:", value=f"Jogo {len(st.session_state.meus_jogos) + 1}",
                                              key="nome_jogo")

                with col_b:
                    if st.button("💾 Salvar Jogo", use_container_width=True):
                        adicionar_jogo_salvo(jogo, nome_jogo)
                        st.success(f"✅ {nome_jogo} salvo!")
                        st.rerun()

                with col_c:
                    link_wpp = gerar_link_whatsapp(jogo, f"Estratégia: {estrategia}")
                    st.link_button("📤 Enviar WhatsApp", link_wpp, use_container_width=True)

    # ========== ABA 3: GERADOR MESTRE (NOVO!) ==========
    with aba3:
        st.subheader("🎯 Gerador MESTRE - Sistema de 4 Jogos Elite")
        st.caption("Cruzamento de Arsenal + Estatística + Tendências + Simulação")

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📋 Dados de Entrada")

            melhor_jogo = st.selectbox(
                "Melhor Jogo do Arsenal (base na simulação):",
                list(engine.arsenal.keys()),
                help="Escolha qual jogo teve melhor performance nos seus testes"
            )

            if st.button("🧪 Simular Arsenal Completo", use_container_width=True):
                with st.spinner("Simulando performance dos 8 jogos..."):
                    ranking = engine.simular_desempenho(df)

                    st.success("✅ Simulação concluída!")

                    for idx, (nome, dados) in enumerate(ranking.items(), 1):
                        with st.expander(f"#{idx} - {nome} ({dados['pontos']} pontos)"):
                            st.markdown(renderizar_dezenas_circulares(dados['dezenas']), unsafe_allow_html=True)
                            st.write(f"**Total Premiações:** {dados['total_premiado']}")

                            if dados['acertos']:
                                st.write("**Detalhes:**")
                                for acerto in dados['acertos'][:5]:
                                    st.write(
                                        f"- Concurso {acerto['concurso']}: {acerto['acertos']} acertos ({acerto['premio']})")

        with col2:
            st.markdown("#### 🔥 Estatísticas Automáticas")
            st.metric("Números Quentes", len(quentes), f"Top {len(quentes)}")
            st.metric("Números Frios", len(frias), f"Atrasados 3+")
            st.metric("Último Sorteio", f"#{ult['Concurso']}", ult['Data'])

            st.code(f"Quentes: {sorted(quentes)}", language="python")
            st.code(f"Frios: {sorted(frias)}", language="python")

        st.divider()

        if st.button("🚀 GERAR 4 JOGOS ELITE", type="primary", use_container_width=True):
            with st.spinner("Gerando jogos com sistema MESTRE..."):
                jogos_gerados = gerador.gerar_4_jogos_elite(
                    quentes=quentes,
                    frios=frias,
                    ultimo_resultado=ult['Dezenas'],
                    melhor_jogo_nome=melhor_jogo
                )

            st.success("✅ 4 Jogos Elite Gerados com Sucesso!")

            for jogo in jogos_gerados:
                with st.container():
                    st.markdown(f"### {jogo['nome']} (Score: {jogo['score']}/100)")

                    st.markdown(renderizar_dezenas_circulares(jogo['dezenas'], 'acerto'), unsafe_allow_html=True)

                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        st.metric("Soma", sum(jogo['dezenas']))

                    with col_b:
                        st.metric("Paridade", jogo['paridade'])

                    with col_c:
                        st.metric("Score Confiança", f"{jogo['score']}/100")

                    st.info(f"**Estratégia:** {jogo['estrategia']}")

                    valido, validacoes = gerador.validar_jogo(jogo['dezenas'])

                    v1, v2, v3 = st.columns(3)

                    with v1:
                        status = "✅" if validacoes['soma']['valido'] else "❌"
                        st.metric(f"{status} Soma", validacoes['soma']['valor'], validacoes['soma']['esperado'])

                    with v2:
                        status = "✅" if validacoes['sequencia']['valido'] else "❌"
                        st.metric(f"{status} Sequência", validacoes['sequencia']['valor'],
                                  validacoes['sequencia']['esperado'])

                    with v3:
                        status = "✅" if validacoes['primos']['valido'] else "❌"
                        st.metric(f"{status} Primos", validacoes['primos']['valor'], validacoes['primos']['esperado'])

                    col_s, col_w = st.columns(2)

                    with col_s:
                        if st.button(f"💾 Salvar {jogo['nome']}", key=f"save_{jogo['nome']}", use_container_width=True):
                            adicionar_jogo_salvo(jogo['dezenas'], jogo['nome'])
                            st.success(f"✅ {jogo['nome']} salvo!")
                            st.rerun()

                    with col_w:
                        link = gerar_link_whatsapp(jogo['dezenas'], jogo['estrategia'])
                        st.link_button("📤 WhatsApp", link, use_container_width=True)

                    st.divider()

    # ========== ABA 4: BACKTESTING ==========
    with aba4:
        st.subheader("🧪 Simulador de Lucro (Backtesting)")
        st.caption(f"Teste quanto seu jogo teria ganhado nos últimos {qtd} concursos")

        col_input, col_actions = st.columns([3, 1])

        with col_input:
            entrada_jogo = st.text_input(
                "Digite 15 números separados por espaço:",
                placeholder="Ex: 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15",
                key="entrada_backtesting"
            )

        with col_actions:
            st.write("")
            st.write("")
            usar_salvos = st.checkbox("Usar jogos salvos", value=False)

        if entrada_jogo or usar_salvos:
            if usar_salvos and len(st.session_state.meus_jogos) > 0:
                st.divider()
                st.markdown("### 📊 Análise de Jogos Salvos")

                for jogo_salvo in st.session_state.meus_jogos:
                    jogo = jogo_salvo['jogo']

                    with st.expander(f"📌 {jogo_salvo['nome']} - Soma: {jogo_salvo['soma']}"):
                        st.markdown(renderizar_dezenas_circulares(jogo), unsafe_allow_html=True)

                        valido, validacoes = gerador.validar_jogo(jogo)

                        v1, v2, v3 = st.columns(3)
                        with v1:
                            st.metric("Soma", validacoes['soma']['valor'],
                                      "✅" if validacoes['soma']['valido'] else "❌")
                        with v2:
                            st.metric("Sequência", validacoes['sequencia']['valor'],
                                      "✅" if validacoes['sequencia']['valido'] else "❌")
                        with v3:
                            st.metric("Primos", validacoes['primos']['valor'],
                                      "✅" if validacoes['primos']['valido'] else "❌")

                        st.markdown("#### 💰 Simulação de Ganhos")
                        resultados = simular_backtesting(jogo, df, qtd)

                        col1, col2, col3, col4, col5 = st.columns(5)
                        col1.metric("11 pontos", resultados[11])
                        col2.metric("12 pontos", resultados[12])
                        col3.metric("13 pontos", resultados[13])
                        col4.metric("14 pontos", resultados[14])
                        col5.metric("15 pontos", resultados[15], "🏆")

                        total_premiacoes = sum(resultados.values())
                        if total_premiacoes > 0:
                            st.success(f"✅ Teria ganho {total_premiacoes} vezes nos últimos {qtd} concursos!")
                        else:
                            st.warning("Sem premiações nos últimos concursos.")

            elif entrada_jogo:
                try:
                    nums = sorted(
                        list(set([int(n) for n in entrada_jogo.replace(',', ' ').split() if n.strip().isdigit()])))

                    if len(nums) == 15 and all(1 <= n <= 25 for n in nums):
                        st.divider()

                        st.markdown("### 🎯 Jogo Analisado")
                        st.markdown(renderizar_dezenas_circulares(nums), unsafe_allow_html=True)

                        valido, validacoes = gerador.validar_jogo(nums)

                        st.markdown("### 📋 Validação")
                        v1, v2, v3 = st.columns(3)

                        with v1:
                            status = "✅" if validacoes['soma']['valido'] else "❌"
                            st.metric(f"{status} Soma", validacoes['soma']['valor'])
                        with v2:
                            status = "✅" if validacoes['sequencia']['valido'] else "❌"
                            st.metric(f"{status} Sequência", validacoes['sequencia']['valor'])
                        with v3:
                            status = "✅" if validacoes['primos']['valido'] else "❌"
                            st.metric(f"{status} Primos", validacoes['primos']['valor'])

                        st.markdown("### 💰 Simulação de Ganhos")
                        resultados = simular_backtesting(nums, df, qtd)

                        col1, col2, col3, col4, col5 = st.columns(5)
                        col1.metric("11 pontos", resultados[11])
                        col2.metric("12 pontos", resultados[12])
                        col3.metric("13 pontos", resultados[13])
                        col4.metric("14 pontos", resultados[14])
                        col5.metric("15 pontos", resultados[15], "🏆")

                        total_premiacoes = sum(resultados.values())

                        if total_premiacoes > 0:
                            st.success(f"✅ Teria ganho {total_premiacoes} vezes nos últimos {qtd} concursos!")
                        else:
                            st.warning("Sem premiações nos últimos concursos.")

                        st.divider()
                        col_save, col_wpp = st.columns(2)

                        with col_save:
                            if st.button("💾 Salvar este jogo", use_container_width=True):
                                adicionar_jogo_salvo(nums, f"Jogo Backtesting {len(st.session_state.meus_jogos) + 1}")
                                st.success("✅ Jogo salvo!")
                                st.rerun()

                        with col_wpp:
                            link = gerar_link_whatsapp(nums, f"Backtesting: {total_premiacoes} premiações")
                            st.link_button("📤 WhatsApp", link, use_container_width=True)

                    else:
                        st.error("❌ Digite exatamente 15 números entre 1 e 25")

                except:
                    st.error("❌ Formato inválido. Use números separados por espaço.")

        else:
            st.info("💡 Digite um jogo ou marque 'Usar jogos salvos' para começar a análise")

    # ========== ABA 5: ARSENAL + CONFERIDOR ==========
    with aba5:
        st.subheader("🏆 Arsenal de 8 Jogos + Conferidor")

        st.markdown("### 🎯 Arsenal Completo")

        for nome, dezenas in engine.arsenal.items():
            with st.expander(f"📌 {nome}"):
                st.markdown(renderizar_dezenas_circulares(dezenas), unsafe_allow_html=True)
                st.code(str(dezenas), language="python")

                resultados = simular_backtesting(dezenas, df, qtd)
                total = sum(resultados.values())

                if total > 0:
                    st.success(f"✅ Teria ganho {total} vezes nos últimos {qtd} concursos")

        st.divider()

        st.markdown("### 🎰 Conferidor de Resultados")
        st.caption(f"Confira seus números com o último sorteio: #{ult['Concurso']}")

        st.markdown("#### 🎰 Último Sorteio Oficial")
        st.markdown(renderizar_dezenas_circulares(ult['Dezenas'], 'acerto'), unsafe_allow_html=True)

        st.divider()

        entrada = st.text_input("Digite seus 15 números:", placeholder="Ex: 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15")

        if entrada:
            try:
                nums = sorted(list(set([int(n) for n in entrada.replace(',', ' ').split() if n.strip().isdigit()])))

                if len(nums) == 15:
                    real = set(ult['Dezenas'])
                    acertos = len(set(nums).intersection(real))

                    st.markdown("### 🎯 Seu Jogo")
                    st.markdown(renderizar_dezenas_circulares(nums), unsafe_allow_html=True)

                    st.markdown("### 📊 Resultado")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("Acertos", acertos, "🏆" if acertos >= 11 else "")

                    with col2:
                        premiacoes = {
                            15: "🏆 QUINA - PRÊMIO MÁXIMO!",
                            14: "🥈 QUADRA - 14 pontos",
                            13: "🥉 TERNO - 13 pontos",
                            12: "💰 12 pontos",
                            11: "💵 11 pontos"
                        }

                        if acertos >= 11:
                            st.success(premiacoes.get(acertos, ""))
                        else:
                            st.error(f"Não premiado ({acertos} acertos)")

                    st.markdown("### ✅ Números que Acertou")
                    acertados = sorted(set(nums).intersection(real))
                    st.markdown(renderizar_dezenas_circulares(acertados, 'acerto'), unsafe_allow_html=True)

                else:
                    st.warning("⚠️ Digite exatamente 15 números.")

            except:
                st.error("❌ Erro na digitação. Use apenas números separados por espaço.")

    # Tabela completa
    st.divider()
    with st.expander("📋 Ver Todos os Resultados Históricos"):
        st.dataframe(
            df.style.background_gradient(subset=['Soma'], cmap='Purples'),
            use_container_width=True
        )

else:
    st.error("❌ Erro ao carregar dados da Caixa. Tente novamente.")
    if st.button("🔄 Tentar Novamente"):
        st.rerun()