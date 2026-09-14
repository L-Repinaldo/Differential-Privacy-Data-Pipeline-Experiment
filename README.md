# Diferential-Privacy-Data-Pipeline

Camada de preparação, aplicação de Privacidade Diferencial e versionamento para o experimento com microdados do [ENEM 2025](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem)

## Objetivo do Projeto

Este repositório implementa a etapa de Privacidade Diferencial do experimento. Sua responsabilidade é receber os microdados tabulares do ENEM, selecionar e preparar as variáveis configuradas, aplicar mecanismos de privacidade configuráveis e produzir versões versionadas dos datasets para consumo pelo pipeline experimental de Machine Learning e testes de Membership Inference Attack.

Em particular, o projeto permite comparar o impacto de diferentes valores de ε sobre a utilidade dos dados, preservando o dataset base e os parâmetros empregados em cada execução.

## Arquitetura Geral

Principais componentes (módulos):

- `run_pipeline.py` — orquestra a execução: carrega `config/enem.yaml`, faz o perfil dos dados, cria a versão e grava o baseline e as versões privadas.
- `src/data_exraction.py` — lê o CSV de origem incrementalmente com Pandas. O tamanho dos chunks é configurável e, se omitido, é `100_000` linhas.
- `src/transform_dataframe.py` — seleciona e valida as colunas de saída. A saída reúne as colunas nominais, ordinais, numéricas e a coluna-alvo; as demais, incluindo as listadas em `drop_columns`, não são carregadas para o resultado.
- `src/encoding.py` — codifica temporariamente os atributos categóricos sensíveis para valores numéricos, valida os mapeamentos e decodifica os valores privatizados para a categoria mais próxima antes da gravação.
- `src/diferential_privacy.py` — valida a configuração, calcula limites globais dos atributos sensíveis e aplica ruído Laplace com NumPy, limitado aos valores mínimo e máximo observados.
- `src/versioning.py` — cria `datasets/{nome_do_dataset} - v-YYYY-MM-DD_HH-MM-SS/` e grava os parquets incrementalmente, com um único cabeçalho por arquivo.
- `config/enem.yaml` — arquivo de configuração principal: fonte ENEM, seleção de colunas, mapeamentos de codificação e parâmetros de privacidade.

Cada módulo tem responsabilidade bem definida e o fluxo é implementado por `run_pipeline.py`.

## Papel na Arquitetura do Experimento

- Microdados ENEM 2025: fonte tabular de participantes, configurada como `config/Data/PARTICIPANTES_2025.csv`.
- DP Data Pipeline (este repositório): lê os dados em chunks, prepara as variáveis, aplica Privacidade Diferencial e versiona os resultados.
- Pipeline Experimental de Machine Learning: consome o baseline e as versões privatizadas para treinar modelos e executar avaliações, incluindo ataques de Membership Inference.

Este repositório corresponde estritamente à etapa de preparação e privatização; não realiza treino ou avaliação de modelos.

## Fluxo Completo dos Dados

```text
config/Data/PARTICIPANTES_2025.csv
   ↓
src/data_exraction.py (leitura incremental em chunks)
   ↓
src/transform_dataframe.py (seleção e validação das colunas)
   ↓
1ª passagem: src/encoding.py + src/diferential_privacy.py
            (codificação e cálculo dos limites globais)
   ↓
2ª passagem: baseline.csv + codificação → ruído Laplace → decodificação
   ↓
src/versioning.py (gravação incremental e metadata.json)
   ↓
datasets/enem_2025 - v-YYYY-MM-DD_HH-MM-SS/
```

O uso de duas passagens evita materializar o arquivo inteiro em memória e garante que os limites usados pelo mecanismo sejam globais, e não apenas do chunk em processamento.

## Formato de Entrada e Saída

- Entrada: CSV configurado em `source.file`, atualmente `config/Data/PARTICIPANTES_2025.csv`, separado por `;` e lido com codificação `latin-1`.
- Transformação: o arquivo `config/enem.yaml` define as colunas nominais, ordinais, numéricas e o alvo `Q005`. As colunas de identificação e localização listadas em `drop_columns` são excluídas da saída.
- Saída: em cada execução é criado um diretório `datasets/enem_2025 - v-YYYY-MM-DD_HH-MM-SS/` com:
  - `baseline.parquet` — dataset selecionado, sem ruído;
  - `dp_eps_{epsilon}.parquet` — uma versão por cada ε configurado (atualmente `0.05`, `0.1`, `0.5`, `1.0` , `2.0` e `3.0`);
  - `metadata.json` — metadados por ε, com dataset, mecanismo, seed, quantidade de linhas e colunas, epsilons e limites/sensitivities dos atributos privatizados.

