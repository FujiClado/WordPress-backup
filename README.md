
# wpbackup.py:

Python script to backup Wordpress and  database to a remote sftp server.

## Feature List:

* Automatic detection of database details.
* Sftp backup to remote server.
* Gzip compression of archive file.
* Complete progress report on terminal. 

### Configuring wpbackup.py. 

Open the wpbackup.py and change the follwoing settings 

```
* SFTP_HOST = '192.168.1.5'
* SFTP_USER = 'root'
* SFTP_PASSWD = 'myPassword'
* SFTP_DIR = '/var/ftp/pub/backupdir'
* SFTP_PORT = '22'
```

  
 
### Usage 

```
[root@server]# wpbackup.py  /path/to/wordpress/installation [...]
```




