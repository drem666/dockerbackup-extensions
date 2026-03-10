```bash
Y:\dockers\docker-backup-extension>cd py6
Y:\dockers\docker-backup-extension\py6>call Y:\venv\Scripts\activate
(venv) Y:\dockers\docker-backup-extension\py6>python main.py
sh: cd: line 0: can't cd to /tmp/docker-desktop-root/mnt/docker-desktop-disk/: No such file or directory
Traceback (most recent call last):
  File "Y:\dockers\docker-backup-extension\py6\main.py", line 259, in <module>
    window = MainWindow()
  File "Y:\dockers\docker-backup-extension\py6\main.py", line 26, in __init__
    self._create_ui()
  File "Y:\dockers\docker-backup-extension\py6\main.py", line 140, in _create_ui
    self.model = VolumeTreeModel()
  File "Y:\dockers\docker-backup-extension\py6\volume_model.py", line 28, in __init__
    self._build_model()
  File "Y:\dockers\docker-backup-extension\py6\volume_model.py", line 31, in _build_model
    volumes = list_volumes()
  File "Y:\dockers\docker-backup-extension\py6\utils.py", line 43, in list_volumes
    output = subprocess.check_output(cmd, universal_newlines=True)
  File "C:\Python313\Lib\subprocess.py", line 474, in check_output
    return run(*popenargs, stdout=PIPE, timeout=timeout, check=True,
               **kwargs).stdout
  File "C:\Python313\Lib\subprocess.py", line 579, in run
    raise CalledProcessError(retcode, process.args,
                             output=stdout, stderr=stderr)
subprocess.CalledProcessError: Command '['wsl', '-d', 'docker-desktop', 'sh', '-c', "cd '/tmp/docker-desktop-root/mnt/docker-desktop-disk/' && find . \\( -type d -o -type f \\)"]' returned non-zero exit status 2.

(venv) Y:\dockers\docker-backup-extension\py6>python main.py
```