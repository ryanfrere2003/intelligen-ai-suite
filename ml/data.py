""" interacts with the database to deliver data to svm or distilbert"""

def get_training_data(email_id:int| None=None) -> pd.DataFrame:
    """ takes training data from the database TraininData table and returns a dataframe
    of all emails in the table
        Requires:
            email_id(int): a known email integer.
            email_id(none): all emails in the table.
        Returns:
            A dataframe object containing the query result."""
        
    conn = database.get_connection()

    if email_id is None:
        data = pd.read_sql("SELECT * FROM TrainingData", conn)

        #remove unlabelled and ambiguous
        print(f"data is currently contains: ({len(data)}) emails.")
        data = data[~data["label"].isin(["unlabelled","ambiguous"])]
        print(f"after filtering to suitable data contains: ({len(data)}) emails.")

        #state health of the sample
        print(data["label"].value_counts())

    else:
        data = pd.read_sql("SELECT * FROM TrainingData WHERE id=?",conn ,params=(email_id,))

    data.set_index("id",inplace=True)

    #formats labels and ensures retrained labels are used
    data["training_label"] = data["human_label"].where(data["human_verified"].astype(bool),data["label"])

    return data

#TODO
def get_user_mailbox_data():
    """ takes training data from the database emails table and returns a dataframe
    of all emails in the table"""
    return 