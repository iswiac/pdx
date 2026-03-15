# Installation steps specific to Windows 11 with Debian distribution

This guide provides instructions for setting up and building `pdx` on a Windows 11 machine using the Windows Subsystem for Linux (WSL) with a Debian distribution.

## Enable WSL and Install Debian

- Open Windows PowerShell as an Administrator and run:
```
wsl --install -d Debian
```
- During the Debian installation create a new UNIX username and password

## Setting Up the Debian Environment

- Launch the Debian terminal from the Start Menu or from PowerShell using:
```
wsl -d Debian
```
- Update your package list and install the required dependencies:
```
sudo apt update && sudo apt upgrade -y
sudo apt install -y python-is-python3 python3-venv git podman
```
- Ensure your environment satisfies the project requirements (Python 3.13+)
-- Note: If your Debian version provides an older Python, you may need to use a tool like pyenv or add the Debian Backports repository.
```
python3 --version
```

## Cloning and Building

- Clone the repository:
```
git clone https://github.com/kdudka/pdx
cd pdx
```
- Continue with the build instructions provided in the main documentation

## Note on Windows Filesystem

- WSL automatically mounts your Windows C: drive at /mnt/c/. You can navigate directly to your workspace:
```
cd /mnt/c/Users/<YourWindowsUser>/
```

## Additional Debian packages (optional)

- To view the photos selected after a `pdx` query, use `qimgv` instead of `gwenview` due to stability in Windows 
```
sudo apt install -y qimgv
```
