FROM python:3.10-slim-bookworm

RUN apt update && \
    apt install -y \
    procps locales curl jq unzip \
    groff less vim fzf net-tools \
    iputils-ping sudo tmux gcc wget

# ロケール設定
RUN echo 'ja_JP.UTF-8 UTF-8' >> /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=ja_JP.UTF-8
RUN ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

# Google Chrome インストール
# https://stackoverflow.com/questions/70955307/how-to-install-google-chrome-in-a-docker-container
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb

# Poetry インストール
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$PATH:/root/.local/bin"

RUN mkdir -p /opt/app
WORKDIR /opt/app

# Pythonのパッケージインストール
COPY app/pyproject.toml /opt/app/pyproject.toml
COPY app/poetry.lock /opt/app/poetry.lock
RUN poetry install --no-root --no-dev

# ソースコードのコピー
COPY app /opt/app

CMD ["/bin/bash"]