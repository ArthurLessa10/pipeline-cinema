-- Grão: um usuário com pelo menos uma avaliação.
-- Que fração dos usuários concentra a maior parte das avaliações (Curva de Pareto)?
WITH avaliacoes_usuario AS (
    -- Grão: um usuário e sua quantidade de avaliações.
    SELECT
        usuario_id,
        count(*) AS avaliacoes
    FROM refined.avaliacoes
    GROUP BY usuario_id
)
SELECT
    usuario_id,
    avaliacoes,
    row_number() OVER (ORDER BY avaliacoes DESC, usuario_id ASC) AS posicao,
    round(
        100.0 * sum(avaliacoes) OVER (ORDER BY avaliacoes DESC, usuario_id ASC)
        / sum(avaliacoes) OVER (),
        2
    ) AS pct_acumulado
FROM avaliacoes_usuario
ORDER BY posicao ASC;
