# syntax=docker/dockerfile:1
FROM python:3.12

RUN useradd -m me
USER me
WORKDIR /home/me

COPY requirements/common.txt common.txt

RUN pip3 --disable-pip-version-check --no-cache-dir install -r common.txt && \
	rm common.txt

ENV PATH="/home/me/.local/bin:${PATH}"

COPY --chown=me wuzzln/ wuzzln/
COPY --chown=me templates/ templates/
COPY --chown=me assets/ assets/

CMD python3 -m litestar --app wuzzln.app:app run --port 8501 --host 0.0.0.0
