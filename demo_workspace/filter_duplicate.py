import asyncio
import re

async def Genarate_PS1(PwshContentTemp, i, Domain, UserName, GroupPrefix, emails_per_batch, NumOfGroupPerTab):
    GroupStartingIndex = (i - 1) * NumOfGroupPerTab + 1
    PwshContentTemp   = PwshContentTemp.replace("$email_file      = ''", f"$email_file      = 'emails_{i}.txt'")
    PwshContentTemp   = PwshContentTemp.replace("$new_domain      = ''", f"$new_domain      = '{Domain}'")
    PwshContentTemp   = PwshContentTemp.replace("$user_name       = ''", f"$user_name       = '{UserName}'")
    PwshContentTemp   = PwshContentTemp.replace("$group_index     = 0", f"$group_index     = {GroupStartingIndex}")
    PwshContentTemp   = PwshContentTemp.replace("$group_prefix    = ''", f"$group_prefix    = '{GroupPrefix}'")
    PwshContentTemp   = PwshContentTemp.replace("$email_per_batch = 0", f"$email_per_batch = {emails_per_batch}")

    with open(f"tab{i}.ps1", "w") as f:
        f.write(PwshContentTemp)

    print(f"tab{i}.ps1 has been generated")

async def extract_emails_from_lines(strings: str):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, strings)
    return emails

async def Emails_Duplicate_Remover(filename):
    Total_Lines       = len(open(filename, 'r').read().splitlines())
    unique_emails     = set()
    duplicates_emails = set()

    emails       = open(filename, 'r').read()
    emails       = emails.lower()
    valid_emails = await extract_emails_from_lines(emails)
    for email in valid_emails:
        if email in unique_emails:
            duplicates_emails.add(email)
        else:
            unique_emails.add(email)

    with open(filename, 'w') as file:
        file.write('\n'.join(unique_emails))
    
    TOTAL_LINES      = Total_Lines
    EMAILS_FOUND     = len(valid_emails)
    UNIQUE_EMAILS    = len(unique_emails)
    DUPLICATE_EMAILS = len(duplicates_emails)
    INVALID_EMAILS   = EMAILS_FOUND - UNIQUE_EMAILS if EMAILS_FOUND > UNIQUE_EMAILS else 0

    status = f"""
Total Lines: {TOTAL_LINES}
Emails Found: {EMAILS_FOUND}
Unique Emails: {UNIQUE_EMAILS}
Duplicate Emails: {DUPLICATE_EMAILS}
Invalid Emails: {INVALID_EMAILS}
    """
    print(status)
    return TOTAL_LINES, EMAILS_FOUND, UNIQUE_EMAILS, DUPLICATE_EMAILS, INVALID_EMAILS

async def separate_files(filename , number_of_emails:int):
    with open(filename , 'r') as data_file:
        separated_lines = [next(data_file) for _ in range(number_of_emails)]
    with open(filename , 'r') as data_file:
        lines = data_file.readlines()[number_of_emails:]
    with open(filename , 'w') as data_file:
        data_file.writelines(lines)
    return separated_lines


async def separate_emails(separated_lines, emails_per_file):
    file_count = 1
    for i in range(0, len(separated_lines), emails_per_file):
        with open(f'emails_{file_count}.txt', 'w') as f:
            f.writelines(separated_lines[i:i+emails_per_file])
        file_count += 1

async def Genarate_bat_script(NumOfTabs):
    temp = ''
    temp += '@echo off\n\n'
    temp += 'start "" "pwsh" -File "install.ps1"\n'
    temp += 'timeout /t 10 /nobreak\n\n'

    for i in range(1,NumOfTabs+1):
        temp += f'start "" "pwsh" -NoExit -File "tab{i}.ps1"\n'
        temp += 'timeout /t 5 /nobreak\n\n'

    with open('win.bat', 'w') as f:
        f.write(temp)

async def main():
    UserName         = input('Enter email: ')
    filename          = f'storage/{UserName}.txt'
    separate_amount   = len(open(filename, 'r').read().splitlines())
    Separate_Into_Tab = 10
    NumOfGroupPerTab  = 1
    Domain            = input('Enter Domain: ')
    GroupPrefix       = "new_batch"
    Emails_Per_Batch  = int(separate_amount/Separate_Into_Tab/NumOfGroupPerTab)
    PwshContentTemp   = open("sample.ps1", "r").read()

    for i in range(1, Separate_Into_Tab+1):
        await Genarate_PS1(PwshContentTemp, i, Domain, UserName, GroupPrefix, Emails_Per_Batch, NumOfGroupPerTab)

    await Genarate_bat_script(Separate_Into_Tab)
    print('Done')
    
    cutted_emails = await separate_files(filename , separate_amount)
    await separate_emails(cutted_emails, int(separate_amount/Separate_Into_Tab))
    await Emails_Duplicate_Remover(filename)

if __name__ == '__main__':
    asyncio.run(main())