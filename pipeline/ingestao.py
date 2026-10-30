"""pipeline/ingestao.py — Download e ingestão dos dados brutos do MovieLens para raw.

SPEC
1. ESCOPO
   Baixa o dataset oficial MovieLens (ml-latest-small) da Universidade de Minnesota
   caso os arquivos ainda não existam em raw/.
   Carrega as tabelas no schema raw do DuckDB (cinema.duckdb).
   Todas as colunas entram como VARCHAR (all_varchar=true) para preservar
   o dado bruto fielmente sem perdas ou conversões prematuras.

2. TABELAS CRIADAS EM RAW
   - raw.filmes: a partir de raw/movies.csv (movieId, title, genres)
   - raw.avaliacoes: a partir de raw/ratings.csv (userId, movieId, rating, timestamp)
   - raw.tags: a partir de raw/tags.csv (userId, movieId, tag, timestamp)

3. SAÍDA NO TERMINAL
   Uma linha por tabela com a contagem de linhas (milhar com ponto):
     ✓ raw.filmes          9.742 linhas
     ✓ raw.avaliacoes    100.836 linhas
     ✓ raw.tags            3.683 linhas
       total             114.261 linhas
   stdout configurado em UTF-8.

4. IDEMPOTÊNCIA E TRATAMENTO DE ERRO
   Se o download ou extração falhar, exibe mensagem clara e encerra com sys.exit(1).
   Rodar duas vezes seguidas produz exatamente o mesmo resultado.
"""

from io import BytesIO
from pathlib import Path
import ssl
import sys
import urllib.request
import zipfile

from pipeline.db import conectar, criar_schema

# Reconfigura stdout para utf-8 em terminais Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

URL_MOVIELENS = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
PASTA_RAW = Path("raw")

ARQUIVOS_TABELAS = {
    "filmes": "movies.csv",
    "avaliacoes": "ratings.csv",
    "tags": "tags.csv",
}


def garantir_dados_brutos(pasta_destino: Path = PASTA_RAW) -> None:
    """Baixa e extrai os arquivos CSV na pasta de destino se não existirem."""
    pasta_destino.mkdir(parents=True, exist_ok=True)
    todos_existem = all((pasta_destino / nome_csv).is_file() for nome_csv in ARQUIVOS_TABELAS.values())
    if todos_existem:
        return

    try:
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(URL_MOVIELENS, headers={"User-Agent": "Mozilla/5.0 (PipelineCinema)"})
        with urllib.request.urlopen(req, context=ctx) as resposta:
            conteudo_zip = resposta.read()

        with zipfile.ZipFile(BytesIO(conteudo_zip)) as z:
            for membro in z.namelist():
                nome_base = Path(membro).name
                if nome_base in ARQUIVOS_TABELAS.values():
                    dados = z.read(membro)
                    (pasta_destino / nome_base).write_bytes(dados)
    except Exception as e:
        sys.stderr.write(f"Erro ao baixar ou extrair dados do MovieLens: {e}\n")
        sys.exit(1)


def ingerir(caminho_banco: str = "cinema.duckdb", pasta_dados: Path = PASTA_RAW) -> dict[str, int]:
    """Lê os CSVs de raw e grava as tabelas no schema raw do DuckDB com tipagem bruta VARCHAR."""
    garantir_dados_brutos(pasta_dados)

    con = conectar(caminho_banco)
    criar_schema(con, "raw")

    contagens = {}
    for tabela, arquivo_csv in ARQUIVOS_TABELAS.items():
        caminho_csv = (pasta_dados / arquivo_csv).as_posix()
        if not Path(caminho_csv).is_file():
            sys.stderr.write(f"Arquivo ausente: {caminho_csv}\n")
            con.close()
            sys.exit(1)

        # Ingestão forçando colunas como VARCHAR para garantir dado original intacto
        query = f"""
            CREATE OR REPLACE TABLE raw.{tabela} AS
            SELECT * FROM read_csv('{caminho_csv}', all_varchar=true, header=true)
        """
        con.execute(query)
        total = con.execute(f"SELECT count(*) FROM raw.{tabela}").fetchone()[0]
        contagens[tabela] = int(total)

    con.close()
    return contagens


def main() -> None:
    contagens = ingerir()
    total_linhas = sum(contagens.values())

    for tabela, total in contagens.items():
        total_formatado = f"{total:,}".replace(",", ".")
        print(f"✓ raw.{tabela:<15} {total_formatado:>9} linhas")

    total_geral_formatado = f"{total_linhas:,}".replace(",", ".")
    print(f"  total           {total_geral_formatado:>11} linhas")


if __name__ == "__main__":
    main()
