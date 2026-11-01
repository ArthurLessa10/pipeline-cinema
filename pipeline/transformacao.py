"""pipeline/transformacao.py — Processamento da camada raw para refined.

SPEC (baseada em specs/transformacao.md)
1. ESCOPO
   Lê de raw, grava em refined. Nunca altera o schema raw.
   O schema refined é recriado a cada execução (DROP SCHEMA IF EXISTS refined CASCADE).

2. TABELAS PRODUZIDAS
   - refined.filmes:
       filme_id (INTEGER), titulo (VARCHAR sem o ano),
       ano_lancamento (INTEGER extraído de (YYYY), NULL para os 13 casos sem ano),
       generos (VARCHAR, '(no genres listed)' vira 'sem_genero').
   - refined.avaliacoes:
       usuario_id (INTEGER), filme_id (INTEGER), nota (DOUBLE),
       data_avaliacao (TIMESTAMP convertido do UNIX epoch).
   - refined.tags:
       usuario_id (INTEGER), filme_id (INTEGER), tag (VARCHAR lower e trim),
       data_tag (TIMESTAMP convertido do UNIX epoch).

3. SAÍDA NO TERMINAL
   Mostra cada tabela, contagem antes -> depois, duplicatas removidas e nulos documentados:
     ✓ refined.filmes          9.742 -> 9.742 linhas (0 duplicatas)
         nulos mantidos: ano_lancamento 13
     ✓ refined.avaliacoes    100.836 -> 100.836 linhas (0 duplicatas)
     ✓ refined.tags            3.683 -> 3.683 linhas (0 duplicatas)
       total                 114.261 linhas
   stdout configurado para UTF-8.

4. VALIDAÇÕES E ERRO
   Se faltar qualquer uma das 3 tabelas em raw, avisa para rodar:
     "uv run python -m pipeline.ingestao"
   e encerra com sys.exit(1).
"""

from pathlib import Path
import sys
import duckdb

from pipeline.db import conectar, criar_schema

# Reconfigura stdout para utf-8 em terminais Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TABELAS_ESPERADAS = ["filmes", "avaliacoes", "tags"]


def validar_raw(con: duckdb.DuckDBPyConnection) -> None:
    """Verifica se todas as tabelas brutas existem em raw antes de transformar."""
    tabelas_existentes = [
        row[0]
        for row in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'raw'"
        ).fetchall()
    ]
    faltantes = [t for t in TABELAS_ESPERADAS if t not in tabelas_existentes]
    if faltantes:
        sys.stderr.write(
            f"Erro: Tabelas ausentes em raw: {', '.join(faltantes)}\n"
            f"Execute primeiro: uv run python -m pipeline.ingestao\n"
        )
        con.close()
        sys.exit(1)


def transformar(caminho_banco: str = "cinema.duckdb") -> dict[str, dict[str, int]]:
    """Transforma os dados de raw para refined com tipagem forte e normalização."""
    con = conectar(caminho_banco)
    validar_raw(con)

    # Recria o schema refined garantindo idempotência
    con.execute("DROP SCHEMA IF EXISTS refined CASCADE")
    criar_schema(con, "refined")

    resultados = {}

    # 1. refined.filmes
    antes_filmes = con.execute("SELECT count(*) FROM raw.filmes").fetchone()[0]
    con.execute(r"""
        CREATE TABLE refined.filmes AS
        SELECT
            CAST(movieId AS INTEGER) AS filme_id,
            trim(regexp_replace(title, '\s*\(\d{4}\)', '')) AS titulo,
            TRY_CAST(regexp_extract(title, '\((\d{4})\)', 1) AS INTEGER) AS ano_lancamento,
            CASE WHEN genres = '(no genres listed)' THEN 'sem_genero' ELSE genres END AS generos
        FROM raw.filmes
    """)
    depois_filmes = con.execute("SELECT count(*) FROM refined.filmes").fetchone()[0]
    nulos_ano = con.execute("SELECT count(*) FROM refined.filmes WHERE ano_lancamento IS NULL").fetchone()[0]
    resultados["filmes"] = {
        "antes": antes_filmes,
        "depois": depois_filmes,
        "duplicatas": antes_filmes - depois_filmes,
        "nulos_ano": nulos_ano,
    }

    # 2. refined.avaliacoes
    antes_av = con.execute("SELECT count(*) FROM raw.avaliacoes").fetchone()[0]
    con.execute("""
        CREATE TABLE refined.avaliacoes AS
        SELECT
            CAST(userId AS INTEGER) AS usuario_id,
            CAST(movieId AS INTEGER) AS filme_id,
            CAST(rating AS DOUBLE) AS nota,
            to_timestamp(CAST(timestamp AS BIGINT))::TIMESTAMP AS data_avaliacao
        FROM raw.avaliacoes
    """)
    depois_av = con.execute("SELECT count(*) FROM refined.avaliacoes").fetchone()[0]
    resultados["avaliacoes"] = {
        "antes": antes_av,
        "depois": depois_av,
        "duplicatas": antes_av - depois_av,
    }

    # 3. refined.tags
    antes_tags = con.execute("SELECT count(*) FROM raw.tags").fetchone()[0]
    con.execute("""
        CREATE TABLE refined.tags AS
        SELECT
            CAST(userId AS INTEGER) AS usuario_id,
            CAST(movieId AS INTEGER) AS filme_id,
            lower(trim(tag)) AS tag,
            to_timestamp(CAST(timestamp AS BIGINT))::TIMESTAMP AS data_tag
        FROM raw.tags
    """)
    depois_tags = con.execute("SELECT count(*) FROM refined.tags").fetchone()[0]
    resultados["tags"] = {
        "antes": antes_tags,
        "depois": depois_tags,
        "duplicatas": antes_tags - depois_tags,
    }

    con.close()
    return resultados


def main() -> None:
    res = transformar()
    total_linhas = sum(d["depois"] for d in res.values())

    for tabela, d in res.items():
        antes = f"{d['antes']:,}".replace(",", ".")
        depois = f"{d['depois']:,}".replace(",", ".")
        dups = d["duplicatas"]
        print(f"✓ refined.{tabela:<13} {antes:>7} -> {depois:>7} linhas ({dups} duplicatas)")
        if "nulos_ano" in d and d["nulos_ano"] > 0:
            print(f"    nulos mantidos: ano_lancamento {d['nulos_ano']}")

    total_fmt = f"{total_linhas:,}".replace(",", ".")
    print(f"  total           {total_fmt:>17} linhas")


if __name__ == "__main__":
    main()
