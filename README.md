# Pipeline Cinema · MovieLens

Pipeline de dados analítico construído sobre o dataset público **MovieLens (ml-latest-small)** da Universidade de Minnesota (GroupLens Research).

Projeto final da formação de Engenharia de Dados Júnior.

## Arquitetura do Pipeline

O pipeline segue arquitetura em três camadas desacopladas com DuckDB e Python:
- **`raw`**: Camada bruta, espelhando os arquivos CSV de origem sem modificação.
- **`refined`**: Camada tratada e tipada, aplicando deduplicação, tratamento de tipos e datas, e integridade referencial.
- **`marts`**: Indicadores analíticos consolidados via SQL puro, respondendo perguntas de negócio com grão declarado.

## Stack
- Python 3.13
- uv (gerenciador de ambiente e dependências)
- DuckDB (`cinema.duckdb`)
- pytest & pytest-cov (testes unitários com dados sintéticos e cobertura $\ge$ 60%)

