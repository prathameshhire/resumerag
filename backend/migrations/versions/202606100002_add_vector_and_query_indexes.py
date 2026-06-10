"""add vector and query indexes

Revision ID: 202606100002
Revises: 202605290001
Create Date: 2026-06-10 00:00:00.000000

Why HNSW over IVFFlat
---------------------
IVFFlat partitions the vector space into centroid lists at build time. Two
consequences matter here:

  1. It requires a VACUUM (or at least a table scan) after every significant
     batch of inserts to keep recall from degrading — an operational burden on
     a local app that grows organically.

  2. It must be built with a minimum number of rows already present; creating
     the index on an empty table and then inserting rows produces poor recall
     until you REINDEX.

HNSW (Hierarchical Navigable Small World) builds incrementally as rows are
inserted, delivers better recall at comparable query latency for tables up to
a few million rows, and requires no post-build maintenance. Those properties
make it a better default for a local-first app where the vector count grows
continuously and there is no DBA running scheduled maintenance.

Parameter choices
-----------------
  m = 16            Connections per node per layer.  pgvector default; suitable
                    for up to ~1M vectors.  Higher m → more RAM, better recall.
  ef_construction = 64
                    Beam width during index construction.  pgvector default.
                    Higher value → slower build, marginally better recall.

Both values can be tuned upward if recall needs to improve as the corpus grows.

Supporting B-tree indexes
-------------------------
The retrieval query filters on documents.source_type and documents.category,
and fetches chunks ordered by (document_id, chunk_index).  Without B-tree
indexes those predicates cause seq-scans even when the vector scan is fast.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "202606100002"
down_revision: Union[str, None] = "202605290001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Approximate nearest-neighbour index on chunk embeddings.
    # The cosine operator class matches the `1 - (embedding <=> query)` similarity
    # expression used in retrieval_service.py.
    op.execute(
        """
        CREATE INDEX idx_chunks_embedding
        ON chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )

    # Composite index for ordered chunk retrieval within a document.
    # Used when listing all chunks belonging to a specific document in index order.
    op.create_index(
        "idx_chunks_document_id_chunk_index",
        "chunks",
        ["document_id", "chunk_index"],
    )

    # Single-column indexes on the two filter columns threaded through every
    # retrieval query (see retrieval_service.py WHERE clause construction).
    op.create_index("idx_documents_source_type", "documents", ["source_type"])
    op.create_index("idx_documents_category", "documents", ["category"])


def downgrade() -> None:
    op.drop_index("idx_documents_category", table_name="documents")
    op.drop_index("idx_documents_source_type", table_name="documents")
    op.drop_index("idx_chunks_document_id_chunk_index", table_name="chunks")
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding")
