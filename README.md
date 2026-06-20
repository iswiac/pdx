# Photo inDeXer (pdx)

## Prerequisites

- Python 3.13+
- [Ollama](https://ollama.com) with a vision-language model pulled (e.g. `ollama pull gemma4:26b`)
- [Podman](https://podman.io) for running Qdrant
- `exiftool` for EXIF/GPS metadata extraction (`sudo apt install -y libimage-exiftool-perl`)
- `libGL` for face recognition (`sudo apt install -y libgl1` on Debian/Ubuntu, `sudo dnf install -y mesa-libGL` on Fedora) — optional, only needed if using the `faces` config

See [README-Windows.md](README-Windows.md) for Windows/WSL-specific setup.

## Set up a virtual Python environment

```sh
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

Copy the example config and adjust it for your setup:

```sh
cp config.example.yaml config.yaml
```

| Section | Key | Description |
|---------|-----|-------------|
| `ai` | `language` | Output language: `cs` (Czech) or `en` (English) |
| `ai` | `ollama_url` | URL of the Ollama API endpoint |
| `ai` | `model_name` | Vision-language model to use (e.g. `gemma4:26b`) |
| `location` | `home_names` | List of city names considered "home" — photos taken here won't have the location in the folder name |
| `faces` | `reference_dir` | Directory with reference face photos for recognition (one subdirectory per person) |
| `faces` | `similarity_threshold` | Face matching threshold (lower = stricter, default `0.4`) |
| `faces` | `name_map` | Map directory names to display names (e.g. `john: "Johnny"`) |
| `storage` | `context_file` | Path to a text file with family/personal context for the AI |
| `storage` | `history_file` | JSON list of past folder names (e.g. `"210619 - Beach volleyball"`) used as style examples for AI naming |

### Face recognition (optional)

To enable face recognition, create a reference directory with one subdirectory per person, each containing a few clear photos of their face (one face per photo):

```
~/results/pdx/faces/
├── john/
│   ├── photo1.jpg
│   ├── photo2.jpg
│   └── photo3.jpg
└── jane/
    ├── photo1.jpg
    └── photo2.jpg
```

Directory names are used as identifiers. Use `name_map` in the config to map them to display names (e.g. `john: "Johnny"`). 3-5 reference photos per person is usually enough.

### Family context (optional)

The `context_file` (default: `family_context.txt`) gives the AI background knowledge about your family — names, hobbies, sports, travel habits. This helps it generate more accurate photo descriptions and folder names. Write it in the same language as your `language` setting. Example:

```
FAMILY MEMBERS:
- Dad: Born 1985. Hobbies, sports.
- Mom: Born 1987. Hobbies, interests.
- Child1: Born 2013. Sport (team name, jersey color).

SPORTS:
- Sport1 (Child1 only): Jersey description, equipment.
- Sport2 (Dad): Gear, typical events.
```

If the file is missing, the AI falls back to generic descriptions.

## Start/stop Qdrant (podman)

Storage is in the `pdx` directory under XDG data home (default: `~/.local/share/pdx`).
You can manage the `pdx-qdrant` container using the following commands:

```sh
pdx start       # start Qdrant container
pdx logs        # show Qdrant container logs
pdx logs -f     # follow Qdrant container logs
pdx stop        # stop Qdrant container
```

## Index photos

```sh
pdx index /path/to/photos1                      # create the `default` collection if it does not exist yet
pdx index /path/to/photos2                      # extend the `default` collection by indexing more photos
pdx index -c private /path/to/private_photos    # create or extend the `private` collection
pdx erase -c private                            # delete the `private` collection
```

## Organize photos
```sh
pdx organize -c private /path/to/organized_folder   # Use AI and EXIF to group photos into a structured directory tree.
```

## Query photos

```sh
pdx query gearbox                               # list photos of gearbox (most relevant first)
pdx query -c private treasure                   # list photos of treasure in the `private` collection
pdx query --viewer=gwenview gearbox             # show photos of gearbox using the `gwenview` app
pdx query --viewer=gwenview                     # enter interactive prompt
```

## License

This project is licensed under the [Apache License 2.0](LICENSE).
