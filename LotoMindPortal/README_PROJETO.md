# LotoMind Portal 🧠🎰

Bem-vindo ao repositório oficial do **LotoMind Portal**, uma aplicação web robusta, modular e focada em performance para análise estatística, geração inteligente e gestão de jogos voltados para as modalidades **Lotofácil** e **Mega-Sena**.

## 📌 Visão Geral da Arquitetura

Este projeto foi construído sobre a fundação do **Python + Flask**, adotando o padrão **Factory Pattern (`create_app`)** misturado com a lógica de **Blueprints**, o que garante um código escalável, de fácil manutenção e extremamente organizado.

### **Pilha Tecnológica (Tech Stack)**
- **Back-End:** Python 3, Flask, Flask-Login, Flask-SQLAlchemy, Flask-Mail.
- **Front-End:** Jinja2 Templates, HTML5, CSS3, e Vanilla JavaScript (Fetch API para chamadas assíncronas ao servidor e renderização reativa).
- **Matemática e Performance:** NumPy (para computação matricial e vetorização extrema dos algoritmos preditivos de Monte Carlo).
- **Banco de Dados:** SQLite (via SQLAlchemy) gerando as tabelas localmente com persistência segura.

---

## 📂 Estrutura de Diretórios e Módulos

```text
LotoMindPortal/
├── app.py                   # Ponto de entrada (Factory de criação Flask)
├── config.py                # Controles de variáveis de ambiente e segurança
├── models.py                # Esquemas SQLAlchemy (Usuários, Históricos, Arsenal)
├── auth.py                  # Autenticação segura de usuários e controle de rotas
├── init_db.py / setup_user  # Scripts utilitários para popular o DB
├── README_OTIMIZACOES.md    # Log descritivo das melhorias matemáticas (Numpy)
├── modules/                 # 🚀 Lógica de Negócios (Blueprints)
│   ├── lotofacil/           # Domínio total sobre a Lotofácil
│   │   ├── engine.py        # Coleta e cache dos números oficiais da Caixa
│   │   ├── generator.py     # Lógica básica e randômica
│   │   ├── intelligence_engine.py  # Mapas de calor, frequências, pares/ímpares
│   │   ├── monte_carlo.py   # Simulações pesadas (vetorizadas com NumPy)
│   │   └── routes.py        # Controladores REST e de templates para Lotofácil
│   ├── megasena/            # Domínio total sobre a Mega-Sena
│   │   ├── engine.py        # Mocks e consumo contra falhas na API pública (Timeouts)
│   │   ├── generator.py     # Predição baseada em dispersão do volante
│   │   ├── statistical_filter.py # Filtro de sumário, desvios e matrizes
│   │   └── routes.py        # Controladores
│   └── arsenal/             # Banco de Jogos Salvos
│       └── routes.py        # Lógica de Slot Machines (até 8 espaços de salvamento)
├── templates/               # Views e interfaces do portal
├── static/                  # Folhas de estilo (CSS) originais, animações, logos e JS client-side
└── test_mc.py / test_client # Testes de stress e benchmark paralelos
```

---

## 🗄 Arquitetura de Dados (`models.py`)

O banco de dados gerencia a complexidade de autenticação e os modelos preditivos:
1. **`User` / `LoginSession`:** Controle rigoroso de acessos, com suporte a registro de IP, `user_agent` contra fraudes, e ciclo de vida de sessões permanentes.
2. **`EmailToken`:** Infraestrutura de autenticação de 2 Fatores (MFA / 2FA) através de tokens de e-mail limitados (seis dígitos / expirável em 10 minutos).
3. **`SorteioLotofacil` / `SorteioMegaSena`:** Tabelas de espelhamento que agem como cache do histórico dos bancos das Loterias da Caixa (evita ser bloqueado caso a rede da Caixa caia - "API Failback").
4. **`JogoSalvo` (O Arsenal):** Entidade que une o usuário a perfis de matrizes (até 8 slots), armazenando seu histórico de `score_metric` que indica a confiança estatística do bilhete.

---

## ⚡ Matemática Vetorizada e Performance

Uma das características arquiteturais mais invejáveis deste software documentada é sua capacidade de esgotar o hardware utilizando processamento pseudo-Vetorizado.
- **Refatoração NumPy (Monte Carlo & Statistical Filters):** Os temidos *Timeouts* e erros *HTTP 500* foram resolvidos removendo laços de repetição arcaicos (`for` e `while`). 
- As permutações de sorteios geram milhões de possibilidades de uma única vez em **memória multidimensional**, filtrando desvios padrões globais e matrizes *one-hot encoded* em milissegundos.
- **Tipagem Segura:** Todo número de precisão da engine matemática é sanitizado (por exemplo, voltando de primitivas em `int` ou `float` comum via `.tolist()`), salvando a conversão JSON nas requisições client-side com Vue/JS puro na interface amigável.

---

## 🛡️ Estabilidade & API Externa

A LotoMind sabe que não pode parar quando a provedora cai:
1. **Fallback Automático (`engine.py`)**: As queries externas em sites públicos controlam o tempo de requisição máximo (Timeout).
2. **Mocking**: Se as Loterias da Caixa entrarem em colapso (erros HTTP 403 ou 503), o portal não exibe uma "Tela de Tela de Pânico"; invés disso, o construtor retorna mocks limpos ou lê direto de seu cache assíncrono espelhado, garantindo 100% de tempo de atividade (Uptime).

---
*Este é o documento resumo que mapeia não apenas as regras de código, mas a inteligência por trás do funcionamento unificado do ambiente LotoMind.*
