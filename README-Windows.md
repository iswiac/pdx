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

## Install exiftool

The `organize` command requires `exiftool` for EXIF and GPS metadata extraction.
Without it, all photos will show as "Unknown location".

```
sudo apt install -y libimage-exiftool-perl
```

## Connect to Ollama on Windows

If Ollama is installed on Windows (not inside WSL), you need to make it accessible from WSL.

### 1. Make Ollama listen on all interfaces

Set a Windows environment variable:

- **Settings → System → About → Advanced system settings → Environment Variables**
- Add a new variable: `OLLAMA_HOST` = `0.0.0.0`
- Fully quit Ollama from the system tray (right-click → Quit) and relaunch it

Verify in PowerShell:

```
netstat -an | findstr 11434
```

You should see `0.0.0.0:11434` in the output.

### 2. Add a firewall rule

Find the WSL network address. In WSL, run:

```
ip -4 addr show eth0 | grep -oP 'inet \K[\d.]+'
```

Replace the host part of the IP with `0` to get the network address (e.g. if the
command prints `a.b.c.d`, use `a.b.0.0`). Then open PowerShell as Administrator:

```
netsh advfirewall firewall add rule name="Ollama WSL" dir=in action=allow protocol=TCP localport=11434 remoteip=<a.b.0.0>/20
```

This restricts access to the WSL subnet only.

### 3. Update config.yaml

Find your WSL gateway IP (this is the Windows host as seen from WSL):

```
ip route show default | awk '{print $3}'
```

Update `config.yaml` with that IP:

```yaml
ai:
  ollama_url: "http://<gateway-ip>:11434/api/chat"
```

### 4. Verify connectivity

```
curl http://<gateway-ip>:11434/api/version
```

You should get a JSON response with the Ollama version.

## Additional Debian packages (optional)

- To view the photos selected after a `pdx` query, use `qimgv` instead of `gwenview` due to stability in Windows
```
sudo apt install -y qimgv
```
