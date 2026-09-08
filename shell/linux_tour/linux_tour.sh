#!/usr/bin/env bash
set -e
step() { echo; echo "=== $1 ==="; }

step "root layout (FHS)"
ls -la /

step "file types: binary, text, device, virtual"
file /bin/ls /etc/passwd /dev/null /proc/version

step "inode + perms + timestamps of one file"
stat /etc/passwd

step "directories are just files (same inode structure)"
work=$(mktemp -d)
touch "$work/file1"
mkdir "$work/subdir"
echo "-- a regular file's inode --"
stat "$work/file1"
echo "-- a directory's inode: same fields, type is just 'directory' --"
stat "$work/subdir"
echo "-- link count trivia: each subdir bumps the parent's link count (its '..' entry) --"
stat -c 'Links: %h  %n' "$work"
mkdir "$work/subdir2"
stat -c 'Links: %h  %n' "$work"
echo "-- cat refuses a directory -- kernel policy, not proof it isn't a file --"
cat "$work" 2>&1 || true
echo "-- ls is just the syscall that reads a directory's own data (name -> inode pairs) --"
ls -la "$work"
rm -rf "$work"

step "inode = data, filename = directory entry (hardlink vs symlink)"
work=$(mktemp -d)
echo "original content" > "$work/original"
ln    "$work/original" "$work/hardlink"   # same inode, two names
ln -s "$work/original" "$work/symlink"    # new inode, just stores a path
echo "-- inode numbers: original and hardlink match, symlink is its own inode --"
ls -li "$work"
echo "-- editing through the hardlink changes 'original' too -- it IS original --"
echo "edited via hardlink" >> "$work/hardlink"
cat "$work/original"
echo "-- delete the original name; the data survives because the inode still has a link --"
rm "$work/original"
cat "$work/hardlink"
echo "-- but the symlink is now dangling -- it only ever stored a path, not an inode --"
ls -l "$work/symlink"
cat "$work/symlink" 2>&1 || true
rm -rf "$work"

step "inode numbers reveal /bin -> /usr/bin symlink"
ls -li /bin/ls /usr/bin/ls
readlink -f /bin

step "mounted filesystems"
mount | column -t | head -15

step "disk usage per mount"
df -h

step "block device tree"
lsblk

step "/proc is a virtual window into the kernel"
head -5 /proc/cpuinfo
cat /proc/version

step "/sys exposes devices/drivers"
ls /sys/class/net

step "stdin/stdout/stderr are just fds pointing at your tty"
echo "your controlling terminal device (or 'not a tty' if run non-interactively, e.g. piped):"
tty || true
echo "fd 0(in)/1(out)/2(err) in this shell -> symlinks to that tty device, or to a pipe if non-interactive"
ls -l /proc/self/fd
echo "-- redirecting stdout is nothing magic: fd 1 just points somewhere else --"
(exec 1>/tmp/linux_tour_redir.txt; ls -l /proc/self/fd)
echo "captured output now lives in the file fd 1 was pointed at:"
cat /tmp/linux_tour_redir.txt
rm -f /tmp/linux_tour_redir.txt
echo "-- every open terminal/ssh/tmux session gets its own pseudo-tty device --"
ls /dev/pts
echo "-- 'a million ttys': one real tty (physical console) vs many pty pairs --"
echo "   each terminal emulator/ssh session holds the pty MASTER;"
echo "   your shell attaches to the matching pty SLAVE, shown as /dev/pts/N"
ps -eo pid,tty,cmd | grep -E ' pts/| tty' | head -10

step "process tree, PID 1 down"
ps --ppid 2 -p 2 --forest -o pid,cmd 2>/dev/null || pstree -p | head -15

step "who/what owns this shell"
who
echo "shell pid: $$"
