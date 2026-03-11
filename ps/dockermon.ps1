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
    [string]$Method = "dockercp",   # dockercp | rsync
    [string]$Source,
    [string]$Destination,

    [string]$LogDir = ".\logs",

    [switch]$Help
)

# ---------- HELP ----------
function Show-Help {

Write-Host ""
Write-Host "DockerMon Utility"
Write-Host "================="
Write-Host ""
Write-Host "Monitoring:"
Write-Host "  -MonitorDockerService        Check Docker service state"
Write-Host "  -WatchContainerStop          Monitor container stop events"
Write-Host "  -ContainerName <name>        Target container"
Write-Host "  -WatchAllContainersStop      Detect when all containers stop"
Write-Host "  -Loop                        Continuous monitoring"
Write-Host ""
Write-Host "Backup:"
Write-Host "  -BackupVolumes               Backup all Docker volumes"
Write-Host "  -BackupDir <path>"
Write-Host "  -RetentionDays <days>"
Write-Host ""
Write-Host "Container File Transfer:"
Write-Host "  -Transfer"
Write-Host "  -Method dockercp|rsync"
Write-Host "  -ContainerName <name>"
Write-Host "  -Source <path>"
Write-Host "  -Destination <container path>"
Write-Host ""
Write-Host "Logging:"
Write-Host "  -LogDir <directory>"
Write-Host ""
Write-Host "Help:"
Write-Host "  -Help"
Write-Host ""
}

if ($Help) { Show-Help; exit }

# ---------- INIT ----------
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

# ---------- CONTAINER VALIDATION ----------
function Validate-Container($name) {

    $containers = docker ps --format "{{.Names}}"

    if ($containers -notcontains $name) {
        Log "Container '$name' not running."
        return $false
    }

    return $true
}

# ---------- BACKUP VOLUMES ----------
function Backup-Volumes {

    Log "Starting volume backup..."

    $volumes = docker volume ls --format "{{.Name}}"

    foreach ($v in $volumes) {

        $file = "$BackupDir\$v-$timestamp.tar.gz"

        docker run --rm `
            -v ${v}:/data `
            -v ${BackupDir}:/backup `
            alpine tar czf /backup/$v-$timestamp.tar.gz /data

        Log "Backed up volume $v"
    }

    Get-ChildItem $BackupDir -Recurse |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays) } |
        Remove-Item -Force

    Log "Old backups cleaned."
}

# ---------- DOCKER SERVICE ----------
function Check-DockerService {

    $status = (Get-Service com.docker.service).Status

    Log "Docker service status: $status"
}

# ---------- CONTAINER STOP MONITOR ----------
function Watch-ContainerStopEvents {

    if ($ContainerName) {

        if (!(Validate-Container $ContainerName)) { return }

        Log "Watching container: $ContainerName"

        docker events `
        --filter type=container `
        --filter event=stop `
        --filter container=$ContainerName |
        ForEach-Object {

            Log "Container stopped: $ContainerName"
        }
    }
    else {

        Log "Watching all container stop events"

        docker events --filter type=container --filter event=stop |
        ForEach-Object {

            Log "A container stopped."
        }
    }
}

# ---------- ALL CONTAINERS STOPPED ----------
function Check-AllContainersStopped {

    $running = docker ps -q

    if (-not $running) {

        Log "All containers stopped."
    }
}

# ---------- FILE TRANSFER ----------
function Transfer-Files {

    if (!(Validate-Container $ContainerName)) { return }

    if (!(Test-Path $Source)) {
        Log "Source path not found"
        return
    }

    Log "Starting transfer"
    Log "Method: $Method"
    Log "Source: $Source"
    Log "Destination: $Destination"

    switch ($Method) {

        "dockercp" {

            docker cp $Source "$ContainerName`:$Destination"

            Log "Transfer via docker cp completed"
        }

        "rsync" {

            Log "Attempting rsync transfer"

            docker exec $ContainerName sh -c "which rsync || (apt-get update && apt-get install -y rsync || apk add rsync)"

            rsync -avz $Source "$ContainerName`:$Destination"

            Log "Rsync transfer completed"
        }

        default {
            Log "Unknown transfer method"
        }
    }
}

# ---------- EXECUTION ----------

if ($BackupVolumes) { Backup-Volumes }

if ($MonitorDockerService) {

    if ($Loop) {

        while ($true) {

            Check-DockerService
            Start-Sleep 10
        }
    }
    else {

        Check-DockerService
    }
}

if ($WatchContainerStop) { Watch-ContainerStopEvents }

if ($WatchAllContainersStop) {

    if ($Loop) {

        while ($true) {

            Check-AllContainersStopped
            Start-Sleep 10
        }
    }
    else {

        Check-AllContainersStopped
    }
}

if ($Transfer) { Transfer-Files }