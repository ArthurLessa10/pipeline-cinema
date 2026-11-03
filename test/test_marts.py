"""Testes unitários para pipeline/marts.py."""

import pytest
import duckdb
from pipeline.marts import validar_arquivos_marts, processar_marts


def test_validar_arquivos_marts_sucesso(tmp_path):
    pasta_marts = tmp_path / "sql" / "marts"
    pasta_marts.mkdir(parents=True)

    (pasta_marts / "01_teste_um.sql").write_text("SELECT 1 AS x", encoding="utf-8")
    (pasta_marts / "02_teste_dois.sql").write_text("SELECT 2 AS y", encoding="utf-8")

    marts = validar_arquivos_marts(pasta_marts)
    assert len(marts) == 2
    assert marts[0][1] == "teste_um"
    assert marts[1][1] == "teste_dois"


def test_validar_arquivos_marts_nome_invalido(tmp_path):
    pasta_marts = tmp_path / "sql" / "marts"
    pasta_marts.mkdir(parents=True)
    # Sem prefixo NN_
    (pasta_marts / "arquivo_sem_prefixo.sql").write_text("SELECT 1", encoding="utf-8")

    with pytest.raises(SystemExit):
        validar_arquivos_marts(pasta_marts)


def test_validar_arquivos_marts_duplicado(tmp_path):
    pasta_marts = tmp_path / "sql" / "marts"
    pasta_marts.mkdir(parents=True)
    # Prefixos diferentes que geram o mesmo nome de tabela
    (pasta_marts / "01_vendas.sql").write_text("SELECT 1", encoding="utf-8")
    (pasta_marts / "02_vendas.sql").write_text("SELECT 2", encoding="utf-8")

    with pytest.raises(SystemExit):
        validar_arquivos_marts(pasta_marts)


def test_processar_marts_execucao_e_rollback_em_erro(tmp_path):
    banco = str(tmp_path / "teste_marts.duckdb")
    con = duckdb.connect(banco)
    con.execute("CREATE SCHEMA refined")
    con.execute("CREATE TABLE refined.filmes (filme_id INT, titulo VARCHAR, ano_lancamento INT, generos VARCHAR)")
    con.execute("CREATE TABLE refined.avaliacoes (usuario_id INT, filme_id INT, nota DOUBLE, data_avaliacao TIMESTAMP)")
    con.execute("CREATE TABLE refined.tags (usuario_id INT, filme_id INT, tag VARCHAR, data_tag TIMESTAMP)")
    con.close()

    pasta_marts = tmp_path / "sql" / "marts"
    pasta_marts.mkdir(parents=True)

    # 1 mart que gera 1 linha
    (pasta_marts / "01_teste.sql").write_text("SELECT 100 AS valor", encoding="utf-8")
    contagens = processar_marts(caminho_banco=banco, pasta_sql=pasta_marts)
    assert contagens["teste"] == 1

    # Adiciona um mart que falha na sintaxe para verificar rollback
    (pasta_marts / "02_erro_sintaxe.sql").write_text("SELECT COM ERRO DE SINTAXE", encoding="utf-8")
    with pytest.raises(SystemExit):
        processar_marts(caminho_banco=banco, pasta_sql=pasta_marts)

    # Verifica se o mart 01 continua existindo após o rollback
    con_check = duckdb.connect(banco, read_only=True)
    total = con_check.execute("SELECT count(*) FROM marts.teste").fetchone()[0]
    assert total == 1
    con_check.close()
