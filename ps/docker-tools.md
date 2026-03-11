# show help
.\docker-tools.ps1 -Help

# backup volumes
.\docker-tools.ps1 -BackupVolumes

# monitor docker service continuously
.\docker-tools.ps1 -MonitorDockerService -Loop

# monitor a specific container
.\docker-tools.ps1 -WatchContainerStop -ContainerName nginx

# check if all containers stopped
.\docker-tools.ps1 -WatchAllContainersStop