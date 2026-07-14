 # DP-Data-Pipeline

 Camada de preparação e aplicação de Privacidade Diferencial para o experimento

 ## Objetivo do Projeto

 Este repositório implementa a etapa de Privacidade Diferencial do experimento. Sua responsabilidade é receber dados tabulares sintéticos gerados pelo Sistema de RH, executar limpeza e transformação, aplicar mecanismos de privacidade configuráveis e produzir versões versionadas dos datasets para consumo pelo pipeline experimental de Machine Learning e testes de Membership Inference Attack.

 Em particular, o projeto resolve o problema de produzir datasets privatizados de forma reprodutível e rastreável, permitindo comparar impacto de diferentes valores de ε sobre a utilidade dos dados.

 ## Arquitetura Geral

 Principais componentes (módulos):

 - `src/extract.py` — conecta ao banco PostgreSQL e extrai as tabelas configuradas em `config/pipeline.yaml` como DataFrames Pandas.
 - `src/transform.py` — prepara os dados tabulares: cálculo de `idade` e `tempo_na_empresa`, agregação de avaliações (`nota_media`), contagem de benefícios (`qtd_beneficios`), merges com dimensões (`cargo`, `setor`), preenchimento de NA e tipagem.
 - `src/diferential_privacy.py` — camada de privatização. Implementa aplicação do mecanismo Laplace (via `diffprivlib`) aos atributos sensíveis definidos em configuração. Mantém compatibilidade de formato e registra metadados importantes (mecanismo, atributos, epsilons, seed).
 - `src/versioning.py` — persiste os arquivos gerados por execução em `datasets/v-YYYY-MM-DD_HH-MM-SS/`, incluindo `baseline.csv`, `dp_eps_{epsilon}.csv` e `metadata.json`.
 - `config/pipeline.yaml` — arquivo de configuração principal: fontes de dados, colunas esperadas, atributos sensíveis (bounds), mecanismo e lista de epsilons.

 Cada módulo tem responsabilidade bem definida e o fluxo é implementado por `run_pipeline.py`.

 ## Papel na Arquitetura do Experimento

 - Sistema de RH Sintético: gera os dados originais (fora deste repositório).
 - DP Data Pipeline (este repositório): realiza extração, transformação, aplicação de Privacidade Diferencial e versionamento dos datasets.
 - Pipeline Experimental de Machine Learning: consome os CSVs gerados (baseline e versões privatizadas) para treinar modelos e executar avaliações, incluindo ataques de Membership Inference.

 Este repositório corresponde estritamente à etapa de privatização e não realiza treino ou avaliação de modelos.

 ## Fluxo Completo dos Dados

 ```text
 PostgreSQL
    ↓
 src/extract.py (extração de tabelas como DataFrames)
    ↓
 src/transform.py (limpeza, agregações e tipagem)
    ↓
 src/diferential_privacy.py (aplica mecanismo Laplace por atributo sensível)
    ↓
 src/versioning.py (salva baseline, dp_eps_*.csv e metadata.json)
    ↓
 datasets/ (versões geradas)
 ```

 ## Formato de Entrada e Saída

 - Entrada: tabelas SQL conforme `config/pipeline.yaml` (`funcionarios`, `avaliacoes`, `beneficios`, `beneficio_funcionario`, `setores`, `cargos`). O módulo `extract` retorna um dicionário de DataFrames.
 - Saída: em cada execução é criado um diretório `datasets/v-YYYY-MM-DD_HH-MM-SS/` com:
   - `baseline.csv` — dataset pós-transformação sem ruído;
   - `dp_eps_{epsilon}.csv` — uma versão por cada ε configurado (ex.: `0.1`, `0.5`, `1.0`, `2.0`);
   - `metadata.json` — descreve `mechanism`, `attributes` (min/max/sensitivity), `epsilons` e `seed` usado para reprodutibilidade.

 As colunas do dataset de saída (exemplo): `salario, idade, tempo_na_empresa, nota_media, qtd_beneficios, cargo, setor`.

 ## Detalhes de Privacidade

 - Mecanismo: Laplace (implementado com `diffprivlib`).
 - Atributos sensíveis: definidos em `config/pipeline.yaml` com bounds (min/max) — atualmente `salario`, `nota_media`, `idade`, `tempo_na_empresa`.
 - Sensibilidade: no código atual cada atributo usa `sensitivity = max - min` quando aplicado por-valor; a escolha de sensibilidade e a estratégia (por-valor vs. por-consulta) estão documentadas no código e no `README` para análise crítica.
 - Reprodutibilidade: a seed do mecanismo é lida de `config/pipeline.yaml` (`privacy.mechanism.seed`) ou adotada um valor padrão (42). A seed é registrada em `metadata.json` e passada ao mecanismo para garantir que execuções com a mesma configuração gerem os mesmos arquivos privatizados.

 ## Execução

 1. Instale dependências (recomendado em virtualenv):

 ```bash
 python -m pip install -r requirements.txt
 ```

 2. Configure variáveis de ambiente para acesso ao PostgreSQL (ou use uma cópia local dos dados para desenvolvimento). O `extract` usa `python-dotenv` para carregar variáveis se um arquivo `.env` estiver presente.

 3. Ajuste `config/pipeline.yaml` conforme necessário (tabelas, bounds, epsilons, seed).

 4. Execute o pipeline:

 ```bash
 python run_pipeline.py
 ```

 Ao final, um diretório em `datasets/` conterá o `baseline.csv`, os `dp_eps_*.csv` e o `metadata.json` com os parâmetros e a seed utilizada.

 ## Observações e Boas Práticas

 - Este repositório implementa mecanismos experimentais para pesquisa. A aplicação direta desses datasets em produção exige revisão de contabilidade de privacidade (composição de ε), justificativa formal de sensitivities e auditoria.
 - Para reproduzir resultados exatos, mantenha `config/pipeline.yaml` e as variáveis de ambiente inalteradas entre execuções (a seed garante reprodutibilidade do ruído).
 - O pipeline atual aplica ruído por registro a atributos sensíveis. Dependendo do objetivo (liberar estatísticas agregadas versus datasets por registro) recomenda-se reavaliar a estratégia de sensibilidades e a forma de liberação (agregados, sintetizadores, shift controlado, etc.).

 ## Estrutura do Repositório

 - `run_pipeline.py` — orquestrador de execução;
 - `config/pipeline.yaml` — configuração principal do pipeline;
 - `src/extract.py` — extração de dados do banco;
 - `src/transform.py` — transformação e limpeza;
 - `src/diferential_privacy.py` — aplicação do mecanismo Laplace e geração de datasets DP;
 - `src/versioning.py` — persistência/versionamento dos datasets;
 - `datasets/` — saída gerada por execução (versões historicamente armazenadas);
 - `requirements.txt` — dependências do projeto.

 ## Licença

 Uso acadêmico e educacional.

