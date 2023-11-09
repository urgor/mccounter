FROM python:3
COPY mccounter.py /

RUN pip install --no-cache-dir mcpi-e prometheus-client

ENTRYPOINT ["python3", "mccounter.py"]