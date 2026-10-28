#!/bin/sh
set -eu

# StartOS mounts the persisted volume over the image's /data ownership. Repair
# fresh and restored volumes before dropping privileges for the actual runtime.
install -d -o 10001 -g 10001 /data /data/backups /data/home /data/mnemosyne
chown -R 10001:10001 /data

exec gosu 10001:10001 "$@"