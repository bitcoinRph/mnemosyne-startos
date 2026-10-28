#!/bin/sh
set -eu

# StartOS mounts the persisted volume over the image's /data ownership. Repair
# fresh and restored volumes before dropping privileges for the actual runtime.
# Keep the mount root non-writable to the daemon so it cannot rename backups.
DATA_ROOT="${MNEMOSYNE_DATA_ROOT:-/data}"

assert_directory_or_absent() {
  path="$1"
  if [ -L "$path" ] || { [ -e "$path" ] && [ ! -d "$path" ]; }; then
    echo "refusing unsafe data path: $path" >&2
    exit 1
  fi
}

BACKUPS="$DATA_ROOT/backups"
HOME_DIR="$DATA_ROOT/home"
MNEMOSYNE_DIR="$DATA_ROOT/mnemosyne"
for path in "$DATA_ROOT" "$BACKUPS" "$HOME_DIR" "$MNEMOSYNE_DIR"; do
  assert_directory_or_absent "$path"
done

install -d -o 0 -g 0 -m 0755 "$DATA_ROOT"
chown 0:0 "$DATA_ROOT"
chmod 0755 "$DATA_ROOT"
install -d -o 10001 -g 10001 -m 0750 "$BACKUPS" "$HOME_DIR" "$MNEMOSYNE_DIR"
chown -R -h 10001:10001 "$BACKUPS" "$HOME_DIR" "$MNEMOSYNE_DIR"

exec gosu 10001:10001 "$@"
