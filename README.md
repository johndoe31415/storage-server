# storage-server
This is a collection of tools and configuration scripts that I use to run a
storage server for backing up data remotely. It consists of an embedded
computer ("ILO") inside the main storage host ("storage"). The ILO uses GPIOs
to turn on/off the storage server (so it does not need to run 24/7).

There are client tools which do [restic](https://github.com/restic/restic)
backups as well, wrapping it in a script to first wake up the storage host,
then run the backup. All https is protected with client certificates.

## Dependencies
On the storage/ilo computers: fping, mako, apache2.

## Third-party Software
Included here is the following software:

  * [sprintf in JavaScript](https://github.com/alexei/sprintf.js/)
  * [Pure.CSS stylesheets and examples](https://purecss.io/)
  * [Progressbar.JS](https://github.com/kimmobrunfeldt/progressbar.js)

## Setting up the backup client
To setup the backup client on a new host, do the following:

  * As root, create a new private/public ssh keypair. For example:
    ```
    # ssh-keygen -t ed25519 -f ~/.ssh/backup_id_ed25519
    ```
  * Make sure that connections to the storage server use this keypair by
    default:
    ```
    # cat >>~/.ssh/config
    Host storage.dyn.example.com
        IdentityFile ~/.ssh/backup_id_ed25519
    ```
  * Also ensure that as your regular user you have access to the storage as
    well (whitelist that key additionally).
  * Check the sftp connection to the storage server works.
  * As user, run the client/storage_backup script once with the dryrun option:
    ```
    $ client/storage_backup -d
    ```
    It will create a default configuration file (typically
    ~/.config/jbin/backup/storage_backup.json).
  * Edit the configuration file and adapt to your needs. Set hostnames/ports
    and remove the "REMOVE_BEFORE_USAGE" key.
  * Initialize a restic repository on the remote:
    ``` 
    $ restic init -r sftp://joe@storage.dyn.example.com//data/joe/restic
    ``` 
    Make sure that restic repository is accessible with the key you configured
    (typically /etc/restic.txt).
  * Run the script without the dryrun option and see if everything works as
    expected.

# License
storage-server is licensed under GNU GPL-3. Included third-party software under their respective licenses.
