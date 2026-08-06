""" loads data from training tables and allows analysis by the AI agent"""

import pandas as pd

from database import database 


def get_training_data(email_id:int| None=None) -> pd.DataFrame:
    """ takes training data from the database and returns a dataframe"""
    conn = database.get_connection()

    if email_id is None:
        data = pd.read_sql("SELECT * FROM TrainingData", conn)
    else:
        data = pd.read_sql("SELECT * FROM TrainingData WHERE id=?",conn ,params=(email_id,))
    data.set_index("id",inplace=True)
    print(data.head(10))

    #remove unlabelled and ambiguous
    print(f"data is currently contains: ({len(data)}) emails.")
    data = data[~data["label"].isin(["unlabelled","ambiguous"])]
    print(f"after filtering to suitable data contains: ({len(data)}) emails.")

    #state health of the sample
    print(data["label"].value_counts())

    return data

get_training_data()
