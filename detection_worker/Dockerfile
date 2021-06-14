FROM tensorflow/tensorflow:1.15.2-gpu-jupyter

COPY ./service-key.json /tmp/service-key.json
ENV DEBIAN_FRONTEND=noninteractive 
ENV GOOGLE_APPLICATION_CREDENTIALS=/tmp/service-key.json

RUN apt-get update && apt-get install -y gnupg curl \
    && echo "deb http://packages.cloud.google.com/apt cloud-sdk-xenial main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - \
    && apt-get update && apt-get install -y google-cloud-sdk ssh-client protobuf-compiler python-pil python-lxml python-tk libsm6 libxext6 git\
    && rm -rf /var/lib/apt/lists/* \
    && gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS


COPY . /src
WORKDIR /src


COPY ./install-protobuf.sh /tmp/install-protobuf.sh
RUN pip3 install pip --upgrade \     
    && chmod 700 /tmp/install-protobuf.sh \
    && pip install .

ENTRYPOINT ["/src/bin/entrypoint"]