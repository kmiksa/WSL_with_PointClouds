from pympler import asizeof
import math

from google.cloud import bigquery

def check_bigquery(run,project,trip,video,version,bq_client):

    query = """
        SELECT DISTINCT project,trip,video,version 
        FROM `continual-grin-207218.TFexperiments.detections` 
        WHERE run = @run
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("run", "STRING", run)
        ]
    )
    query_job = bq_client.query(query, job_config=job_config)
    df = query_job.to_dataframe()

    for index,row in df.iterrows():
        if not row['project'] == project:
            continue
        if not row['trip'] == trip:
            continue
        if not row['video'] == video:
            continue
        if not row['version'] == version:
            continue
        return True

    return False 

def querry_frames(dets,bq_client):
    '''
    query frames given list of images.
    '''
    query = """
        SELECT * 
        FROM `continual-grin-207218.TFexperiments.detections` 
        WHERE run = @run AND version = @version AND project = @project AND
            trip = @trip AND image IN UNNEST(@images)
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("run", "STRING", dets['run']), 
            bigquery.ScalarQueryParameter("version", "STRING", dets['version']),
            bigquery.ScalarQueryParameter("project", "STRING", dets['project']),
            bigquery.ScalarQueryParameter("trip", "STRING", dets['trip']),
            bigquery.ArrayQueryParameter("image", "STRING", dets['images'])
        ]
    )
    query_job = bq_client.query(query, job_config=job_config)
    detections = query_job.to_dataframe()
    return detections


def querry_video(dets,bq_client):
    '''
    query frames given list of images.
    '''
    query = """
        SELECT * 
        FROM `continual-grin-207218.TFexperiments.detections` 
        WHERE run = @run AND version = @version AND project = @project AND
            trip = @trip AND video = @video
        ORDER BY frame
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("run", "STRING", dets['run']), 
            bigquery.ScalarQueryParameter("version", "STRING", dets['version']),
            bigquery.ScalarQueryParameter("project", "STRING", dets['project']),
            bigquery.ScalarQueryParameter("trip", "STRING", dets['trip']),
            bigquery.ScalarQueryParameter("video", "STRING", dets['video'])
        ]
    )
    query_job = bq_client.query(query, job_config=job_config)
    detections = query_job.to_dataframe()
    return detections


def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

def generate_row(table, item):
    row = []
    for field in table.schema:
        row.append(item.get(field.name))
    return row

def push_to_bigquery(rows_to_insert,bq_client,table):
    if len(rows_to_insert) > 0:
        print('len detections table: ', len(rows_to_insert))
        size_rows_dict = asizeof.asizeof(rows_to_insert)
        batchsize=50
        for i in range(0, len(rows_to_insert), batchsize):
            objs2 = rows_to_insert[i:i+batchsize]
            size_rows_dict_batched = asizeof.asizeof(objs2)
            errors = bq_client.insert_rows(table, map(lambda x: generate_row(table, x), objs2))
    print('Added to bigquery')