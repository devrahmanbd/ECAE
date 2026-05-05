import asyncio
import argparse
import os
import httpx
import msal

API_BASE_URL = 'https://graph.microsoft.com/v1.0'

async def get_access_token(client_id: str, tenant_id: str, client_secret: str) -> str | None:
    try:
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        scopes = ["https://graph.microsoft.com/.default"]

        app = msal.ConfidentialClientApplication(
            client_id=client_id,
            authority=authority,
            client_credential=client_secret
        )
        result = app.acquire_token_for_client(scopes=scopes)

        if "access_token" in result:
            return result["access_token"]
        else:
            print(f"Error acquiring token: {result.get('error')} - {result.get('error_description')}")
            return None

    except Exception as e:
        print(f"Exception occurred fetching token: {str(e)}")
        return None

async def create_user(access_token: str, email: str, ms_acc_domain: str, session: httpx.AsyncClient) -> bool | None:
    display_name = email.split('@')[0].replace('.', ' ').title()
    principal_name = f"{email.replace('@', '_')}#EXT#@{ms_acc_domain}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    password = "Welcome@123"
    user_data = {
        "accountEnabled": True,
        "displayName": display_name,
        "mailNickname": email.split('@')[0],
        "userPrincipalName": principal_name,
        "userType": "Guest",
        "mail": email,
        "passwordProfile": {
            "forceChangePasswordNextSignIn": True,
            "password": password
        }
    }

    try:
        resp = await session.post(
            f"{API_BASE_URL}/users",
            headers=headers,
            json=user_data
        )
        data = resp.json()
        if resp.status_code == 201:
            print(f"Created user: {email}")
            return True
        elif 'Directory_QuotaExceeded' in resp.text:
            print(f"Directory quota exceeded for: {email}")
            return False
        else:
            print(f"Failed to create {email}: {resp.status_code} - {data}")
            return None
    except Exception as e:
        print(f"Exception creating {email}: {str(e)}")
        return None

async def Process_User_Creation(
    record: str,
    session: httpx.AsyncClient,
    storage_dir: str,
    workers_per_account: int
):
    fields = record.split('\t')
    ms_acc_email = fields[0]
    ms_acc_domain = ms_acc_email.split('@')[1]
    client_secret = fields[3]
    client_id = fields[4]
    tenant_id = fields[5]

    print(f"{ms_acc_email} processing...")
    email_file = os.path.join(storage_dir, f"{ms_acc_email}.txt")
    try:
        emails = open(email_file, 'r').read().splitlines()
    except FileNotFoundError:
        print(f"Email file not found: {email_file}")
        return

    token = await get_access_token(client_id, tenant_id, client_secret)
    if not token:
        print(f"{ms_acc_email} - failed to get access token")
        with open('failed.txt', 'a') as f:
            f.write(f"{ms_acc_email}\n")
        return

    print(f"{ms_acc_email} - access token acquired")
    pending = [create_user(token, e, ms_acc_domain, session) for e in emails]
    total_created = 0
    quota_exceeded = False

    while pending and not quota_exceeded:
        batch = pending[:workers_per_account]
        pending = pending[workers_per_account:]
        results = await asyncio.gather(*batch)
        total_created += sum(1 for r in results if r is True)
        if any(r is False for r in results):
            quota_exceeded = True
        print(f"{ms_acc_email} - created so far: {total_created}")

    with open('success.txt', 'a') as f:
        f.write(f"{ms_acc_email} - {total_created} users created\n")

    print(f"{ms_acc_email} - done, total: {total_created}")

async def run_uploader(
    data_file: str,
    storage_dir: str,
    workers_per_account: int,
    batch_size: int
):
    os.makedirs(storage_dir, exist_ok=True)
    records = open(data_file, 'r').read().splitlines()
    session = httpx.AsyncClient(timeout=25)
    tasks = [
        Process_User_Creation(rec, session, storage_dir, workers_per_account)
        for rec in records
    ]

    index = 0
    while index < len(tasks):
        batch = tasks[index:index+batch_size]
        await asyncio.gather(*batch)
        index += batch_size

    await session.aclose()
    print('All uploads completed.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch upload contacts via MS Graph')
    parser.add_argument('--data-file', default='data.txt', help='Tab-separated account records')
    parser.add_argument('--storage-dir', default='storage', help='Directory with per-account email lists')
    parser.add_argument('--workers-per-account', type=int, default=10, help='Concurrent user-creation per account')
    parser.add_argument('--batch-size', type=int, default=5, help='Concurrent account-processing batch size')
    args = parser.parse_args()

    asyncio.run(run_uploader(
        data_file=args.data_file,
        storage_dir=args.storage_dir,
        workers_per_account=args.workers_per_account,
        batch_size=args.batch_size
    ))


