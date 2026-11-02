-- Grão: um gênero de filme. A coluna filmes e avaliações não soma entre gêneros,
-- pois um mesmo filme frequentemente pertence a múltiplos gêneros (ex: Ação e Aventura).
WITH generos_explodidos AS (
    -- Grão: um filme por gênero e suas notas individuais.
    SELECT
        f.filme_id,
        unnest(string_split(f.generos, '|')) AS genero,
        a.nota
    FROM refined.filmes AS f
    JOIN refined.avaliacoes AS a ON a.filme_id = f.filme_id
)
SELECT
    genero,
    count(DISTINCT filme_id)                                           AS filmes,
    count(*)                                                           AS avaliacoes,
    round(avg(nota), 2)                                                AS nota_media,
    round(100.0 * count(*) / sum(count(*)) OVER (), 2)                 AS pct_avaliacoes
FROM generos_explodidos
GROUP BY genero
ORDER BY avaliacoes DESC;
