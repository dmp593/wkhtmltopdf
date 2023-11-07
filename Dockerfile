FROM python:3.12-bookworm AS builder

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt -t /dependencies

FROM python:3.12-bookworm

LABEL maintainer="Daniel Pinto"

ARG UID=1337
ARG GID=1339

ARG DEBIAN_FRONTEND=noninteractive
ARG DEBCONF_NOWARNINGS=yes

# Create the setwin user with a specific UID and GID
RUN addgroup --system --gid ${GID} setwin \
    && adduser --system --uid ${UID} --ingroup setwin --home /home/setwin --shell /bin/bash setwin

# Copy only the installed dependencies from the build stage
COPY --from=builder /dependencies /usr/local/lib/python3.12/site-packages/

# Install wkhtmltopdf and clean up
RUN apt-get update \
    && apt-get install -y wkhtmltopdf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER setwin

WORKDIR /home/setwin

COPY ./app /home/setwin/app

EXPOSE 8080

ENTRYPOINT [ "python" ]

CMD [ "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080" ]
