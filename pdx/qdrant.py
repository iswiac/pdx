# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 The PDX Project Authors

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


class VDB:
    point_id: int
    cname: str
    client: QdrantClient

    def __init__(
        self,
        cname: str,
        url: str = "http://127.0.0.1:6333",
    ):
        self.point_id = 0
        self.cname = cname
        self.client = QdrantClient(url)

    def init_collection(
        self,
        vsize: int = 768,
        vdist: Distance = Distance.COSINE,
    ) -> None:
        """Create the collection if it does not exist. When it already exists, set point_id to current count for appending."""
        if self.client.collection_exists(self.cname):
            info = self.client.get_collection(self.cname)
            self.point_id = info.points_count or 0
            return

        # create a new collection
        vp = VectorParams(size=vsize, distance=vdist)
        self.client.create_collection(self.cname, vp)

    def delete_collection(self) -> bool:
        """Delete this VDB's collection if it exists. Returns True if deleted, False if it did not exist."""
        if not self.client.collection_exists(self.cname):
            return False
        self.client.delete_collection(self.cname)
        return True

    def upsert(self, **kwargs) -> None:
        self.client.upsert(collection_name=self.cname, **kwargs)

    def upsert_batch(self, vectors, paths, metadatas=None) -> None:
        size = len(paths)
        assert size == len(vectors)

        points = []
        for i in range(size):
            self.point_id += 1
            # Default payload contains the path
            payload = {"path": paths[i]}

            # Merge additional metadata (date, location) if provided
            if metadatas and i < len(metadatas):
                payload.update(metadatas[i])

            points.append(
                PointStruct(
                    id=self.point_id,
                    vector=vectors[i],
                    payload=payload,
                )
            )
        self.upsert(points=points)

    def query_points(self, **kwargs):
        return self.client.query_points(collection_name=self.cname, **kwargs)

    def query_photos(self, query, limit: int, min_score: float = 0.0) -> list[tuple]:
        """Returns (score, path, description) for each result."""
        response = self.query_points(query=query, limit=limit, with_payload=True)
        results = []
        for res in response.points:
            if res.score >= min_score:
                # Catch the AI description from the payload
                desc = res.payload.get("description", "[No description yet]")
                results.append((res.score, res.payload["path"], desc))
        return results

    def update_payload(self, point_id, metadata: dict) -> None:
        """Saves new metadata (like AI descriptions) to a specific point."""
        self.client.set_payload(
            collection_name=self.cname,
            payload=metadata,
            points=[point_id],
        )
