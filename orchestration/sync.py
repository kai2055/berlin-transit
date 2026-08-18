

import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from google.cloud import bigquery, storage
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


GCP_PROJECT = os.environ['GCP_PROJECT']          
GCS_BUCKET = os.environ['GCS_BUCKET']            
BQ_DATASET = os.environ['BQ_DATASET']           
BQ_TABLE = os.environ['BQ_TABLE']                
GITHUB_REPO = os.environ['GITHUB_REPO']           

DATA_DIR = 'data'                                
GCS_PREFIX = 'data'                              

# Public repo — no token needed
REPO_URL = f'https://github.com/{GITHUB_REPO}.git'


PUSHGATEWAY_URL = os.environ.get('PUSHGATEWAY_URL')


registry = CollectorRegistry()
m_files = Gauge('sync_files_uploaded', 'New files uploaded this run', registry=registry)
m_rows = Gauge('sync_rows_loaded', 'Rows in BigQuery after load', registry=registry)
m_duration = Gauge(
    'sync_duration_seconds', 'Wall-clock duration of the sync', registry=registry
)
m_success = Gauge(
    'sync_success', '1 if the run succeeded, 0 if it failed', registry=registry
)


BQ_SCHEMA = [
    bigquery.SchemaField('fetched_at', 'STRING'),
    bigquery.SchemaField('station_id', 'STRING'),
    bigquery.SchemaField('station_name', 'STRING'),
    bigquery.SchemaField('response', 'JSON'),
]

# ── STEP 1: Clone the repo into a temp folder ──
# We use --depth 1 to only download the latest commit (fast, small)
# The folder auto-deletes when we're done (with tempfile)
def clone_repo() -> Path:
    tmpdir = tempfile.mkdtemp(prefix='repo_')
    logger.info(f'Cloning {GITHUB_REPO} into {tmpdir}...')
    subprocess.run(
        ['git', 'clone', '--depth', '1', REPO_URL, tmpdir],
        check=True,
        capture_output=True,
        text=True,
    )
    logger.info('Clone complete.')
    return Path(tmpdir)

# ── STEP 2: List all .json files in the repo's data/ folder ──
def list_repo_files(repo_path: Path) -> set:
    data_path = repo_path / DATA_DIR
    if not data_path.exists():
        logger.warning(f'Data dir not found in repo: {data_path}')
        return set()
    files = set()
    for f in data_path.rglob('*.json'):
        rel = f.relative_to(data_path).as_posix()
        files.add(rel)
    logger.info(f'Found {len(files)} JSON files in repo.')
    return files

# ── STEP 3: List all .json files already in GCS ──
def list_gcs_files() -> set:
    client = storage.Client(project=GCP_PROJECT)
    bucket = client.bucket(GCS_BUCKET)
    blobs = bucket.list_blobs(prefix=f'{GCS_PREFIX}/')
    files = set()
    for blob in blobs:
        if blob.name.endswith('.json'):
            rel = blob.name[len(GCS_PREFIX) + 1:]
            files.add(rel)
    logger.info(f'Found {len(files)} JSON files already in GCS.')
    return files

# ── STEP 4: Copy new files from repo → GCS ──
def upload_new_files(repo_path: Path, new_files: set) -> None:
    if not new_files:
        logger.info('No new files to upload.')
        return
    client = storage.Client(project=GCP_PROJECT)
    bucket = client.bucket(GCS_BUCKET)
    for rel_path in new_files:
        local = repo_path / DATA_DIR / rel_path
        blob_name = f'{GCS_PREFIX}/{rel_path}'
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(local))
        logger.info(f'Uploaded: {rel_path} → gs://{GCS_BUCKET}/{blob_name}')
    logger.info(f'Uploaded {len(new_files)} new files.')

# ── STEP 5: Load ALL GCS files into BigQuery ──
# WRITE_TRUNCATE = delete old table, rebuild from scratch (idempotent)
def load_to_bigquery() -> None:
    client = bigquery.Client(project=GCP_PROJECT)
    table_ref = f'{GCP_PROJECT}.{BQ_DATASET}.{BQ_TABLE}'
    gcs_client = storage.Client(project=GCP_PROJECT)
    bucket = gcs_client.bucket(GCS_BUCKET)
    blobs = list(bucket.list_blobs(prefix=f'{GCS_PREFIX}/'))
    uris = [f'gs://{GCS_BUCKET}/{b.name}' for b in blobs if b.name.endswith('.json')]
    if not uris:
        logger.warning('No JSON files in GCS to load.')
        return 0 
    logger.info(f'Loading {len(uris)} files into {table_ref}...')
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        schema=BQ_SCHEMA,
    )
    load_job = client.load_table_from_uri(uris, table_ref, job_config=job_config)
    load_job.result()
    logger.info(f'Load complete. Rows loaded: {load_job.output_rows}')
    return load_job.output_rows 


def push_metrics(files, rows, duration, success):
    """Drop this run's numbers into the mailbox. No-op if no gateway configured."""
    if not PUSHGATEWAY_URL:
        logger.info('PUSHGATEWAY_URL not set — skipping metrics push.')
        return
    m_files.set(files)
    m_rows.set(rows)
    m_duration.set(duration)
    m_success.set(1 if success else 0)
    try:
        # job='transit_sync' is the grouping key — the "name on the mailbox".
        push_to_gateway(PUSHGATEWAY_URL, job='transit_sync', registry=registry)
        logger.info(f'Pushed metrics to {PUSHGATEWAY_URL}')
    except Exception as e:
        logger.error(f'Failed to push metrics: {e}')


def main() -> int:
    start = time.monotonic()
    files_count = 0
    rows_count = 0
    success = False
    try:
        logger.info('=== Transit Sync Starting ===')
        repo_path = clone_repo()
        repo_files = list_repo_files(repo_path)
        gcs_files = list_gcs_files()
        new_files = repo_files - gcs_files
        files_count = len(new_files)
        logger.info(f'New files to sync: {files_count}')
        upload_new_files(repo_path, new_files)
        rows_count = load_to_bigquery()
        logger.info('=== Transit Sync Complete ===')
        success = True
        return 0
    except subprocess.CalledProcessError as e:
        logger.error(f'Git command failed: {e.stderr}')
        return 1
    except Exception as e:
        logger.error(f'Sync failed: {e}', exc_info=True)
        return 1
    finally:
        push_metrics(files_count, rows_count, time.monotonic() - start, success)


if __name__ == '__main__':
    sys.exit(main())