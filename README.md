# Differential Privacy Data Pipeline Experiment

## Visão Geral

Este repositório implementa o pipeline experimental de preparação, aplicação de Privacidade Diferencial e versionamento de microdados tabulares do [ENEM 2025](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados). Ele prepara a fonte de entrada em chunks, remove colunas configuradas, calcula limites globais dos atributos sensíveis e gera um dataset baseline junto de versões perturbadas para diferentes valores de ε (`epsilon`).

O projeto é a etapa de geração de dados do experimento de privacidade. Ele não treina modelos nem executa avaliações de utilidade ou Membership Inference Attack; essas atividades pertencem ao pipeline experimental de Machine Learning que consome os datasets produzidos aqui.

```text
menor ε → maior ruído esperado e maior garantia nominal de privacidade
maior ε → menor ruído esperado e, potencialmente, maior utilidade
```

> **Nota:** este repositório tem finalidade acadêmica e experimental. Os mecanismos, a contabilidade de privacidade e o formato de divulgação devem ser revisados antes de qualquer uso em produção.

---

## Objetivo do Projeto

O pipeline recebe uma fonte CSV configurada, prepara as colunas que permanecerão no experimento, aplica ruído Laplace aos atributos sensíveis e grava cada execução em uma versão independente.

O desenho preserva:

- o dataset baseline, sem ruído;
- uma versão privada para cada ε configurado;
- os limites globais e as sensitivities usados pelo mecanismo;
- a seed e os demais metadados necessários para documentar a execução.

A leitura e a escrita são incrementais, de modo que o arquivo inteiro não precisa ser materializado em memória.

---

## Arquitetura Atual

A arquitetura é composta por um orquestrador, módulos de extração e transformação, uma camada de codificação para atributos sensíveis, o mecanismo de privacidade e a persistência versionada:

```text
Fonte CSV
  → Extração incremental
  → Seleção e validação das colunas
  → Codificação dos atributos sensíveis
  → Perfil global: limites mínimo/máximo
  → Geração do baseline e das versões DP
  → Persistência em Parquet e metadata.json
```

Responsabilidades principais:

- **Orquestração:** `run_pipeline.py` carrega a configuração, executa o profiling em duas passagens, cria a versão e coordena a escrita.
- **Extração:** `src/data_exraction.py` lê CSVs com Pandas em chunks, usando `100_000` linhas por padrão.
- **Transformação:** `src/transform_dataframe.py` valida as colunas configuradas para descarte e seleciona todas as demais.
- **Codificação:** `src/encoding.py` valida e converte mapeamentos categóricos dos atributos sensíveis para códigos numéricos.
- **Privacidade:** `src/diferential_privacy.py` valida a configuração, calcula limites globais e aplica ruído Laplace limitado ao intervalo observado.
- **Versionamento:** `src/versioning.py` grava os chunks em arquivos Parquet com schema consistente e salva os metadados da execução.

---

## Papel na Arquitetura do Experimento

O experimento completo é formado por dois sistemas independentes:

1. **Differential Privacy Data Pipeline Experiment** — este repositório.
   - Lê os microdados do ENEM.
   - Seleciona as colunas do dataset experimental.
   - Codifica os atributos sensíveis quando há mapeamento configurado.
   - Aplica o mecanismo Laplace para os ε definidos.
   - Versiona o baseline e as saídas privadas.

2. **Pipeline Experimental de Machine Learning** — sistema consumidor.
   - Carrega o baseline e os datasets `dp_eps_*.parquet`.
   - Treina modelos de classificação para medir utilidade.
   - Executa avaliações de risco, incluindo Membership Inference Attack.
   - Compara o trade-off entre utilidade e privacidade.

Este repositório corresponde estritamente à preparação, privatização e persistência dos datasets.

---

## Fluxo Experimental

```text
config/Data/PARTICIPANTES_2025.csv
   ↓
src/data_exraction.py
(leitura incremental em chunks)
   ↓
src/transform_dataframe.py
(remoção das colunas configuradas)
   ↓
1ª passagem
src/encoding.py + src/diferential_privacy.py
(codificação e cálculo dos limites globais)
   ↓
2ª passagem
baseline.parquet + ruído Laplace nas colunas sensíveis
   ↓
src/versioning.py
(Parquet incremental + metadata.json)
   ↓
datasets/enem_2025 - v-YYYY-MM-DD_HH-MM-SS/
```

A primeira passagem calcula os limites sobre todos os chunks. A segunda escreve o baseline e aplica o mecanismo privado usando esses limites globais, evitando que a escala do ruído dependa apenas do chunk corrente.

---

## Estrutura do Repositório

```text
.
├── config/
│   ├── enem.yaml
│   └── Data/
│       └── PARTICIPANTES_2025.csv
├── datasets/
├── src/
│   ├── data_exraction.py
│   ├── diferential_privacy.py
│   ├── encoding.py
│   ├── transform_dataframe.py
│   └── versioning.py
├── get_uniques.py
├── requiremnts.txt
├── run_pipeline.py
└── README.md
```

`datasets/` recebe as versões geradas durante a execução e pode não conter saídas em um clone limpo do repositório.

