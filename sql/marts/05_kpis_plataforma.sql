-- Grão: a plataforma inteira, uma única linha.
-- Os grandes números macro do catálogo e engajamento da plataforma.
WITH metricas AS (
    -- Grão: a plataforma inteira, 1 linha.
    SELECT
        (SELECT count(*) FROM refined.filmes)                   AS total_filmes,
        (SELECT count(DISTINCT filme_id) FROM refined.avaliacoes) AS filmes_avaliados,
        count(*)                                                AS total_avaliacoes,
        count(DISTINCT usuario_id)                              AS total_usuarios,
        round(avg(nota), 2)                                     AS nota_media_global,
        round(median(nota), 2)                                  AS nota_mediana_global,
        round(count(*)::DOUBLE / count(DISTINCT usuario_id), 1)  AS media_avaliacoes_por_usuario
    FROM refined.avaliacoes
)
SELECT * FROM metricas;
