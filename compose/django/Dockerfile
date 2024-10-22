FROM ubuntu:24.04

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app
ARG DEBIAN_FRONTEND=noninteractive
ARG PYTHON_3_10=3.10.14
ARG PYTHON_3_11=3.11.9
ARG PYTHON_3_12=3.12.3

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV COMPOSE_DOCKER_CLI_BUILD 1
ENV DOCKER_BUILDKIT 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}
ENV MULTIPLE_PYTHON=True

WORKDIR ${APP_HOME}

# Install apt packages
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update \
    && apt-get --no-install-recommends install -y \
    # Some basic tools and libraries
    bash curl wget git make \
    build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
    libsqlite3-dev llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev \
    libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev ca-certificates

# Install pyenv
RUN git clone https://github.com/pyenv/pyenv.git .pyenv
ENV PYENV_ROOT ${APP_HOME}/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

# Install Python version(s)
RUN if [ "$MULTIPLE_PYTHON" = "True" ] ; then \
    pyenv install ${PYTHON_3_12}; \
    pyenv install ${PYTHON_3_11}; \
    pyenv install ${PYTHON_3_10}; \
    else \
    pyenv install 3.12; \
    fi

# Initialize pyenv
RUN eval "$(pyenv init -)"

# Add deadsnakes PPA
RUN apt update
RUN apt-get install -y software-properties-common
RUN add-apt-repository 'ppa:deadsnakes/ppa'
RUN apt-get update

# Make Python version(s) accessible in the project and install Python venv
RUN if [ "$MULTIPLE_PYTHON" = "True" ] ; then \
    apt-get install -y python3.12-venv python3.10-venv python3.11-venv; \
    pyenv local ${PYTHON_3_12} ${PYTHON_3_10} ${PYTHON_3_11}; \
    else \
    apt-get install -y python3.12-venv; \
    pyenv local 3.12; \
    fi

# Ensure pip is installed
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get --no-install-recommends install -y \
    python3-pip

# Install uv
RUN pip install --upgrade uv

# Add the venv
RUN uv venv

# Copy requirements files
COPY pyproject.toml uv.lock requirements.txt ${APP_HOME}/

# Install dependencies using uv
RUN uv sync --prerelease=allow --extra dev

# Copy remaining project files
COPY noxfile.py manage.py ${APP_HOME}
COPY .darglint .editorconfig .flake8 .gitignore .pre-commit-config.yaml .prettierignore .readthedocs.yml bandit.yml ${APP_HOME}
COPY CHANGELOG.md CODE_OF_CONDUCT.md CONTRIBUTING.md LICENSE README.md ${APP_HOME}
COPY ./docs/ ${APP_HOME}/docs
COPY ./example_project/ ${APP_HOME}/example_project/
COPY ./src/ ${APP_HOME}/
COPY ./src/ ${APP_HOME}/src/

# Rehash pyenv shims
RUN pyenv rehash

# Project initialization:
COPY ./compose/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

# Initialize git and add .
RUN git init
RUN git add .

ENTRYPOINT ["/entrypoint"]