---

## Configuração

A configuração principal está em [`config/enem.yaml`](config/enem.yaml):

```yaml
dataset:
  name: enem_2025

source:
  file: config/Data/PARTICIPANTES_2025.csv
  separator: ";"
  encoding: latin-1

privacy:
  mechanism: laplace
  seed: 42
```

A configuração atual também define as colunas descartadas:

- `NU_INSCRICAO`
- `NU_ANO`
- `CO_MUNICIPIO_PROVA`
- `NO_MUNICIPIO_PROVA`
- `CO_UF_PROVA`

Os atributos sensíveis configurados atualmente são `TP_FAIXA_ETARIA` e `Q001`–`Q004`, `Q007`–`Q022`, com os mapeamentos categóricos correspondentes definidos na seção `privacy.encoding`.

Os valores de ε configurados atualmente são:

```text
0.05, 0.1, 0.5, 1.0, 2.0, 3.0
```

Opcionalmente, `source.chunk_size` pode ser usado para alterar o tamanho dos chunks. Quando omitido, o valor padrão é `100_000`.

---

## Formato de Entrada e Saída

### Entrada

A fonte padrão é o arquivo `config/Data/PARTICIPANTES_2025.csv`, lido como CSV separado por `;` e com codificação `latin-1`. O caminho, separador e encoding podem ser alterados em `config/enem.yaml`.

O pipeline remove as colunas listadas em `drop_columns` e mantém as demais colunas presentes na fonte. A configuração atual não define uma lista explícita de colunas de saída: a seleção é feita por exclusão.

### Saída

Cada execução cria um diretório no formato:

```text
datasets/enem_2025 - v-YYYY-MM-DD_HH-MM-SS/
├── baseline.parquet
├── dp_eps_0.05.parquet
├── dp_eps_0.1.parquet
├── dp_eps_0.5.parquet
├── dp_eps_1.0.parquet
├── dp_eps_2.0.parquet
├── dp_eps_3.0.parquet
└── metadata.json
```

- `baseline.parquet` contém as colunas selecionadas sem ruído.
- `dp_eps_{epsilon}.parquet` contém uma versão para cada ε configurado.
- `metadata.json` registra dataset, mecanismo, seed, quantidade de linhas, quantidade de colunas, εs, limites e sensitivities.

Os arquivos Parquet são escritos incrementalmente. O escritor mantém um único arquivo por saída e rejeita chunks cujo schema seja incompatível com o schema inicial.

---

## Mecanismo de Privacidade

O mecanismo atual é Laplace, implementado diretamente com `numpy.random.RandomState.laplace`.

Para cada atributo sensível:

1. O mapeamento categórico é validado e, quando configurado, os valores são convertidos para códigos numéricos.
2. Na primeira passagem, são calculados o mínimo e o máximo globais.
3. A sensitivity é calculada como `max - min`.
4. Na segunda passagem, o ruído é gerado com escala `sensitivity / epsilon`.
5. O resultado é limitado ao intervalo `[min, max]` observado.

A implementação aplica ruído diretamente aos registros e mantém os valores perturbados numéricos nos arquivos DP. Embora `src/encoding.py` contenha uma função de decodificação para uso auxiliar, o fluxo atual do `run_pipeline.py` não decodifica os atributos antes de persistir os datasets privados.

A seed configurada é usada para inicializar um gerador pseudoaleatório independente para cada ε. A reprodução depende da mesma fonte, configuração, ordem de leitura e seed.

---

## Execução

1. Crie e ative um ambiente virtual, se desejado.

2. Instale as dependências:

```bash
python -m pip install -r requiremnts.txt
```

3. Disponibilize a fonte no caminho configurado ou ajuste `source.file`, `source.separator` e `source.encoding` em `config/enem.yaml`.

4. Revise o nome do dataset, as colunas descartadas, os atributos sensíveis, os mapeamentos, os εs e a seed.

5. Execute:

```bash
python run_pipeline.py
```

Ao final, o comando imprime um resumo com o diretório da versão e os arquivos gerados.

---

## Validações e Boas Práticas

- Todos os valores de ε devem ser positivos.
- O mecanismo suportado atualmente é apenas `laplace`.
- Todos os atributos sensíveis devem existir no dataset preparado.
- Os mapeamentos configurados devem conter todos os valores não nulos encontrados nas respectivas colunas; valores desconhecidos interrompem a execução.
- Os códigos dos mapeamentos devem ser numéricos e reversíveis.
- Os atributos sensíveis devem ser numéricos após a codificação e não podem conter somente valores ausentes.
- A fonte é lida duas vezes: uma para profiling e outra para gravação e aplicação do ruído.
- O baseline é escrito antes da aplicação do ruído e não é alterado pela codificação usada para a visão privada.
- A aplicação do mecanismo a múltiplos atributos e múltiplas versões exige análise de composição de privacidade adequada ao objetivo da divulgação.
- Os datasets gerados podem conter dados sensíveis; controle o armazenamento e o compartilhamento da pasta `datasets/`.

---

## Licença

Uso acadêmico e educacional.
