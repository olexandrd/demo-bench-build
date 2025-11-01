# syntax=docker/dockerfile:1.7

ARG BASE=ubuntu:24.04
FROM ${BASE}

ARG NUMPY_VERSION=2.3.4
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates tzdata locales curl jq procps coreutils \
      python3 python3-pip python3-venv python3-dev \
      stress-ng ffmpeg time util-linux numactl \
    && rm -rf /var/lib/apt/lists/*

ENV VENV_DIR=/opt/py
RUN python3 -m venv "$VENV_DIR" && \
    "$VENV_DIR/bin/pip" install --upgrade pip==24.2 && \
    "$VENV_DIR/bin/pip" install numpy==2.3.4

ENV PATH="$VENV_DIR/bin:${PATH}"

WORKDIR /opt/bench

COPY numpy_tasks.py /opt/bench/numpy_tasks.py

COPY bench.sh /usr/local/bin/bench

RUN chmod +x /usr/local/bin/bench

ENTRYPOINT ["/usr/local/bin/bench"]
CMD ["help"]
