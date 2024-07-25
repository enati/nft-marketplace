FROM python:3.10-bullseye 

RUN mkdir app
WORKDIR /app

ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH=.

COPY init.sql poetry.lock pyproject.toml ./
COPY . ./

RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install 

# Add docker-compose-wait tool
ENV WAIT_VERSION 2.7.2
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/$WAIT_VERSION/wait /wait
RUN chmod +x /wait

