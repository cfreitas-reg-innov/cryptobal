# set base image (host OS)
FROM python:3.8

# set the working directory in the container
WORKDIR /api_consumer

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip3 install -r requirements.txt
RUN apt-get update
RUN apt-get install dumb-init

# copy the content of the local src directory to the working directory
COPY ./api_consumer .

# runs storeData file without arguments
ENTRYPOINT ["dumb-init","python3", "storeData.py"]