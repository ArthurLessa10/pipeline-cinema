"""pipeline/marts.py — Execução dos marts analíticos em DuckDB.

SPEC
1. ESCOPO
   Lê do schema refined e escreve no schema marts.
   Nunca escreve em raw nem em refined.
   O schema marts é recriado a cada execução (DROP SCHEMA IF EXISTS marts CASCADE).

2. UM ARQUIVO, UMA TABELA
   Lê todos os sql/marts/*.sql em ordem alfabética.
   Nome da tabela = nome do arquivo sem a extensão e sem o prefixo numérico:
     sql/marts/01_top_filmes.sql -> marts.top_filmes
   Executa: CREATE TABLE marts.<nome> AS <conteúdo do arquivo>
   O Python não altera, não monta e não completa a SQL.

3. SAÍDA NA TELA
   Uma linha por mart, com a contagem vinda do banco (milhar com ponto):
     ✓ marts.top_filmes               450 linhas
     ...
     5 marts                        1.093 linhas
   stdout reconfigurado para UTF-8.

4. TRANSAÇÃO E TRATAMENTO DE ERROS
   - Valida se todas as tabelas esperadas em refined existem antes de rodar.
   - Valida formato dos nomes dos arquivos (prefixo numérico NN_).
   - Executa tudo em transação única (BEGIN TRANSACTION / COMMIT / ROLLBACK).
   - Se um mart retornar 0 linhas ou falhar na sintaxe, desfaz tudo e sys.exit(1).
"""

from pathlib import Path
import re
import sys
import duckdb

from pipeline.db import conectar, criar_schema

# Reconfigura stdout para utf-8 em terminais Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PASTA_SQL_MARTS = Path("sql/marts")
TABELAS_REFINED_ESPERADAS = ["filmes", "avaliacoes", "tags"]
PADRAO_ARQUIVO = re.compile(r"^\d{2}_(.+)\.sql$")


def validar_refined(con: duckdb.DuckDBPyConnection) -> None:
    """Garante que as tabelas necessárias da camada refined existem."""
    tabelas_existentes = [
        row[0]
        for row in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'refined'"
        ).fetchall()
    ]
    faltantes = [t for t in TABELAS_REFINED_ESPERADAS if t not in tabelas_existentes]
    if faltantes:
        sys.stderr.write(
            f"Erro: Tabelas ausentes em refined: {', '.join(faltantes)}\n"
            f"Execute primeiro: uv run python -m pipeline.transformacao\n"
        )
        con.close()
        sys.exit(1)


def validar_arquivos_marts(pasta: Path = PASTA_SQL_MARTS) -> list[tuple[Path, str]]:
    """Valida nomes e unicidade dos arquivos SQL dos marts."""
    arquivos = sorted(pasta.glob("*.sql"))
    if not arquivos:
        sys.stderr.write(f"Erro: Nenhum arquivo .sql encontrado em {pasta}\n")
        sys.exit(1)

    tabelas_vistas = set()
    lista_marts = []

    for arq in arquivos:
        match = PADRAO_ARQUIVO.match(arq.name)
        if not match:
            sys.stderr.write(
                f"Erro: Arquivo '{arq.name}' fora do padrão NN_nome.sql (ex: 01_top_filmes.sql)\n"
            )
            sys.exit(1)

        nome_tabela = match.group(1)
        if nome_tabela in tabelas_vistas:
            sys.stderr.write(f"Erro: Nome de tabela duplicado nos marts: '{nome_tabela}'\n")
            sys.exit(1)

        tabelas_vistas.add(nome_tabela)
        lista_marts.append((arq, nome_tabela))

    return lista_marts


def processar_marts(caminho_banco: str = "cinema.duckdb", pasta_sql: Path = PASTA_SQL_MARTS) -> dict[str, int]:
    """Cria todas as tabelas do schema marts dentro de uma transação segura."""
    marts_para_criar = validar_arquivos_marts(pasta_sql)

    con = conectar(caminho_banco)
    validar_refined(con)

    con.execute("BEGIN TRANSACTION")
    try:
        con.execute("DROP SCHEMA IF EXISTS marts CASCADE")
        criar_schema(con, "marts")

        contagens = {}
        for arq, nome_tabela in marts_para_criar:
            sql_conteudo = arq.read_text(encoding="utf-8").strip().rstrip(";")
            con.execute(f"CREATE TABLE marts.{nome_tabela} AS {sql_conteudo}")

            total = con.execute(f"SELECT count(*) FROM marts.{nome_tabela}").fetchone()[0]
            if total == 0:
                raise ValueError(f"Mart 'marts.{nome_tabela}' retornou 0 linhas.")

            contagens[nome_tabela] = int(total)

        con.execute("COMMIT")
        con.close()
        return contagens
    except Exception as e:
        con.execute("ROLLBACK")
        con.close()
        sys.stderr.write(f"Erro ao processar marts: {e}\n")
        sys.exit(1)


def main() -> None:
    contagens = processar_marts()
    total_linhas = sum(contagens.values())
    qtd_marts = len(contagens)

    for tabela, total in contagens.items():
        total_formatado = f"{total:,}".replace(",", ".")
        unidade = "linha" if total == 1 else "linhas"
        print(f"✓ marts.{tabela:<24} {total_formatado:>6} {unidade}")

    total_geral_fmt = f"{total_linhas:,}".replace(",", ".")
    print(f"  {qtd_marts} marts                      {total_geral_fmt:>7} linhas")


if __name__ == "__main__":
    main()
