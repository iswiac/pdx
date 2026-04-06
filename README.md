# Photo inDeXer (pdx)

## Set up a virtual Python environment

```sh
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

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
pdx organize -c private /path/to/organized_folder   # Use AI and EXIF metadata to group photos into a structured directory tree.
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
