from functools import lru_cache

from pyiceberg.catalog import load_catalog

from app.config import settings


@lru_cache
def get_catalog():
    return load_catalog(
        "atlas",
        **{
            "type": "sql",
            "uri": settings.iceberg_catalog_uri,
            "warehouse": settings.iceberg_warehouse,
            "s3.endpoint": settings.s3_endpoint_url,
            "s3.access-key-id": settings.minio_access_key,
            "s3.secret-access-key": settings.minio_secret_key,
            "s3.path-style-access": "true",
            "s3.region": "us-east-1",
        },
    )
