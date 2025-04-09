> A simple utility script to add a new email forwarding rule to a Cloudflare-registered domain.

## Installation ⚙️

### Get your API token

Go to [your profile's API tokens tab](https://dash.cloudflare.com/profile/api-tokens) and click the **View** button for your **Global API Key**.

> [!CAUTION]
>
> If you choose to save your token when running the script, make sure that the `.creds` file doesn't get shared!

### Get your domain's Zone ID

Go to [your profile's domains tab](https://dash.cloudflare.com), select your domain, scroll down the **Overview**'s tab and copy the **Zone ID**.

### Install UV

Follow the docs for your platform [here](https://docs.astral.sh/uv/getting-started/installation/).

### Clone the repository

```bash
git clone https://github.com/madkarmaa/cloudflare-new-email.git
cd ./cloudflare-new-email/
```

### Install dependencies

```bash
uv sync
```

### Run the program

```bash
uv run ./main.py
```