O dataset de saída atual possui 33 colunas: cinco nominais (`TP_SEXO`, `TP_COR_RACA`, `TP_NACIONALIDADE`, `SG_UF_PROVA`, `Q023`), 27 ordinais e o alvo `Q005`.

## Detalhes de Privacidade

- Mecanismo: Laplace, implementado diretamente com `numpy.random.RandomState.laplace`.
- Atributos sensíveis: definidos em `privacy.sensitive_attributes` de `config/enem.yaml`. Atualmente: `TP_FAIXA_ETARIA`, `TP_ANO_CONCLUIU`, `Q001`–`Q004`, `Q007`–`Q013`, `Q018`, `Q021` e `Q022`.
- Codificação: os atributos sensíveis que possuem mapeamento em `encoding` são convertidos para códigos numéricos antes da perturbação. Após o ruído, cada código é convertido de volta à categoria válida mais próxima. A versão privada mantém, portanto, o formato categórico dessas colunas.
- Sensibilidade: para cada atributo, o pipeline calcula `max - min` sobre todos os chunks da fonte. O ruído usa escala `sensitivity / epsilon` e o resultado é limitado ao intervalo observado.
- Reprodutibilidade: uma instância pseudoaleatória é inicializada com `privacy.seed` para cada ε. Com a mesma fonte, configuração, ordem de leitura e seed, as versões geradas são reproduzíveis. A seed e os limites calculados são registrados em `metadata.json`.

## Execução

1. Instale as dependências em um ambiente virtual:

```bash
python -m pip install -r requiremnts.txt
```

2. Disponibilize o CSV dos participantes no caminho configurado em `config/enem.yaml` ou altere `source.file`, `separator` e `encoding` para sua fonte.

3. Ajuste `config/enem.yaml` conforme necessário: nome do dataset, colunas de saída, mapeamentos de categorias, atributos sensíveis, epsilons, seed e, opcionalmente, `source.chunk_size`.

4. Execute o pipeline:

```bash
python run_pipeline.py
```

Ao final, o comando informa o diretório criado em `datasets/`. Ele conterá o `baseline.parquet`, os `dp_eps_*.parquet` e o `metadata.json` da execução.

## Observações e Boas Práticas

- O pipeline foi pensado para arquivos grandes: a leitura e a escrita são feitas em chunks, mas cada execução realiza duas leituras completas da fonte.
- Mapeamentos presentes em `encoding` devem incluir todos os valores não nulos encontrados na respectiva coluna; valores desconhecidos interrompem a execução para evitar uma codificação silenciosamente incorreta.
- O baseline preserva os valores selecionados após a leitura. A codificação é aplicada somente à visão que será privatizada, e as categorias sensíveis são restauradas antes da persistência.
- Este repositório implementa mecanismos experimentais para pesquisa. A aplicação direta desses datasets em produção exige revisão de contabilidade de privacidade (incluindo composição de ε), justificativa formal das sensitivities e auditoria.
- O pipeline atual aplica ruído por registro aos atributos sensíveis. Dependendo do objetivo da liberação, recomenda-se reavaliar a estratégia de sensitivities e o formato da divulgação, por exemplo estatísticas agregadas ou dados sintéticos.

## Estrutura do Repositório

- `run_pipeline.py` — orquestrador de execução;
- `config/enem.yaml` — configuração do experimento ENEM;
- `config/Data/PARTICIPANTES_2025.csv` — arquivo de entrada configurado;
- `src/data_exraction.py` — leitura incremental da fonte CSV;
- `src/transform_dataframe.py` — seleção e validação das colunas;
- `src/encoding.py` — codificação e decodificação reversível de categorias sensíveis;
- `src/diferential_privacy.py` — cálculo de limites e aplicação do mecanismo Laplace;
- `src/versioning.py` — persistência e versionamento dos datasets;
- `datasets/` — versões geradas por execução;
- `requiremnts.txt` — dependências do projeto.

## Licença

Uso acadêmico e educacional.
