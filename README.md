# ledger_bot

1. Install dependencies from Poetry - `poetry install` or `poetry install --with dev`
2. Create a `.env` file (or otherwise set the required env variables)
3. Run the bot:
   - If using dev dependencies: `poetry run task start`
   - If not using dev dependencies: `poetry run python -m ledger_bot`

Although ledger-bot has been built using [Poetry](https://python-poetry.org/), `requirements.txt` is included for those who require it.

Dev deploys can be changed via altering value of the GitHub variable `DO_DEV_DEPLOY`. Set the value to `1` to deploy and `0` to skip it.
