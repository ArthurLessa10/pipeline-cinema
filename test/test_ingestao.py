"""Testes unitários para pipeline/ingestao.py."""

import pytest
from pipeline.ingestao import ingerir


def test_ingerir_cria_tabelas_raw_com_contagem_exata(tmp_path):
    pasta_raw = tmp_path / "raw"
    pasta_raw.mkdir()

    # Cria CSVs inventados com contagens controladas (2 filmes, 3 avaliacoes, 1 tag)
    (pasta_raw / "movies.csv").write_text("movieId,title,genres\n1,Toy Story (1995),Animation\n2,Jumanji (1995),Adventure\n", encoding="utf-8")
    (pasta_raw / "ratings.csv").write_text("userId,movieId,rating,timestamp\n1,1,4.0,964982703\n1,2,3.5,964982704\n2,1,5.0,964982705\n", encoding="utf-8")
    (pasta_raw / "tags.csv").write_text("userId,movieId,tag,timestamp\n1,1,funny,1445714994\n", encoding="utf-8")

    banco = str(tmp_path / "teste_ingestao.duckdb")
    contagens = ingerir(caminho_banco=banco, pasta_dados=pasta_raw)

    assert contagens["filmes"] == 2
    assert contagens["avaliacoes"] == 3
    assert contagens["tags"] == 1


def test_ingerir_falha_se_arquivo_faltando(tmp_path):
    pasta_raw = tmp_path / "raw"
    pasta_raw.mkdir()
    # Apenas 1 dos 3 arquivos obrigatórios presente
    (pasta_raw / "movies.csv").write_text("movieId,title,genres\n1,Teste (2020),Drama\n", encoding="utf-8")

    banco = str(tmp_path / "teste_falha.duckdb")
    with pytest.raises(SystemExit):
        ingerir(caminho_banco=banco, pasta_dados=pasta_raw, auto_download=False)
