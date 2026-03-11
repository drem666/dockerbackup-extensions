param(
    [switch]$BackupVolumes,
    [string]$BackupDir = "D:\DockerBackups",
    [int]$RetentionDays = 7,

    [switch]$MonitorDockerService,
    [switch]$WatchContainerStop,
    [string]$ContainerName,

    [switch]$WatchAllContainersStop,
    [switch]$Loop,

    [switch]$Transfer,
    [string]$Source,
    [string]$Destination = "/tmp",
    [string]$Method = "dockercp",

    [string]$LogDir = ".\logs",

    [switch]$Help
)

#################################################
# HELP
#################################################

function Show-Help {

Write-Host ""
Write-Host "DockerMon Utility"
Write-Host "================="
Write-Host ""

Write-Host "Monitoring:"
Write-Host "  -MonitorDockerService       Check Docker service state"
Write-Host "  -WatchContainerStop         Monitor container stop events"
Write-Host "  -ContainerName <name>       Target container"
Write-Host "  -WatchAllContainersStop     Detect when all containers stop"
Write-Host "  -Loop                       Continuous monitoring"

Write-Host ""
Write-Host "Backup:"
Write-Host "  -BackupVolumes              Backup all Docker volumes"
Write-Host "  -BackupDir <path>"
Write-Host "  -RetentionDays <days>"

Write-Host ""
Write-Host "File Transfer:"
Write-Host "  -Transfer"
Write-Host "  -ContainerName <name>"
Write-Host "  -Source <path>"
Write-Host "  -Destination <container path>"
Write-Host "  -Method dockercp|rsync"

Write-Host ""
Write-Host "Logging:"
Write-Host "  -LogDir <directory>"

Write-Host ""
Write-Host "Examples:"
Write-Host "  .\dockermon.ps1 -BackupVolumes"
Write-Host "  .\dockermon.ps1 -MonitorDockerService"
Write-Host "  .\dockermon.ps1 -WatchContainerStop -ContainerName nginx"
Write-Host "  .\dockermon.ps1 -Transfer -ContainerName nginx -Source C:\data -Destination /data"

Write-Host ""
}

if ($Help) { Show-Help; exit }

#################################################
# INIT
#################################################

if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

$timestamp = Get-Date -Format "yyyy.MM.dd-HH.mm.ss"
$logfile = "$LogDir\dockermon-$timestamp.log"

function Log($msg) {

    $line = "$(Get-Date -Format s)  $msg"

    Write-Host $line
    Add-Content -Path $logfile -Value $line
}

#################################################
# CONTAINER SELECTION
#################################################

function Select-Container {

    $containers = docker ps --format "{{.Names}}"

    if (-not $containers) {
        Log "No running containers found."
        exit
    }

    Write-Host ""
    Write-Host "Select container:"
    $i = 1

    foreach ($c in $containers) {
        Write-Host "$i) $c"
        $i++
    }

    $choice = Read-Host "Enter number"

    $selected = $containers[$choice-1]

    return $selected
}

#################################################
# VALIDATION
#################################################

function Validate-Container($name) {

    $containers = docker ps --format "{{.Names}}"

    if ($containers -notcontains $name) {
        Log "Container '$name' not running."
        exit
    }
}

#################################################
# BACKUP VOLUMES
#################################################

function Backup-Volumes {

    Log "Starting Docker volume backup..."

    if (!(Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir | Out-Null
    }

    $volumes = docker volume ls --format "{{.Name}}"

    foreach ($v in $volumes) {

        $file = "$BackupDir\$v-$timestamp.tar.gz"

        docker run --rm `
        -v ${v}:/data `
        -v ${BackupDir}:/backup `
        alpine tar czf /backup/$v-$timestamp.tar.gz /data

        Log "Backed up volume: $v"
    }

    Log "Applying retention policy..."

    Get-ChildItem $BackupDir -Recurse |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays) } |
    Remove-Item -Force -ErrorAction SilentlyContinue

    Log "Backup completed."
}

#################################################
# DOCKER SERVICE STATUS
#################################################

function Check-DockerService {

    try {

        $status = (Get-Service com.docker.service).Status
        Log "Docker service status: $status"

    } catch {

        Log "Docker service not found."
    }
}

#################################################
# CONTAINER STOP MONITOR
#################################################

function Watch-ContainerStopEvents {

    if ($ContainerName) {

        Validate-Container $ContainerName
        Log "Watching container stop: $ContainerName"

        docker events `
        --filter type=container `
        --filter event=stop `
        --filter container=$ContainerName |
        ForEach-Object {

            Log "Container stopped: $ContainerName"
        }

    } else {

        Log "Watching ALL container stop events"

        docker events `
        --filter type=container `
        --filter event=stop |
        ForEach-Object {

            Log "A container stopped."
        }
    }
}

#################################################
# ALL CONTAINERS STOPPED
#################################################

function Check-AllContainersStopped {

    $running = docker ps -q

    if (-not $running) {

        Log "All containers stopped."
    }
}

#################################################
# FILE TRANSFER
#################################################

function Transfer-Files {

    if (-not $ContainerName) {
        $ContainerName = Select-Container
    }

    Validate-Container $ContainerName

    if (!(Test-Path $Source)) {
        Log "Source path not found: $Source"
        exit
    }

    Log "Transfer starting"
    Log "Container: $ContainerName"
    Log "Source: $Source"
    Log "Destination: $Destination"
    Log "Method: $Method"

    $file = Split-Path $Source -Leaf

    if ($Method -eq "dockercp") {

        docker cp $Source "$ContainerName`:$Destination"

        Log "docker cp completed"

    } elseif ($Method -eq "rsync") {

        Log "Checking rsync inside container..."

        docker exec $ContainerName sh -c "which rsync || (apk add --no-cache rsync || apt-get update && apt-get install -y rsync)"

        rsync -avz $Source "$ContainerName`:$Destination"

        Log "rsync transfer completed"

    }

    #################################################
    # ARCHIVE DETECTION
    #################################################

    if ($file -match "\.zip$") {

        Log "Extracting zip archive"

        docker exec $ContainerName sh -c "cd $Destination && unzip -o $file"

    }

    elseif ($file -match "\.tar$") {

        Log "Extracting tar archive"

        docker exec $ContainerName sh -c "cd $Destination && tar xf $file"

    }

    elseif ($file -match "\.tar\.gz$") {

        Log "Extracting tar.gz archive"

        docker exec $ContainerName sh -c "cd $Destination && tar xzf $file"

    }

    elseif ($file -match "\.tar\.bz2$") {

        Log "Extracting tar.bz2 archive"

        docker exec $ContainerName sh -c "cd $Destination && tar xjf $file"

    }

    Log "Transfer completed"
}

#################################################
# EXECUTION
#################################################

if ($BackupVolumes) {

    Backup-Volumes
}

if ($MonitorDockerService) {

    if ($Loop) {

        while ($true) {

            Check-DockerService
            Start-Sleep 10
        }

    } else {

        Check-DockerService
    }
}

if ($WatchContainerStop) {

    Watch-ContainerStopEvents
}

if ($WatchAllContainersStop) {

    if ($Loop) {

        while ($true) {

            Check-AllContainersStopped
            Start-Sleep 10
        }

    } else {

        Check-AllContainersStopped
    }
}

if ($Transfer) {

    Transfer-Files
}

if (-not ($BackupVolumes -or $MonitorDockerService -or $WatchContainerStop -or $WatchAllContainersStop -or $Transfer)) {

    Show-Help
}