FROM ubuntu:22.04

LABEL maintainer="Daniel Pinto"

ARG WKHTMLTOPDF_VERSION=0.12.6.1-3
ARG DEBIAN_FRONTEND=noninteractive
ARG DEBCONF_NOWARNINGS=yes

ENV TZ=UTC

RUN ln -snf /usr/share/zoneinfo/UTC /etc/localtime && echo UTC > /etc/timezone

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y curl \
        software-properties-common \
        ca-certificates \
        lsb-release \
        openssl \
        xvfb \
        build-essential \
        libncursesw5-dev \
        libssl-dev \
        libsqlite3-dev \
        tk-dev \
        libgdbm-dev \
        libc6-dev \
        libbz2-dev \
        libffi-dev \
        zlib1g-dev

RUN echo "https://github.com/wkhtmltopdf/packaging/releases/download/${WKHTMLTOPDF_VERSION}/wkhtmltox_${WKHTMLTOPDF_VERSION}.$(lsb_release -sc)_$(dpkg --print-architecture).deb" |  xargs -n 1 curl -O -L

RUN echo "./wkhtmltox_${WKHTMLTOPDF_VERSION}.$(lsb_release -sc)_$(dpkg --print-architecture).deb" | xargs -n 1 apt-get -y install

RUN add-apt-repository -y ppa:deadsnakes/ppa

RUN apt-get update && apt-get install -y python3.11 python3-pip

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN pip3 install --upgrade pip

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip3 install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
