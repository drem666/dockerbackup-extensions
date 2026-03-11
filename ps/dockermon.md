# Functions 
Docker volume backups
Docker service monitoring
Container stop monitoring
All containers stopped detection
Transfer/sync files into containers
Structured logging
Retention cleanup
Help system

```bash
# Show Help
.\dockermon.ps1 -Help
# Backup Docker volumes
.\dockermon.ps1 -BackupVolumes
# Monitor container stops
.\dockermon.ps1 -WatchContainerStop -ContainerName nginx
# Continuous monitoring
.\dockermon.ps1 -WatchAllContainersStop -Loop
# Transfer files to container
.\dockermon.ps1 `
-Transfer `
-ContainerName nginx `
-Source C:\data `
-Destination /var/www `
-Method dockercp
```

This merged tool adds:
    unified single script
    help system
    structured logging
    backup retention
    container validation
    file transfer capability
    rsync option
    continuous monitoring mode