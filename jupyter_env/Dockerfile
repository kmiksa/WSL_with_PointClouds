FROM python:3.9.2-slim
ENV PYTHONUNBUFFERED 1
ADD requirements.txt .
RUN pip install -r requirements.txt

ADD overrides.json .
COPY overrides.json /usr/local/share/jupyter/lab/settings/overrides.json

ENV PROJECT_DIR /jupyter-gpu
WORKDIR $PROJECT_DIR