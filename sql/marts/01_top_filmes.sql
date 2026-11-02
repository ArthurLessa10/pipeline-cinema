-- Grão: um filme com no mínimo 50 avaliações do público.
-- Quais os filmes mais bem avaliados com relevância estatística?
SELECT
    f.filme_id,
    f.titulo,
    f.ano_lancamento,
    count(a.nota)         AS avaliacoes,
    round(avg(a.nota), 2) AS nota_media
FROM refined.filmes AS f
JOIN refined.avaliacoes AS a ON a.filme_id = f.filme_id
GROUP BY f.filme_id, f.titulo, f.ano_lancamento
HAVING count(a.nota) >= 50
ORDER BY nota_media DESC, avaliacoes DESC, f.filme_id ASC;
