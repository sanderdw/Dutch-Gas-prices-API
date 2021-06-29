FROM ubuntu:bionic
LABEL maintainer="sanderdw@gmail.com"

# Required ystem packages and cleanup
RUN  apt-get update \
    && apt-get install -y curl wget \
	tesseract-ocr \
	libtesseract-dev && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Custom user to so we don't run under root
RUN useradd -ms /bin/bash apiuser

# Getting the latest miniconda installer and make the user owner
ADD https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh /home/apiuser/miniconda.sh
RUN chown apiuser /home/apiuser/miniconda.sh

# Switch to apiuser
USER apiuser
WORKDIR /home/apiuser
RUN mkdir /home/apiuser/.conda
RUN mkdir /home/apiuser/app
RUN mkdir /home/apiuser/app/cache

# Install miniconda
RUN /bin/bash /home/apiuser/miniconda.sh -b -p /home/apiuser/miniconda
ENV PATH=/home/apiuser/miniconda/bin:${PATH}
RUN conda update -y conda

# Install the conda packages
RUN conda config --add channels conda-forge
RUN conda install --yes \
    python=3.7 \
    fastapi=0.43.0 \
    uvicorn=0.9.1 \
    pip

# Install the pip packages
RUN pip install \
    requests \
    requests[socks] \
    requests[security] \
    fake_headers \
    tesseract \
    pytesseract \
    Pillow
    geopy

# Copy the python files to the image
COPY ./app/api.py /home/apiuser/app/api.py
COPY ./app/gas_prices.py /home/apiuser/app/gas_prices.py
COPY ./app/gas_stations.py /home/apiuser/app/gas_stations.py
WORKDIR /home/apiuser/app

# Expose 5035 port for API
EXPOSE 5035

# Run fastapi with the app (api.py)
CMD ["/bin/bash", "-c", "uvicorn --proxy-headers api:app --host=0.0.0.0 --port=5035"]