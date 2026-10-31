# Especificação: raw -> refined (Pipeline Cinema)

Esta especificação descreve as transformações aplicadas para migrar os dados brutos de `raw` para o schema `refined`.
Todas as decisões são justificadas com base nas métricas reais contadas diretamente em `raw` (somente leitura).

---

## 1. Escopo e Nomenclatura
- Lê de `raw.filmes`, `raw.avaliacoes` e `raw.tags`.
- Escreve em `refined.filmes`, `refined.avaliacoes` e `refined.tags`.
- Nunca altera nem apaga dados do schema `raw`.
- Padronização em português e `snake_case` nas colunas.

---

## 2. Tabela `refined.filmes`

### Contagens em raw
- 9.742 linhas, todas com `movieId` único (0 duplicatas de chave primária).
- 9.729 filmes trazem o ano de lançamento entre parênteses no final do título (ex: `"Toy Story (1995)"`).
- 13 filmes não possuem ano no título (ex: `"Babylon 5"`, `"Ready Player One"`, `"Hyena Road"`).
- 34 filmes possuem o texto `"(no genres listed)"` no campo de gêneros.

### Decisões e Tipos
1. **`filme_id`**: `INTEGER`, convertido de `movieId`.
2. **`titulo`**: `VARCHAR`. Remove o sufixo de ano `(YYYY)` e espaços nas bordas (`trim(regexp_replace(title, '\s*\(\d{4}\)', ''))`).
   *Motivo:* O ano passa a ter coluna própria e o título fica limpo para buscas e visualização.
3. **`ano_lancamento`**: `INTEGER`. Extraído via regex `regexp_extract(title, '\((\d{4})\)', 1)`.
   *Motivo:* Permite agregações e análises temporais no SQL. Para os 13 filmes sem ano, o valor permanece `NULL` sem descartar o filme.
4. **`generos`**: `VARCHAR`. Se o valor for `"(no genres listed)"`, converte para `'sem_genero'`. Caso contrário, mantém a lista de gêneros separada por pipe (`|`).
   *Motivo:* 34 filmes não tinham gênero especificado; padronizar com `'sem_genero'` evita tratar string com parênteses em queries analíticas.

---

## 3. Tabela `refined.avaliacoes`

### Contagens em raw
- 100.836 linhas.
- 100.836 pares distintos de `(userId, movieId)` — cada usuário avaliou cada filme no máximo uma vez.
- 0 duplicatas exatas.
- Notas variam de 0.5 a 5.0 (exatamente dentro do domínio esperado).
- Timestamps variam de `828124615` (29/03/1996) até `1537799250` (24/09/2018).
- 0 avaliações com `movieId` inexistente em `raw.filmes` (integridade referencial de 100%).

### Decisões e Tipos
1. **`usuario_id`**: `INTEGER`, convertido de `userId`.
2. **`filme_id`**: `INTEGER`, convertido de `movieId`.
3. **`nota`**: `DOUBLE`, convertido de `rating`.
   *Motivo:* As notas são fracionárias com passos de 0.5 (ex: 3.5, 4.0).
4. **`data_avaliacao`**: `TIMESTAMP`, convertido de timestamp UNIX via `to_timestamp(CAST(timestamp AS BIGINT))::TIMESTAMP`.
   *Motivo:* Permite extração de ano, mês e ordenação cronológica diretamente no DuckDB.

---

## 4. Tabela `refined.tags`

### Contagens em raw
- 3.683 linhas.
- 3.683 linhas distintas, 0 duplicatas exatas, 0 nulos.
- 0 tags com `movieId` inexistente em `raw.filmes`.

### Decisões e Tipos
1. **`usuario_id`**: `INTEGER`, convertido de `userId`.
2. **`filme_id`**: `INTEGER`, convertido de `movieId`.
3. **`tag`**: `VARCHAR`. Normalizada com `lower(trim(tag))`.
   *Motivo:* Evita variações de caixa (ex: `"Funny"` vs `"funny"`) em agrupamentos analíticos.
4. **`data_tag`**: `TIMESTAMP`, convertido de timestamp UNIX.

---

## 5. Critérios de Aceite da Transformação
- `refined.filmes`: exatamente 9.742 linhas, com 13 nulos em `ano_lancamento` e 34 filmes `'sem_genero'`.
- `refined.avaliacoes`: exatamente 100.836 linhas, sem nulos em qualquer coluna, notas entre 0.5 e 5.0.
- `refined.tags`: exatamente 3.683 linhas, tags em minúsculas e sem espaços nas bordas.
- Total geral de linhas em `refined`: **114.261 linhas** (exatamente o mesmo total de `raw`, provando que nenhuma linha foi descartada indevidamente).
