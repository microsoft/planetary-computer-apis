FROM python:3.8-slim

COPY . /opt/src/

RUN pip install -r /opt/src/requirements.txt

WORKDIR /opt/src

CMD ["alembic", "upgrade", "head"]