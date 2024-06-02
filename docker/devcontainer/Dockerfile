# https://mcr.microsoft.com/en-us/product/devcontainers/base/about
FROM mcr.microsoft.com/devcontainers/base:dev-ubuntu-22.04

RUN apt-get update && \
    apt-get install -y \
      default-mysql-client bash-completion procps net-tools iputils-ping \
      locales make jq fzf vim \
      curl wget git groff less sudo \
      gcc

# ロケール設定
RUN echo 'ja_JP.UTF-8 UTF-8' >> /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=ja_JP.UTF-8
RUN ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

# aws cli インストール
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install

# pythonのインストール
RUN apt-get update && \
    apt-get install -y python3.10 python3-pip

# Google Chrome インストール
# https://stackoverflow.com/questions/70955307/how-to-install-google-chrome-in-a-docker-container
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb

# Poetry インストール
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/home/vscode/.pypoetry python3 - && \
    chown -R vscode:vscode /home/vscode/.pypoetry
ENV PATH="$PATH:/home/vscode/.pypoetry/bin"

# Pythonのパッケージインストール
#COPY app/job/requirements.txt ./app-job-requirements.txt
#RUN pip install -r app-job-requirements.txt