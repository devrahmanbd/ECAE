Install-Module -Name ExchangeOnlineManagement -Force
Import-Module ExchangeOnlineManagement

function login_to_microsoft_365($user_name) {
    try {
        Connect-ExchangeOnline -UserPrincipalName $user_name -ErrorAction Stop
        Write-Host -ForegroundColor Green "Login Successful. Script Execution Continues...`n"
        return $true
    }
    catch {
        Write-Host "Error Logging: $_"
        return $false
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
        Write-Host -ForegroundColor Green "Message Approval Enabled for $group_name with $moderator_email as Moderator`n"
        
        Add-Content -Path "unique_domain.txt" -Value $email
    }
    catch {
        Write-Host "Error Creating Mail Enabled Security Group Named ${group_name}: $_"
    }
}

$user_names      = Get-Content -Path "users.txt"
$total_users     = $user_names.Count
$user_count      = 1
$group_prefix    = 'new_batch'
$group_limit     = 10

foreach ($user_name in $user_names) {
    $domain          = $user_name.Split('@')[1]
    $group_index     = 1
    Write-Host -ForegroundColor Green "$user_count/$total_users. $user_name - Processing..."
    $logincheck = login_to_microsoft_365($user_name)
    if ($logincheck -eq $true) {
        for ($i = 1; $i -le $group_limit; $i++) {
            $group_name = "$group_prefix$group_index"
            # create_new_distribution_group $group_name $domain
            create_distribution_group_with_moderator_message_approval $group_name $domain $user_name 
            $group_index++
        }
        Write-Host -ForegroundColor Green "------------------------------------------------------------`n"
    }
    else {
        Write-Host -ForegroundColor Red "Login Failed. Skipping to next account...`n"
    }
    $user_count++
}

Write-Host -ForegroundColor Green "Script Execution Completed Successfully !"