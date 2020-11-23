# How to run for Binance
```
python3 storeData.py Binance btcusdt '13 Novembre 2020'
```

# How to run for Kraken
```
python3 storeData.py Kraken XBT/USD '13 Novembre 2020'
python3 storeData.py Kraken "XBT/USD,ETH/USD" '13 Novembre 2020'
```

## Assets for Kraken
- XBT (Bitcoin)
- ETH (Ethereum)
- XTZ (Tezos)

- USD (US Dollars)
- EUR (Euro)

https://support.kraken.com/hc/en-us/articles/360000678446

### Asset Format
- XBT/USD
- XTZ/EUR

# How to run for Coinbase
```
python3 storeData.py Coinbase ETH-USD '13 Novembre 2020'
```

## Assets for Coinbase
- BTC (Bitcoin)
- ETH (Ethereum)
- XTZ (Tezos)

- USD (US Dollars)
- EUR (Euro)

### Asset Format
- BTC-USD
- XTZ-EUR

<br>

# Git Usage
Project URL:
https://github.com/cfreitas-reg-innov/cryptobal.git

Configurate a private SSH key:
https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent

### Basic commands:
```
git clone https://github.com/cfreitas-reg-innov/cryptobal.git
git remote add origin git@github.com:cfreitas-reg-innov/cryptobal.git
git pull origin main
git checkout -b new_branch # to create a new branch, utilize the "-b" parameter
git add -A
git commit -a -m 'message' # it is important to include a message about what was changed in the commit
git push --set-upstream origin new_branch

git checkout main # switches back to the main branch
git stash save --keep-index --include-untracked # switch branch discarding changes

git push -d origin <branch_name> # deletes remote branch after Pull Request
git branch -d <branch_name> # deletes local branch after Pull Request

git status # to check the status of the commits and the branch

git config --global core.editor "nano" # this is the text editor that I prefer
git config --global user.name "Your Name" # change "Your Name" for your name
git config --global user.email "email@example.com" # change the email for your email
```

### Important to notice:
- **.gitignore**: In this file it is set which other files will not be included in the commit, therefore, they will not be included pushed to the repository.
It makes sense not to include system configuration files and data files.

### Proposal
1. Clone the actual repository from the main branch
2. Create a new branch for what you are about to develop
3. Push this branch to the repository
4. Propose a Pull Request from the branch to the main branch

<br>

# AWS_keys.json
This is the expected file structure for the document holding the AWS keys. This must be under "cryptobal/api_consumer/"

```
{
    "access_key": "XXXXXXXXXXXXXXXXXXXX",
    "secret_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
}
```

<br>

# Docker
Below the main commands used in docker to run the applications:

Create a Dockerfile with the following structure:
```
# set base image (host OS)
FROM python:3.8

# set the working directory in the container
WORKDIR /api_consumer

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip3 install -r requirements.txt

# copy the content of the local api_consumer directory to the working directory
COPY ./api_consumer .

# runs storeData file without arguments
ENTRYPOINT ["python3", "./storeData.py"]

```

Once the file is created, the following commands will be used:
```
# create a new image from the Dockerfile
docker build -t <image name> .

# create a new container for each exchange:
docker run -it -d --rm --name container_kraken -p 5001:5000 api_image "Kraken" "XBT/USD" "22 Novembre 2020" && 
docker run -it -d --rm --name container_coinbase -p 5002:5000 api_image "Coinbase" "ETH-USD" "22 Novembre 2020" && 
docker run -it -d --rm --name container_binance -p 5003:5000 api_image "Binance" "btcusdt" "22 Novembre 2020"

# start a previously created container
docker container start container_kraken

# execute bash inside the container
docker exec -it container_kraken /bin/bash

# get log from the container
docker container logs --follow container_kraken

# lists all images
docker images

# lists all containers
docker ps -a

# stops all containers
docker stop container_kraken container_binance container_coinbase

# remove container
docker container rm <container name>

# remove image
docker rmi <image name>
```