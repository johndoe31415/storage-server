# storage-server
This is a collection of tools and configuration scripts that I use to run a
storage server for backing up data remotely. It consists of an embedded
computer ("ILO") inside the main storage host ("storage"). The ILO uses GPIOs
to turn on/off the storage server (so it does not need to run 24/7).

There are client tools which do [restic](https://github.com/restic/restic)
backups as well, wrapping it in a script to first wake up the storage host,
then run the backup. All https is protected with client certificates.

## Licenses

## Dependencies
On the storage/ilo computers: fping, mako, apache2.

# License
GNU GPL-3.
