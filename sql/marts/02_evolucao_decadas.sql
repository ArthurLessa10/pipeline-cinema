-- Grão: uma década de lançamento de filmes.
-- Como a média das notas e o volume de produção evoluíram ao longo das décadas?
SELECT
    floor(f.ano_lancamento / 10)::INT * 10 AS decada,
    count(DISTINCT f.filme_id)             AS total_filmes,
    count(a.nota)                          AS total_avaliacoes,
    round(avg(a.nota), 2)                  AS nota_media
FROM refined.filmes AS f
JOIN refined.avaliacoes AS a ON a.filme_id = f.filme_id
WHERE f.ano_lancamento IS NOT NULL
GROUP BY decada
ORDER BY decada ASC;
