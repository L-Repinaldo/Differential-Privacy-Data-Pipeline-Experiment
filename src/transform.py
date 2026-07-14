import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta


class TransformError(Exception):
    pass


def calcula_tempo(date_input):
    today = date.today()
    delta = relativedelta(today, date_input)
    return delta.years


def preparar_funcionarios(df_funcionario: pd.DataFrame) -> pd.DataFrame:
    df = df_funcionario.copy()

    df["idade"] = df["data_nascimento"].apply(calcula_tempo)
    df["tempo_na_empresa"] = df["data_admissao"].apply(calcula_tempo)

    return df[
        [
            "id",
            "id_setor",
            "id_cargo",
            "salario",
            "idade",
            "tempo_na_empresa",
        ]
    ]


def agregar_avaliacoes(df_avaliacoes: pd.DataFrame) -> pd.DataFrame:
    return (
        df_avaliacoes[["id_funcionario", "nota"]]
        .groupby("id_funcionario", as_index=False)
        .agg(nota_media=("nota", "mean"))
    )


def contar_beneficios( df_beneficio_funcionario: pd.DataFrame, df_beneficios: pd.DataFrame) -> pd.DataFrame:

    df = df_beneficio_funcionario.merge(
        df_beneficios[["id"]],
        left_on="id_beneficio",
        right_on="id",
        how="left",
    )

    return (
        df.groupby("id_funcionario", as_index=False)
        .size()
        .rename(columns={"size": "qtd_beneficios"})
    )


def preparar_dimensoes( df_cargos: pd.DataFrame, df_setores: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:

    cargos = df_cargos[["id", "nome"]].rename(columns={"nome": "cargo"})
    setores = df_setores[["id", "nome"]].rename(columns={"nome": "setor"})

    return cargos, setores


def limpar_e_tipar(df: pd.DataFrame) -> pd.DataFrame:
    numeric_fill = {
        "idade": 0,
        "tempo_na_empresa": 0,
        "salario": 0.0,
        "nota_media": 0.0,
        "qtd_beneficios": 0,
    }

    df = df.fillna(numeric_fill)

    df = df.astype(
        {
            "idade": int,
            "tempo_na_empresa": int,
            "salario": float,
            "nota_media": float,
            "qtd_beneficios": int,
            "cargo": "category",
            "setor": "category",
        }
    )

    return df

def transform(dataframes: dict) -> tuple[pd.DataFrame, dict]:
    
    try:
        df_funcionarios = dataframes["funcionarios"]
        df_avaliacoes = dataframes["avaliacoes"]
        df_beneficio_funcionario = dataframes["beneficio_funcionario"]
        df_beneficios = dataframes["beneficios"]
        df_setores = dataframes["setores"]
        df_cargos = dataframes["cargos"]

    except KeyError as e:
        raise TransformError(f"Tabela ausente na extração: {e}")

    funcionarios = preparar_funcionarios(df_funcionarios)
    avaliacoes = agregar_avaliacoes(df_avaliacoes)
    beneficios = contar_beneficios(df_beneficio_funcionario, df_beneficios)
    cargos, setores = preparar_dimensoes(df_cargos, df_setores)

    df = (
        funcionarios
        .merge(avaliacoes, left_on="id", right_on="id_funcionario", how="left")
        .merge(beneficios, left_on="id", right_on="id_funcionario", how="left")
        .merge(cargos, left_on="id_cargo", right_on="id", how="left")
        .merge(setores, left_on="id_setor", right_on="id", how="left")
    )

    df = df.drop(
        columns=[
            "id",
            "id_x",
            "id_y",
            "id_funcionario",
            "id_funcionario_x",
            "id_funcionario_y",
            "id_cargo",
            "id_setor",
        ],
        errors="ignore",
    )

    df = limpar_e_tipar(df)

    sensitive_attributes = [
        "idade",
        "salario",
        "nota_media",
        "tempo_na_empresa",
    ]
    
    return df
