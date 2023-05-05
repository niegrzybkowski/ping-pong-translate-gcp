FROM docker.io/library/python:3.11

WORKDIR /model
RUN wget --no-verbose https://huggingface.co/facebook/nllb-200-distilled-600M/resolve/main/pytorch_model.bin
RUN wget --no-verbose https://huggingface.co/facebook/nllb-200-distilled-600M/raw/main/config.json

WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple --no-cache-dir
RUN apt update
RUN apt install -y gunicorn
COPY . .

#ENTRYPOINT [ "python3" ]
CMD exec gunicorn --preload --bind :$PORT --workers $WORKERS --threads $THREADS --timeout 0 --pythonpath '/app' app:app