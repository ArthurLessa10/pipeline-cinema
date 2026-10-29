"""pipeline/db.py — Conexão e gerenciamento de schemas no DuckDB.

SPEC
1. CONEXÃO
   conectar(caminho="cinema.duckdb", read_only=False) -> duckdb.DuckDBPyConnection.
   Abre conexão com o banco DuckDB especificado.
   Permite modo somente leitura para consultas analíticas e inspeção.

2. ESQUEMAS
   criar_schema(con, nome: str) -> None.
   Cria o schema caso não exista (CREATE SCHEMA IF NOT EXISTS <nome>).
   Garante isolamento entre as camadas raw, refined e marts.

3. TABELAS
   gravar(con, schema: str, tabela: str, sql_select: str) -> int.
   Substitui a tabela pelo resultado do SELECT:
     CREATE OR REPLACE TABLE <schema>.<tabela> AS <sql_select>
   Retorna a contagem exata de linhas gravadas.
"""

from pathlib import Path
import duckdb

BANCO_PADRAO = "cinema.duckdb"
PASTA_RAW = Path("raw")


def conectar(caminho: str = BANCO_PADRAO, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Conecta ao banco DuckDB."""
    return duckdb.connect(caminho, read_only=read_only)


def criar_schema(con: duckdb.DuckDBPyConnection, nome: str) -> None:
    """Cria um schema no banco se ainda não existir."""
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {nome}")


def gravar(con: duckdb.DuckDBPyConnection, schema: str, tabela: str, sql_select: str) -> int:
    """Cria ou substitui a tabela a partir de uma consulta e retorna a contagem de linhas."""
    con.execute(f"CREATE OR REPLACE TABLE {schema}.{tabela} AS {sql_select}")
    res = con.execute(f"SELECT count(*) FROM {schema}.{tabela}").fetchone()
    return int(res[0]) if res else 0
