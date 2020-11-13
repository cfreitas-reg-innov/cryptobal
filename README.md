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

