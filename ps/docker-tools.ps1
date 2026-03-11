param(
    [switch]$BackupVolumes,
    [string]$BackupDir = "D:\DockerBackups",
    [switch]$MonitorDockerService,
    [switch]$WatchContainerStop,
    [string]$ContainerName,
    [switch]$WatchAllContainersStop,
    [switch]$Loop,
    [switch]$Help
)

function Show-Help {
    Write-Host ""
    Write-Host "Docker Utility Script"
    Write-Host "---------------------"
    Write-Host "Options:"
    Write-Host " -BackupVolumes           Backup all Docker volumes"
    Write-Host " -BackupDir <path>        Backup directory (default: D:\DockerBackups)"
    Write-Host ""
    Write-Host " -MonitorDockerService    Log Docker Desktop service start/stop"
    Write-Host ""
    Write-Host " -WatchContainerStop      Monitor for container stop events"
    Write-Host " -ContainerName <name>    Target container name (optional)"
    Write-Host ""
    Write-Host " -WatchAllContainersStop  Log when no containers are running"
    Write-Host ""
    Write-Host " -Loop                    Run monitoring continuously"
    Write-Host ""
    Write-Host " -Help                    Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host " Backup all volumes:"
    Write-Host "   script.ps1 -BackupVolumes"
    Write-Host ""
    Write-Host " Monitor Docker service:"
    Write-Host "   script.ps1 -MonitorDockerService"
    Write-Host ""
    Write-Host " Watch a specific container:"
    Write-Host "   script.ps1 -WatchContainerStop -ContainerName mycontainer -Loop"
    Write-Host ""
}

function Ensure-EventSource {
    $source = "DockerMonitor"
    if (-not [System.Diagnostics.EventLog]::SourceExists($source)) {
        New-EventLog -LogName Application -Source $source
    }
}

function Backup-Volumes {
    Write-Host "Backing up Docker volumes..."
    $volumes = docker volume ls --format "{{.Name}}"

    foreach ($vol in $volumes) {
        $timestamp = Get-Date -Format "yyyyMMddHHmmss"
        $filename = "$vol" + "_" + "$timestamp.tar.gz"

        docker run --rm `
            -v ${vol}:/data `
            -v ${BackupDir}:/backup `
            alpine tar czf /backup/$filename /data

        Write-Host "Backed up volume: $vol"
    }
}

function Check-DockerService {
    Ensure-EventSource
    $serviceName = "com.docker.service"
    $status = (Get-Service -Name $serviceName).Status

    if ($status -eq "Running") {
        Write-EventLog -LogName Application -Source DockerMonitor -EventId 1001 -EntryType Information -Message "Docker service is running."
    }
    elseif ($status -eq "Stopped") {
        Write-EventLog -LogName Application -Source DockerMonitor -EventId 1002 -EntryType Warning -Message "Docker service is stopped."
    }
}

function Watch-ContainerStop {
    Ensure-EventSource

    if ($ContainerName) {
        Write-Host "Watching container: $ContainerName"
        docker events --filter type=container --filter event=stop --filter container=$ContainerName |
        ForEach-Object {
            Write-EventLog -LogName Application -Source DockerMonitor -EventId 1003 -EntryType Information -Message "Container $ContainerName stopped."
        }
    }
    else {
        Write-Host "Watching all container stop events"
        docker events --filter type=container --filter event=stop |
        ForEach-Object {
            Write-EventLog -LogName Application -Source DockerMonitor -EventId 1003 -EntryType Information -Message "A container stopped."
        }
    }
}

function Check-AllContainersStopped {
    Ensure-EventSource
    $containers = docker ps -q

    if (-not $containers) {
        Write-EventLog -LogName Application -Source DockerMonitor -EventId 1004 -EntryType Information -Message "All Docker containers have stopped."
    }
}

if ($Help) {
    Show-Help
    exit
}

if ($BackupVolumes) {
    Backup-Volumes
}

if ($MonitorDockerService) {
    if ($Loop) {
        while ($true) {
            Check-DockerService
            Start-Sleep -Seconds 10
        }
    }
    else {
        Check-DockerService
    }
}

if ($WatchContainerStop) {
    Watch-ContainerStop
}

if ($WatchAllContainersStop) {
    if ($Loop) {
        while ($true) {
            Check-AllContainersStopped
            Start-Sleep -Seconds 10
        }
    }
    else {
        Check-AllContainersStopped
    }
}