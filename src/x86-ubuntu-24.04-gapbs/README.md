---
title: Base Linux x86-ubuntu image
shortdoc: >
    Resources to build a generic x86-ubuntu disk image and run a "boot-exit" test.
authors: ["Harshil Patel"]
---

The x86-ubuntu disk image is based on Ubuntu 22.04 and has its `.bashrc` file modified in such a way that it executes a script passed from the gem5 configuration files (using the `m5 readfile` instruction).
The `boot-exit` test passes a script that causes the guest OS to terminate the simulation (using the `m5 exit` instruction) as soon as the system boots.

## What's on the disk?

- username: gem5
- password: 12345

- The `gem5-bridge`(m5) utility is installed in `/usr/local/bin/gem5-bridge`.
- `libm5` is installed in `/usr/local/lib/`.
- The headers for `libm5` are installed in `/usr/local/include/gem5-bridge`.

Thus, you should be able to build packages on the disk and easily link to the gem5-bridge library.

The disk has network disabled by default to improve boot time in gem5.

If you want to enable networking, you need to modify the disk image and move the file `/etc/netplan/00-installer-config.yaml.bak` to `/etc/netplan/00-installer-config.yaml`.

### Installed packages

- `build-essential`
- `git`
- `scons`
- `vim`

## Init Process and Exit Events

This section outlines the disk image's boot process variations and the impact of specific boot parameters on its behavior.
By default, the disk image boots with systemd in a non-interactive mode.
Users can adjust this behavior through kernel arguments at boot time, influencing the init system and session interactivity.

### Boot Parameters

The disk image supports two main kernel arguments to adjust the boot process:

- `no_systemd=true`: Disables systemd as the init system, allowing the system to boot without systemd's management.
- `interactive=true`: Enables interactive mode, presenting a shell prompt to the user for interactive session management.

Combining these parameters yields four possible boot configurations:

1. **Default (Systemd, Non-Interactive)**: The system uses systemd for initialization and runs non-interactively.
2. **Systemd and Interactive**: Systemd initializes the system, and the boot process enters an interactive mode, providing a user shell.
3. **Without Systemd and Non-Interactive**: The system boots without systemd and proceeds non-interactively, executing predefined scripts.
4. **Without Systemd and Interactive**: Boots without systemd and provides a shell for interactive use.

### Note on Print Statements and Exit Events

- The bold points in the sequence descriptions are `printf` statements in the code, indicating key moments in the boot process.
- The `**` symbols mark gem5 exit events, essential for simulation purposes, dictating system shutdown or reboot actions based on the configured scenario.

### Boot Sequences

#### Default Boot Sequence (Systemd, Non-Interactive)

- Kernel output
- **Kernel Booted print message** **
- Running systemd print message
- Systemd output
- autologin
- **Running after_boot script** **
- Print indicating **non-interactive** mode
- **Reading run script file**
- Script output
- Exit **

#### With Systemd and Interactive

- Kernel output
- **Kernel Booted print message** **
- Running systemd print message
- Systemd output
- autologin
- **Running after_boot script** **
- Shell

#### Without Systemd and Non-Interactive

- Kernel output
- **Kernel Booted print message** **
- autologin
- **Running after_boot script** **
- Print indicating **non-interactive** mode
- **Reading run script file**
- Script output
- Exit **

#### Without Systemd and Interactive

- Kernel output
- **Kernel Booted print message** **
- autologin
- **Running after_boot script** **
- Shell

This detailed overview provides a foundational understanding of how different boot configurations affect the system's initialization and mode of operation.
By selecting the appropriate parameters, users can customize the boot process for diverse environments, ranging from automated setups to hands-on interactive sessions.

## Example Run Scripts

Within the gem5 repository, two example scripts are provided which utilize the x86-ubuntu resource.

The first is `configs/example/gem5_library/x86-ubuntu-run.py`.
This will boot the OS with a Timing CPU.
To run:

```sh
scons build/X86/gem5.opt -j`nproc`
./build/X86/gem5.opt configs/example/gem5_library/x86-ubuntu-run.py
```

The second is `configs/example/gem5_library/x86-ubuntu-run-with-kvm.py`.
This will boot the OS using KVM cores before switching to Timing Cores to run a simple echo command.
To run:

```sh
scons build/X86/gem5.opt -j`nproc`
./build/X86/gem5.opt configs/example/gem5_library/x86-ubuntu-run-with-kvm.py`
```

**Note:** the `x86-ubuntu-with-kvm.py` script requires a host machine with KVM to function correctly.

## Building and modifying the disk image

See [BUILDING.md](BUILDING.md) for instructions on how to build the disk image.

See [using-local-resources](https://www.gem5.org/documentation/gem5-stdlib/using-local-resources) for instructions on how to use customized resources in gem5 experiments.

To boot in qemu, make sure to specify `/sbin/init.old` as the `init=` option on the kernel command line.
Otherwise, you will execute the gem5 magic instructions which will cause illegal instructions or segmentation faults.
