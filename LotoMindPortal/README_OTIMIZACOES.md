# Otimizações e Refatoração - LotoMind Portal & MegaMind

Este arquivo documenta as recentes atualizações e otimizações de performance aplicadas no núcleo estatístico das loterias (Lotofácil e Mega-Sena). O principal objetivo foi eliminar a sobrecarga de processamento, resolver travamentos (Timeouts / Erro 500) do servidor Flask e melhorar a experiência de geração dos jogos.

## O que foi feito

### 1. Vetorização Matemática com NumPy (Método Monte Carlo)
O motor das simulações de Monte Carlo sofreu uma alteração arquitetural profunda. Os algoritmos que geravam e filtravam jogos através de laços repetitivos (`for / while` iterando jogo a jogo) foram substituídos por operações matriciais utilizando **NumPy**.
*   **Geração em Massa:** Os milhares de jogos agora são gerados e ordenados em milissegundos usando matrizes multidimensionais (`np.random.rand` e `argsort`).
*   **Filtros Vetorizados:** Cálculos estatísticos, como somas, quantitativo de pares/ímpares e desvios padrões globais são aplicados na matriz inteira ao mesmo tempo através de máscaras espaciais do NumPy.
*   **Multiplicação de Matrizes (Lotofácil):** Para cruzar as simulações com o histórico da Lotofácil, transformamos os jogos em matrizes *one-hot encoded* e multiplicamos pelo histórico oficial. Isso reduziu o tempo de checagem contra o histórico de dezenas de segundos para frações de segundo.

### 2. Correção e Prevenção de Falhas Visuais (JSON)
Vários erros na página visual eram ocasionados pois o servidor tentava responder as requisições com tipos numéricos originários do NumPy (ex: `np.int64`, `np.float64`), que não são serializáveis nativamente em arquivos JSON quando o Flask tenta enviar a resposta ao JavaScript.
*   **Tipagem Forte:** Todo dado estatístico final devolvido pelas engines é convertido estritamente em primitivas Python (`int`, `float`, e uso do `.tolist()` em arrays finais). Isso garante a comunicação correta com a Interface (`frontend`).

### 3. Estabilidade da API Externa
A classe `MegaSenaEngine` consumia dados direto da API Pública da Loteria. Foram incluídos:
*   Tempos de resposta máximos (`timeouts`) para não travar a aplicação quando o site da Caixa está offline.
*   Geração automática de dados de reserva (Mock de dados seguros) para que o sistema não pare total em momentos de instabilidade (erro 403 / 503) das Loterias da Caixa.

### 4. Scripts de Benchmark em Nuvem
Criamos arquivos exclusivos na raiz do projeto para o desenvolvedor atestar a performance e validar retornos da API via CLI (sem precisar de Postman / Interface Web).

---

## Principais Códigos Modificados (Files)

*   **`modules/lotofacil/monte_carlo.py`**
    *   Refatoração profunda da classe `LotofacilMonteCarlo`. Adicionado o `historico_matrix`. 
    *   O motor da Lotofácil agora filtra, elimina jogos duplicados e seleciona os Top K de modo 100% vetorizado.

*   **`modules/megasena/statistical_filter.py`**
    *   Reescrita total da função `simulacao_monte_carlo`.
    *   O Filtro Estatístico da Mega-Sena foi aperfeiçoado para avaliar Somas (100 a 250), Desvios Padrões (14 a 22) e Paridade sem causar gargalos na CPU do servidor.

*   **`modules/megasena/engine.py`**
    *   Adicionadas defesas de Request (headers) e mock de `[MegaSenaEngine] API da Caixa indisponível`.
    *   Agrupamento de quadrantes, ciclos e sistema de backtesting para a Mega.

*   **`test_mc.py` e `test_client.py`**
    *   Códigos utilitários para estressar / depurar os módulos matemáticos e checar em quantos segundos o servidor processa até 100.000 jogos simultâneos e devolve em string JSON válida.
