import requests as req
import click
import base64
from typing import Literal, Optional, List, Final
from pydantic import BaseModel, Field
from pathlib import Path

CREDS_FILE: Final[Path] = Path(Path(__file__).parent, '.creds').resolve()
KEY_SEPARATOR: Final[str] = '::'

class Action(BaseModel):
    type: Literal['drop', 'forward', 'worker']
    value: List[str]

class Matcher(BaseModel):
    field: Literal['to']
    type: Literal['literal']
    value: str

class NewEmailRequestBody(BaseModel):
    actions: List[Action]
    matchers: List[Matcher]
    enabled: bool = True
    name: Optional[str] = None
    priority: Optional[int] = Field(None, ge = 0)

def generate_request_body(*, email_name: str, domain: str, dest_email: str) -> dict:
    email_name = email_name.strip()
    domain = domain.strip()
    dest_email = dest_email.strip()

    return NewEmailRequestBody(
        actions = [
            Action(
                type = 'forward',
                value = [dest_email]
            )
        ],
        matchers = [
            Matcher(
                field = 'to',
                type = 'literal',
                value = f'{email_name}@{domain}'
            )
        ],
        name = f'Forward {email_name}@{domain} to {dest_email}'
    ).model_dump(exclude_none = True)

def add_new_email(*, cf_email: str, cf_token: str, zone_id: str, body: dict) -> bool:
    cf_email = cf_email.strip()
    cf_token = cf_token.strip()
    zone_id = zone_id.strip()

    res: req.Response = req.post(
        url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/email/routing/rules',
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-Email': cf_email,
			'X-Auth-Key': cf_token
        },
        json = body
    )

    return res.json()['success']

def save_credential(key: str, value: str) -> None:
    creds: dict[str, str] = {}

    for line in CREDS_FILE.read_text().splitlines():
        if KEY_SEPARATOR in line:
            k, v = line.strip().split(KEY_SEPARATOR, 1)
            creds[k] = v

    encoded_key: str = base64.b64encode(key.encode()).decode('utf-8')
    encoded_value: str = base64.b64encode(value.encode()).decode('utf-8')

    creds[encoded_key] = encoded_value

    CREDS_FILE.write_text('\n'.join(
        f'{k}{KEY_SEPARATOR}{v}'
        for k, v
        in creds.items()
    ))

def get_saved_credential(key: str) -> Optional[str]:
    encoded_key: str = base64.b64encode(key.encode()).decode('utf-8')

    for line in CREDS_FILE.read_text().splitlines():
        if KEY_SEPARATOR in line:
            k, v = line.strip().split(KEY_SEPARATOR, 1)
            if k == encoded_key:
                return base64.b64decode(v.encode()).decode('utf-8')

    return None

def prompt(text: str, *, secret: bool = False, ask_save: bool = False) -> str:
    saved_value: Optional[str] = get_saved_credential(text)
    if saved_value is not None:
        click.echo(click.style(f'{text}: Using saved value', fg = 'blue', bold = True))
        click.echo()
        return saved_value

    res: str = click.prompt(
        click.style(text, fg = 'yellow', bold = True),
        value_proc = str,
        prompt_suffix = ' > ',
        hide_input = secret,
    )

    if not secret:
        click.echo(click.style(f'✅ {res}', fg = 'green', bold = True))

    if ask_save:
        should_save: bool = click.confirm(
            click.style('Save this option?', fg = 'blue', bold = True),
            default = True
        )
        if should_save:
            save_credential(text, res)
            click.echo(click.style('✅ Saved', fg = 'green', bold = True))

    click.echo()
    return res.strip()

def main() -> None:
    if not CREDS_FILE.exists():
        CREDS_FILE.write_bytes(b'')

    cf_email: str = prompt('CF account email', ask_save = True)
    cf_token: str = prompt('CF token', secret = True, ask_save = True)
    zone_id: str = prompt('Zone ID', ask_save = True)
    domain: str = prompt('Domain', ask_save = True)
    email_name: str = prompt('New email name')
    dest_email: str = prompt('Destination email')

    body: dict = generate_request_body(
        email_name = email_name,
        domain = domain,
        dest_email = dest_email
    )

    success: bool = add_new_email(
        cf_email = cf_email,
        cf_token = cf_token,
        zone_id = zone_id,
        body = body
    )

    if success:
        click.echo(click.style(f'✅ Email forwarding rule created successfully!', fg = 'green', bold = True))
    else:
        click.echo(click.style(f'❌ Failed to create email forwarding rule', fg = 'red', bold = True))

if __name__ == '__main__':
    try:
        main()
    except click.exceptions.Abort:
        pass