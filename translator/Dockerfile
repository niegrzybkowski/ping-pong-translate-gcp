FROM docker.io/library/python:3.11

RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --no-cache-dir
RUN pip3 install 'transformers[torch]' sentencepiece --no-cache-dir

WORKDIR /model

RUN wget --no-verbose https://huggingface.co/facebook/nllb-200-distilled-600M/resolve/main/pytorch_model.bin
RUN wget --no-verbose https://huggingface.co/facebook/nllb-200-distilled-600M/raw/main/config.json

WORKDIR /app

COPY . .

ENTRYPOINT [ "python3", "translator.py"]
