import asyncio
import argparse
import os

async def separate_data(username: str, main_file: str, cut_size: int, storage_dir: str):
    with open(main_file, 'r') as f:
        emails = f.read().splitlines()

    cutted_emails = emails[:cut_size]
    remaining_emails = emails[cut_size:]

    os.makedirs(storage_dir, exist_ok=True)

    storage_file = os.path.join(storage_dir, f'{username}.txt')
    with open(storage_file, 'w') as f:
        f.write('\n'.join(cutted_emails) + '\n')
    with open('emails.txt', 'w') as f:
        f.write('\n'.join(cutted_emails) + '\n')
    with open(main_file, 'w') as f:
        f.write('\n'.join(remaining_emails) + ('\n' if remaining_emails else ''))

    print(f'Created {storage_file} - Remaining Emails: {len(remaining_emails)}')

async def run_separator(users_file: str, main_file: str, cut_size: int, storage_dir: str):
    with open(users_file, 'r') as f:
        users = f.read().splitlines()

    with open(main_file, 'r') as f:
        total_emails = len(f.read().splitlines())

    if cut_size * len(users) > total_emails:
        print(f'Not enough emails for {len(users)} users (need {cut_size * len(users)}, have {total_emails})')
        return

    for user in users:
        await separate_data(user, main_file, cut_size, storage_dir)

    print('Done')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Separate emails into per-user files.')
    parser.add_argument('--users-file', default='users.txt', help='Path to users file.')
    parser.add_argument('--main-file', default='all_data.txt', help='Path to main email file.')
    parser.add_argument('--cut-size', type=int, required=True, help='Number of emails per user.')
    parser.add_argument('--storage-dir', default='storage', help='Directory to store user files.')
    args = parser.parse_args()

    asyncio.run(run_separator(
        users_file=args.users_file,
        main_file=args.main_file,
        cut_size=args.cut_size,
        storage_dir=args.storage_dir
    ))
