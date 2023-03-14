from google.cloud import bigquery
import pandas as pd

# UPLOAD DATA TO BQ

PROJECT = "my-project"
DATASET = "taxifare_lecture"
TABLE = "lecture_data"


# Should probably be set in a config file
credentials_path = 'path/to/credentials.json'
project_id = 'your-project-id'

# TODO set up table, dtable knowledge required
table = f"{PROJECT}.{DATASET}.{TABLE}"

# TODO Choose
# create client from service account
client = bigquery.Client.from_service_account_json(credentials_path, project=project_id)
# OR generic?
client = bigquery.Client(project=gcp_project)


def upload_dataframe(df_to_upload : pd.DataFrame, destination_table : str =table, write_mode : str = "WRITE_TRUNCATE"):
    '''Takes a dataframe and uploads it to BigQuery'''
    # upload the dataframe to BigQuery
    if write_mode=="WRITE_TRUNCATE":
        df_to_upload.to_gbq(destination_table, project_id=project_id, if_exists='replace', credentials=client)
    elif write_mode=="WRITE_APPEND":
        df_to_upload.to_gbq(destination_table, project_id=project_id, if_exists='append', credentials=client)


#  TODO Table knowedge required
query = f"""
    SELECT *
    FROM {PROJECT}.{DATASET}.{TABLE}
    """

def query_bq(query):
    '''Takes a query and returns a dataframe'''
    query_job = client.query(query)
    result = query_job.result()
    return result.to_dataframe()
