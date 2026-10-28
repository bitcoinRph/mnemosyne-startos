#!/bin/sh
set -eu

# StartOS mounts the persisted volume over the image's /data ownership. Repair
# fresh and restored volumes before dropping privileges for the actual runtime.
# Keep the mount root non-writable to the daemon so it cannot rename backups.
install -d -o 0 -g 0 -m 0755 /data
chown 0:0 /data
chmod 0755 /data
install -d -o 10001 -g 10001 -m 0750 /data/backups /data/home /data/mnemosyne
chown -R 10001:10001 /data/backups /data/home /data/mnemosyne

exec gosu 10001:10001 "$@"
