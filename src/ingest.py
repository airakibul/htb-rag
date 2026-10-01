"""Backward-compatible shim — delegates to src.pipeline.ingest."""

from src.pipeline.ingest import (  # noqa: F401
    _check_collection,
    _get_files,
    _parse_args,
    _store_with_retry,
    _validate_embedder,
    _validate_keys,
    main,
)

if __name__ == "__main__":
    main()
