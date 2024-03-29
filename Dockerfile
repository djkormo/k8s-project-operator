FROM python:3.7-alpine

RUN apk --no-cache add  gcc musl-dev curl bash
# RUN apk --no-cache add --update expat=2.4.5-r0  libretls=3.3.4-r3  libssl1.1=1.1.1n-r0 libcrypto1.1=1.1.1n-r0  zlib=1.2.12-r0 

RUN pip install --upgrade pip

ADD app /app
RUN addgroup -S worker && adduser -D -h /home/worker -s /bin/bash worker -G worker

USER worker

WORKDIR /home/worker

COPY --chown=worker:worker /app/requirements.txt requirements.txt

RUN pip install --no-cache-dir --user -r requirements.txt


ENV PATH="/home/worker/.local/bin:${PATH}"

COPY --chown=worker:worker /app /home/worker/app

RUN chmod u+x /home/worker/app/operator.bash

LABEL maintainer="Krzysztof Pudlowski <djkormo@gmail.com>" version="1.0.0"

ENTRYPOINT ["/bin/bash", "-c", "/home/worker/app/operator.bash"]



