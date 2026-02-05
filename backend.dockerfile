FROM dr2.parswitch.com/devops/python:3-10

WORKDIR /app/
ENV PYTHONPATH=/app

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY ./app/pyproject.toml ./app/poetry.lock /app/
RUN pip install poetry
RUN poetry config virtualenvs.create false
COPY ./app/pyproject.toml ./app/poetry.lock* /app/
RUN poetry install --no-interaction --no-ansi

COPY ./gunicorn_conf.py ./start-server.sh  /
COPY ./app .
CMD [ "/bin/bash", "/start-server.sh" ]
