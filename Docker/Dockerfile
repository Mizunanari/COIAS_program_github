FROM ubuntu:20.04

LABEL author="Haruki Anbai" 

SHELL ["/bin/bash", "-c"]

ENV TZ=Asia/Tokyo\
    DEBIAN_FRONTEND=noninteractive

#optを作業ディレクトリとする
WORKDIR /opt

#必要なパッケージをubuntuにインストール
RUN apt update && apt install -y\
    git\
    wget\
    build-essential\
    libncurses-dev\
    unzip\
    source-extractor\
    && rm -rf /var/lib/apt/lists/*

#miniconda3をインストール
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    chmod 700 ./Miniconda3-latest-Linux-x86_64.sh && \
    bash ./Miniconda3-latest-Linux-x86_64.sh -b && \
    ~/miniconda3/bin/conda init bash && \
    rm ./Miniconda3-latest-Linux-x86_64.sh

#miniconda3のPATHを通す
ENV PATH $PATH:/root/miniconda3/bin

#クローンをして、COIASのための環境構築
RUN git clone https://github.com/coias/coias-back-app.git --depth 1

# condaのcoias-back-app環境下で、ビルド
WORKDIR /opt/coias-back-app
RUN conda env create -n coias -f ./env/ubuntu_env.yml
RUN conda config --set auto_activate_base false

# conda activate coiasと同じ
SHELL ["conda", "run", "-n", "coias", "/bin/bash", "-c"]

# Cythonのビルド
RUN chmod -R 700 ./*
WORKDIR /opt/coias-back-app/src5_astsearch_new
RUN /root/miniconda3/envs/coias/bin/python setup12.py build_ext --inplace

# C++のビルド
WORKDIR /opt/coias-back-app/findOrb
RUN make -f linlunar.mak && \
    make -f linmake

# coias-back-appとfindOrbのPATHを通す
ENV PATH $PATH:/opt/coias-back-app
ENV PATH $PATH:/opt/coias-back-app/findOrb
ENV PATH $PATH:/opt/coias-back-app/COIASlibs
ENV PATH $PATH:/opt/coias-back-app/src1_preprocess
ENV PATH $PATH:/opt/coias-back-app/src2_startsearch2R
ENV PATH $PATH:/opt/coias-back-app/src3_prempsearchC-before
ENV PATH $PATH:/opt/coias-back-app/src4_prempsearchC-after
ENV PATH $PATH:/opt/coias-back-app/src5_astsearch_new
ENV PATH $PATH:/opt/coias-back-app/src6_between_COIAS_and_ReCOIAS
ENV PATH $PATH:/opt/coias-back-app/src7_AstsearchR_afterReCOIAS
ENV PATH $PATH:/opt/coias-back-app/src8_astsearch_manual
ENV PYTHONPATH $PYTHONPATH:/opt/coias-back-app/COIASlibs

# API server を開始
WORKDIR /opt/coias-back-app
ENTRYPOINT [ "bash", "/opt/coias-back-app/script/startup.sh" ]