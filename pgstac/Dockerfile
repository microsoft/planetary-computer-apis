FROM postgres:14 as pg


ENV POSTGIS_MAJOR 3
ENV PGUSER postgres
ENV PGDATABASE postgres
ENV PGHOST localhost

RUN \
    apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-$PG_MAJOR-pgtap \
        postgresql-$PG_MAJOR-partman \
        postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR \
        postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR-scripts \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 5432

RUN mkdir -p /docker-entrypoint-initdb.d
