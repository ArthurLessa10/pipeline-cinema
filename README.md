# Pipeline Cinema · Análise Analítica com MovieLens

Pipeline de dados end-to-end em Python, DuckDB e SQL construído sobre o dataset oficial **MovieLens (ml-latest-small)** da Universidade de Minnesota (GroupLens Research).

Projeto final da formação profissional de Engenharia de Dados Júnior.

---

## 1. Fonte dos Dados e Licença

- **Origem:** [GroupLens Research / Universidade de Minnesota](https://grouplens.org/datasets/movielens/)
- **Arquivo:** `ml-latest-small.zip` (100.836 avaliações e 3.683 tags aplicadas a 9.742 filmes por 610 usuários entre 1996 e 2018).
- **Licença:** Aberta para ensino e pesquisa acadêmica, com atribuição expressa ao GroupLens Research.
- **Ingestão automatizada:** O script `pipeline/ingestao.py` baixa o arquivo oficial da universidade e descompacta os CSVs diretamente para a pasta `raw/`.

---

## 2. O Grão de Cada Tabela

### Camada Bruta (`raw`)
Espelha os arquivos CSV exatamente como vieram, com tipagem bruta (`all_varchar=true`):
- **`raw.filmes`** (9.742 linhas): O grão é um filme cadastrado (`movieId`, `title`, `genres`).
- **`raw.avaliacoes`** (100.836 linhas): O grão é uma avaliação de um usuário sobre um filme (`userId`, `movieId`, `rating`, `timestamp`).
- **`raw.tags`** (3.683 linhas): O grão é uma palavra-chave atribuída por um usuário a um filme (`userId`, `movieId`, `tag`, `timestamp`).

### Camada Transformada (`refined`)
Padronização de tipos, normalização textual e integridade referencial:
- **`refined.filmes`** (9.742 linhas): O grão é um filme limpo.
  - `filme_id` (INTEGER, PK).
  - `titulo` (VARCHAR): título sem o ano e com espaços aparados.
  - `ano_lancamento` (INTEGER): ano de 4 dígitos extraído via regex `\((\d{4})\)`. 13 filmes sem ano no título recebem `NULL` sem descarte de linha.
  - `generos` (VARCHAR): lista de gêneros separada por pipe; os 34 filmes com `(no genres listed)` foram convertidos para `'sem_genero'`.
- **`refined.avaliacoes`** (100.836 linhas): O grão é uma avaliação com nota e data real.
  - `usuario_id` (INTEGER), `filme_id` (INTEGER, FK para `refined.filmes`).
  - `nota` (DOUBLE): notas fracionárias de 0.5 a 5.0.
  - `data_avaliacao` (TIMESTAMP): timestamp convertido do UNIX epoch.
- **`refined.tags`** (3.683 linhas): O grão é uma tag limpa.
  - `usuario_id` (INTEGER), `filme_id` (INTEGER, FK).
  - `tag` (VARCHAR): texto em minúsculas e sem espaços nas bordas (`lower(trim(tag))`).
  - `data_tag` (TIMESTAMP): timestamp convertido do UNIX epoch.

---

## 3. As Três Camadas e os Indicadores de Negócio (`marts`)

Cada indicador analítico reside em um arquivo SQL individual em `sql/marts/` com o grão explicitamente declarado na primeira linha e em todas as CTEs:

1. **`01_top_filmes.sql`** (450 linhas):
   - *Pergunta:* Quais são os filmes mais bem avaliados com relevância estatística?
   - *Grão:* Um filme qualificado com pelo menos 50 avaliações do público.
   - *Top 1:* *The Shawshank Redemption* (317 avaliações, nota média 4,43).
2. **`02_evolucao_decadas.sql`** (12 linhas):
   - *Pergunta:* Como a nota média e o volume de produção evoluíram por década?
   - *Grão:* Uma década de lançamento (de 1900 a 2010).
   - *Insight:* Décadas de ouro (1940 e 1950) lideram em satisfação média (3,87 e 3,85), enquanto as décadas de 1990 e 2000 concentram 66% de todo o volume avaliado.
3. **`03_ranking_generos.sql`** (20 linhas):
   - *Pergunta:* Quais gêneros concentram mais avaliações e qual a nota de cada um?
   - *Grão:* Um gênero de filme (explodido via `unnest(string_split(generos, '|'))`).
   - *Liderança:* Drama (41.928 avaliações, média 3,66) e Comédia (39.053 avaliações, média 3,38).
4. **`04_concentracao_usuarios.sql`** (610 linhas):
   - *Pergunta:* Que fração dos usuários concentra a maior parte do engajamento (Pareto)?
   - *Grão:* Um usuário ativo.
   - *Insight:* Apenas 215 usuários (35,2% da base) são responsáveis por 80% de todas as avaliações da plataforma.
5. **`05_kpis_plataforma.sql`** (1 linha):
   - *Pergunta:* Quais são os grandes números macro da plataforma?
   - *Grão:* A plataforma inteira, uma única linha.
   - *Totais:* 9.742 filmes cadastrados, 9.724 filmes avaliados, 100.836 avaliações, 610 usuários, nota média global de 3,50 e média de 165,3 avaliações por usuário.

---

## 4. Como Rodar o Projeto do Zero

O pipeline é 100% reproduzível utilizando o gerenciador de pacotes **uv**:

### 1. Clonar o repositório e sincronizar dependências
```bash
git clone https://github.com/ArthurLessa10/pipeline-cinema.git
cd pipeline-cinema
uv sync
```

### 2. Rodar a Ingestão (Raw)
Baixa os dados oficiais do MovieLens e cria o schema `raw` no DuckDB:
```bash
uv run python -m pipeline.ingestao
```
Saída esperada:
```text
✓ raw.filmes              9.742 linhas
✓ raw.avaliacoes        100.836 linhas
✓ raw.tags                3.683 linhas
  total               114.261 linhas
```

### 3. Rodar a Transformação (Refined)
Executa a limpeza, tipagem e extrações baseadas na especificação:
```bash
uv run python -m pipeline.transformacao
```
Saída esperada:
```text
✓ refined.filmes          9.742 ->   9.742 linhas (0 duplicatas)
    nulos mantidos: ano_lancamento 13
✓ refined.avaliacoes    100.836 -> 100.836 linhas (0 duplicatas)
✓ refined.tags            3.683 ->   3.683 linhas (0 duplicatas)
  total                     114.261 linhas
```

### 4. Rodar os Marts Analíticos (Marts)
Executa as consultas SQL com garantia de atomicidade transacional:
```bash
uv run python -m pipeline.marts
```
Saída esperada:
```text
✓ marts.top_filmes                  450 linhas
✓ marts.evolucao_decadas             12 linhas
✓ marts.ranking_generos              20 linhas
✓ marts.concentracao_usuarios       610 linhas
✓ marts.kpis_plataforma               1 linha
  5 marts                        1.093 linhas
```

### 5. Rodar os Testes Unitários com Cobertura
Roda a suíte completa de testes unitários isolados com dados sintéticos (sem abrir o banco real `cinema.duckdb`):
```bash
uv run pytest --cov
```
Saída esperada:
```text
Name                        Stmts   Miss  Cover   Missing
---------------------------------------------------------
pipeline\__init__.py            0      0   100%
pipeline\db.py                 12      0   100%
pipeline\ingestao.py           59     22    63%
pipeline\marts.py              72     16    78%
pipeline\transformacao.py      49     12    76%
---------------------------------------------------------
TOTAL                         192     50    74%
Required test coverage of 60.0% reached. Total coverage: 73.96%
============================= 10 passed in 2.44s ==============================
```

---

## 5. Auditoria de Interação com a IA: Onde a IA Errou e Como Foi Corrigido

Seguindo o princípio do desenvolvimento guiado por especificação e conferência rigorosa por contagens, a interação com o assistente de IA passou por três correções importantes durante a construção:

1. **Agrupamento por Décadas em Ponto Flutuante:**
   - *O que a IA assumiu:* A IA propôs inicialmente calcular a década com `(ano_lancamento / 10) * 10`.
   - *Onde falhou:* No DuckDB, a barra `/` efetua divisão real (float), gerando valores como `1902.0` em vez de agrupar em décadas inteiras (`1900`).
   - *Como foi descoberto:* Ao inspecionar o resultado do SELECT, a query retornava 106 linhas em vez de agrupar em décadas.
   - *Correção aplicada:* Alterado para `floor(f.ano_lancamento / 10)::INT * 10`, agrupando rigorosamente nas 12 décadas reais de cinema da base (1900 a 2010).

2. **Referência Ambígua em Coluna de JOIN:**
   - *O que a IA assumiu:* No cálculo de contagem de filmes por década, a IA escreveu `count(DISTINCT filme_id)`.
   - *Onde falhou:* Como `filmes` e `avaliacoes` estavam unidas por `JOIN`, o DuckDB disparou `Binder Error: Ambiguous reference to column name "filme_id"`.
   - *Como foi descoberto:* Falha imediata na execução do teste do SQL.
   - *Correção aplicada:* Prefixação explícita da tabela de origem (`f.filme_id`), mantendo a regra de integridade do SQL.

3. **Teste Unitário com Download Indevido:**
   - *O que a IA assumiu:* Ao escrever o teste unitário `test_ingerir_falha_se_arquivo_faltando`, a IA esperava que a falta de um CSV na pasta temporária gerasse `SystemExit`.
   - *Onde falhou:* A função `ingerir()` disparava internamente `garantir_dados_brutos()`, que baixava os arquivos da internet em tempo de teste e fazia a função passar.
   - *Como foi descoberto:* O teste falhou no `pytest` com `Failed: DID NOT RAISE SystemExit`.
   - *Correção aplicada:* Adicionado o parâmetro de controle `auto_download=False` na assinatura de `ingerir()`, garantindo que os testes unitários sejam verdadeiramente isolados e nunca dependam de rede externa.
