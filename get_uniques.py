import pandas as pd

df = pd.read_csv(
    "config/Data/PARTICIPANTES_2025.csv",
    sep=";",
    encoding="latin-1",
    usecols=["Q020"],
)

print(df["Q020"].value_counts(dropna=False))