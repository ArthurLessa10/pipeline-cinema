"""Testes unitários para pipeline/transformacao.py."""

import pytest
import duckdb
from pipeline.transformacao import transformar, validar_raw


def test_transformacao_tipos_e_extracao_ano(tmp_path):
    banco = str(tmp_path / "teste_transf.duckdb")
    con = duckdb.connect(banco)
    con.execute("CREATE SCHEMA raw")

    # 1 filme com ano, 1 filme sem ano, 1 filme com sem_genero
    con.execute("""
        CREATE TABLE raw.filmes (movieId VARCHAR, title VARCHAR, genres VARCHAR);
        INSERT INTO raw.filmes VALUES
            ('10', 'Matrix, The (1999)', 'Action|Sci-Fi'),
            ('20', 'Filme Sem Ano', '(no genres listed)');
    """)

    # 2 avaliações válidas
    con.execute("""
        CREATE TABLE raw.avaliacoes (userId VARCHAR, movieId VARCHAR, rating VARCHAR, timestamp VARCHAR);
        INSERT INTO raw.avaliacoes VALUES
            ('1', '10', '4.5', '1500000000'),
            ('2', '10', '5.0', '1500000100');
    """)

    # 1 tag com maiúsculas e espaços para testar normalização
    con.execute("""
        CREATE TABLE raw.tags (userId VARCHAR, movieId VARCHAR, tag VARCHAR, timestamp VARCHAR);
        INSERT INTO raw.tags VALUES
            ('1', '10', '  Cyberpunk Clássico  ', '1500000000');
    """)
    con.close()

    res = transformar(caminho_banco=banco)

    assert res["filmes"]["depois"] == 2
    assert res["filmes"]["nulos_ano"] == 1
    assert res["avaliacoes"]["depois"] == 2
    assert res["tags"]["depois"] == 1

    # Validações detalhadas no banco gerado
    con_check = duckdb.connect(banco, read_only=True)
    f1 = con_check.execute("SELECT titulo, ano_lancamento, generos FROM refined.filmes WHERE filme_id = 10").fetchone()
    assert f1 == ("Matrix, The", 1999, "Action|Sci-Fi")

    f2 = con_check.execute("SELECT titulo, ano_lancamento, generos FROM refined.filmes WHERE filme_id = 20").fetchone()
    assert f2 == ("Filme Sem Ano", None, "sem_genero")

    tag_limpa = con_check.execute("SELECT tag FROM refined.tags WHERE filme_id = 10").fetchone()[0]
    assert tag_limpa == "cyberpunk clássico"

    con_check.close()


def test_transformacao_falha_se_faltar_raw(tmp_path):
    banco = str(tmp_path / "teste_vazio.duckdb")
    con = duckdb.connect(banco)
    # Schema raw vazio sem as tabelas obrigatórias
    con.execute("CREATE SCHEMA raw")
    con.close()

    with pytest.raises(SystemExit):
        transformar(caminho_banco=banco)
