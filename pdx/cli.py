# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 The PDX Project Authors

"""Click-based CLI for pdx."""

import os
import sys

import click
import logging

try:
    import readline  # NOQA enable readline-like editing/history for input()
except ImportError:
    pass


@click.group()
@click.version_option()
def pdx():
    """PDX: photo indexing and search CLI."""
    pass


@pdx.command()
@click.option("--collection", "-c", default="default", help="Qdrant collection name.")
@click.option(
    "--force-cpu",
    is_flag=True,
    help="Force CPU processing (disable CUDA-based acceleration).",
)
@click.option(
    "--real-path", is_flag=True, help="Index absolute paths with symlinks expanded."
)
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
def index(collection: str, force_cpu: bool, real_path: bool, paths: tuple[str, ...]):
    """Index photos into a Qdrant collection."""
    from pdx.find import find_photos

    logging.basicConfig(level=logging.INFO)

    # collect paths to photos
    photos = find_photos(paths, include_symlinks=real_path)
    cnt = len(photos)
    logging.info(f"{cnt} photos to process")
    if not cnt:
        return

    if real_path:
        photos = [os.path.realpath(p) for p in photos]

    # delayed initialization of Model/VDB
    from pdx.index import Indexer

    idx = Indexer(force_cpu=force_cpu)
    idx.index_photos(collection, photos)

@pdx.command()
@click.argument("target", type=click.Path())
@click.option("--collection", "-c", default="default", help="Qdrant collection name.")
@click.option("--config", "-f", default="config.yaml", help="Path to config file.")
def organize(target: str, collection: str, config: str):
    """Organize indexed photos into a structured directory tree."""
    from pdx.organizer import Organizer
    logging.basicConfig(level=logging.INFO)
    org = Organizer(collection, target, config_path=config)
    org.organize()

@pdx.command()
@click.argument("query_args", nargs=-1)
@click.option("--collection", "-c", default="default", help="Qdrant collection name.")
@click.option("--limit", "-n", type=int, default=100, help="Max number of results.")
@click.option(
    "--min-score", "-s", type=float, default=0.2, help="Max number of results."
)
@click.option(
    "--viewer",
    "-v",
    default=None,
    metavar="CMD",
    help="Run CMD with a temp dir of symlinks to results instead of printing.",
)
def query(
    query_args: tuple[str, ...],
    collection: str,
    limit: int,
    min_score: float,
    viewer: str | None,
):
    """Search photos by natural language query. No query: interactive mode."""
    from pdx.query import QueryHandler

    logging.basicConfig(level=logging.INFO)
    handler = QueryHandler(collection, limit, min_score, viewer)

    query_str = " ".join(query_args).strip() if query_args else ""
    if query_str:
        # batch mode
        handler.query(query_str)
        return

    # Interactive mode: readline-like prompt repeatedly
    while True:
        try:
            line = input("query> ").strip()
        except EOFError:
            break

        if line:
            handler.query(line)


@pdx.command()
@click.option(
    "--collection",
    "-c",
    required=True,
    help="Qdrant collection name to delete (required to avoid accidental erase).",
)
def erase(collection: str):
    """Delete a Qdrant collection."""
    from pdx.qdrant import VDB

    vdb = VDB(cname=collection)
    if vdb.delete_collection():
        click.echo(f"Deleted collection {collection!r}.")
    else:
        click.echo(f"Collection {collection!r} does not exist.", err=True)
        sys.exit(1)


@pdx.command()
def start():
    """Start the Qdrant container for pdx (podman). Uses XDG data home/pdx for storage."""
    from pdx.podman import start as podman_start

    click.echo(podman_start())


@pdx.command()
def stop():
    """Stop the Qdrant container for pdx (podman)."""
    from pdx.podman import stop as podman_stop

    success, message = podman_stop()
    if success:
        click.echo(message)
    else:
        click.echo(message, err=True)
        sys.exit(1)


@pdx.command()
@click.option("-f", "--follow", is_flag=True, help="Stream logs (like tail -f).")
def logs(follow: bool):
    """Show logs of the Qdrant container (podman)."""
    from pdx.podman import logs as podman_logs

    podman_logs(follow=follow)


def main():
    """Entry point for the pdx console script."""
    pdx()


if __name__ == "__main__":
    main()
