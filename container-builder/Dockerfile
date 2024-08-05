FROM ubuntu:18.04

RUN apt update && \
	apt install -y python3.8 \
			python3.8-dev \
			python3-pip \
			python3-setuptools \
			python3-wheel \
			zlib1g-dev

RUN python3.8 -m pip install -U pip && \
	python3.8 -m pip install -U setuptools wheel && \
	python3.8 -m pip install -U pyinstaller

RUN mkdir /build /dist

WORKDIR /source
