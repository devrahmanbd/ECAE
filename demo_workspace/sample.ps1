function login_to_microsoft_365($user_name) {
    try {
        Install-Module -Name ExchangeOnlineManagement -Force
        Import-Module ExchangeOnlineManagement
        Connect-ExchangeOnline -UserPrincipalName $user_name -ErrorAction Stop
        Write-Host -ForegroundColor Green "Login Successful. Script Execution Continues...`n"
    }
    catch {
        Write-Host "Error Logging: $_"
        return
    }
}

function upload_email_contacts($email_batch) {
    try {
        $counter = 1
        $email_batch | ForEach-Object { 
            $uuid = (New-Guid).Guid
            $contactName = "$uuid"
            try {
                New-MailContact -Name $contactName -DisplayName $contactName -ExternalEmailAddress $_ -ErrorAction Stop
                Write-Host -ForegroundColor Green "$counter. Contact $contactName - $_ Created Successfully"
            }
            catch {
                Write-Host "$counter. Error Creating Contact $_"
            }
            $counter++
        }  
    }
    catch {
        Write-Host "Error Uploading Contacts Data: $_"
    }
}

function create_new_distribution_group($group_name, $domain) {
    try {
        New-DistributionGroup -Name $group_name -RequireSenderAuthenticationEnabled $false
        Write-Host -ForegroundColor Green "Distribution Group $group_name Created Successfully"
        $email = "$group_name@$domain"
        Add-Content -Path "$domain.txt" -Value $email
    }
    catch {
        Write-Host "Error Creating Distribution Group Named ${group_name}: $_"
    }
}

function create_distribution_group_with_moderator_message_approval($group_name, $domain, $moderator_email) {
    try {
        $group = New-DistributionGroup -Name $group_name -RequireSenderAuthenticationEnabled $false
        Write-Host -ForegroundColor Green "Distribution Group $group_name Created Successfully"
        
        $email = "$group_name@$domain"
        Set-DistributionGroup -Identity $group.Identity -PrimarySmtpAddress $email
        
        Set-DistributionGroup -Identity $group.Identity -ModeratedBy $moderator_email -ModerationEnabled $true -SendModerationNotifications "Always"
        Write-Host -ForegroundColor Green "Message Approval Enabled for $group_name with $moderator_email as Moderator"
        
        Add-Content -Path "unique_domain.txt" -Value $email
    }
    catch {
        Write-Host "Error Creating Mail Enabled Security Group Named ${group_name}: $_"
    }
}

function add_members_to_group($group_name, $email_batch) {
    try {
        $counter = 1
        $email_batch | ForEach-Object { 
            try {
                Add-DistributionGroupMember -Identity $group_name -Member $_ -ErrorAction Stop
                Write-Host -ForegroundColor Green "$counter. Contact $_ Added Successfully to $group_name"
            }  
            catch {
                Write-Host "$counter. Error Adding Member $_ to Group $group_name"
            }
            $counter++
        }
    }
    catch {
        Write-Host "Error Adding Members To Group ${group_name}: $_"
    }
}

function change_group_primary_email_address($group_name, $new_domain) {
    try {
        Set-DistributionGroup -Identity $group_name -PrimarySmtpAddress "$group_name@$new_domain" -ErrorAction Stop
        Write-Host -ForegroundColor Green "Distribution Group $group_name Primary Email Address Changed to $group_name@$new_domain`n"
        
        $new_email = "$group_name@$new_domain"
        Add-Content -Path "$new_domain.txt" -Value $new_email
    }
    catch {
        Write-Host "Error Changing Primary Email Address of Group ${group_name}: $_"
    }
}

$email_file      = ''
$new_domain      = ''
$user_name       = ''
$domain          = $user_name.Split('@')[1]
$group_index     = 0
$group_prefix    = ''
$emails          = Get-Content $email_file
$email_per_batch = 0

Write-Host -ForegroundColor Green "Starting Microsoft 365 Members Adders Script..."
Write-Host -ForegroundColor Green "Microsoft Account...$user_name"
login_to_microsoft_365 $user_name


for ($i = 0; $i -lt $emails.Count; $i += $email_per_batch) {
    $batch = $emails[$i..($i+$email_per_batch-1)]
    $group_name = "$group_prefix$group_index"
    Write-Host -ForegroundColor Green "Processing Group $group_index..."
    # upload_email_contacts $batch
    create_new_distribution_group $group_name $domain
    # create_distribution_group_with_moderator_message_approval $group_name $domain $user_name
    change_group_primary_email_address $group_name $new_domain
    add_members_to_group $group_name $batch
    $group_index++
}
Write-Host -ForegroundColor Green "Script Execution Completed Successfully !"