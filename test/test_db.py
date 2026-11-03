"""Testes unitários para pipeline/db.py."""

from pipeline.db import conectar, criar_schema, gravar


def test_conectar_e_criar_schema(tmp_path):
    # Banco isolado em pasta temporária
    banco = str(tmp_path / "teste.duckdb")
    con = conectar(banco)

    criar_schema(con, "camada_teste")
    schemas = [r[0] for r in con.execute("SELECT schema_name FROM information_schema.schemata").fetchall()]
    assert "camada_teste" in schemas
    con.close()


def test_gravar_tabela_retorna_contagem(tmp_path):
    banco = str(tmp_path / "teste.duckdb")
    con = conectar(banco)
    criar_schema(con, "camada_teste")

    # Inserindo 3 linhas inventadas
    linhas = gravar(con, "camada_teste", "itens", "SELECT 1 AS id UNION ALL SELECT 2 UNION ALL SELECT 3")
    assert linhas == 3

    # Confere se a tabela existe e tem 3 linhas
    total = con.execute("SELECT count(*) FROM camada_teste.itens").fetchone()[0]
    assert total == 3
    con.close()
