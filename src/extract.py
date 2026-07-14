import psycopg2
import os
from dotenv import load_dotenv
import yaml
import pandas as pd

load_dotenv()

def data_extraction ():

    try:
        config = yaml.safe_load(open("config/pipeline.yaml"))

        db_cfg = config["source"]["database"]

        conn = psycopg2.connect(
            host = os.getenv(db_cfg["host"]),
            port = os.getenv(db_cfg["port"]),
            user = os.getenv(db_cfg["user_env"]),
            password = os.getenv(db_cfg["password_env"])
        )

        queries = {
            "funcionarios": "SELECT * FROM funcionarios;",
            "avaliacoes": "SELECT * FROM avaliacoes;",
            "beneficio_funcionario": "SELECT * FROM beneficio_funcionario;",
            "beneficios": "SELECT * FROM beneficios;",
            "setores": "SELECT * FROM setores;",
            "cargos": "SELECT * FROM cargos;"
        }

        dataframes = {}

        for name, query in queries.items():
            dataframes[name] = pd.read_sql(query, conn)

        conn.close()

        return dataframes


    
    except psycopg2.DatabaseError as error:

        print("Unable to connect to the Database")

        print("XXXXXXXXXXXXXXXXX")

        print(error)

        return None