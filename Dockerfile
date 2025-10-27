# ---------- STAGE 1: build ledger + Python bindings ----------
FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Build deps for ledger + Python bindings
RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates \
    build-essential cmake ninja-build pkg-config \
    python3 python3-dev python3-venv \
    libboost-all-dev libboost-python-dev \
    libgmp-dev libmpfr-dev libedit-dev libutfcpp-dev \
  && apt-get install -y software-properties-common

RUN apt-get install -y build-essential libgpgme-dev libgpgmepp-dev \
  libgpg-error-dev cmake libgmp-dev libmpfr-dev libgpgmepp-dev \
  gettext zlib1g-dev libbz2-dev libedit-dev texinfo lcov sloccount \
  python3-dev doxygen ninja-build libutfcpp-dev libboost-dev \
  libboost-date-time-dev libboost-filesystem-dev libboost-iostreams-dev \
  libboost-regex-dev libboost-system-dev libboost-test-dev tzdata

# Choose the ledger commit/tag; override with --build-arg LEDGER_REF=v3.3.2 (example)
ARG LEDGER_REF=v3.4.1
WORKDIR /src
RUN git clone https://github.com/ledger/ledger.git && \
    cd ledger && \
    git checkout "${LEDGER_REF}" && \
    git submodule update --init --recursive

RUN python3 -m venv /venv && /venv/bin/pip install --upgrade pip

SHELL ["/bin/bash", "-c"]

RUN source /venv/bin/activate && cd ledger && \
  ./acprep --python --prefix /ledger \
  && make -j"$(nproc)" && make install

# ---------- STAGE 2: runtime with venv ----------
FROM ubuntu:24.04 AS runtime

ENV DEBIAN_FRONTEND=noninteractive
# Runtime libs needed by the compiled module + Python
RUN apt-get update && apt-get install -y software-properties-common \
  && apt-get install -y --no-install-recommends \
  python3 python3-venv \
  libgmp10 libmpfr6 libedit2 locales \
  libgpgme11 libgpgmepp6 \
  libgpg-error0 libgmp10 \
  gettext zlib1g libbz2-1.0 \
  python3 libedit2 tzdata \
  curl ca-certificates libboost-all-dev \
  && rm -rf /var/lib/apt/lists/* \
  && locale-gen pt_BR.UTF-8 \
  && update-locale LANG=pt_BR.UTF-8

COPY --from=builder /ledger /ledger
COPY --from=builder /venv /venv

# Copy your app
WORKDIR /app
COPY . /app

RUN /venv/bin/pip install -r requirements.txt

ENV PATH="/venv/bin:${PATH}"

EXPOSE 3000
CMD ["/venv/bin/python", "main.py"]
