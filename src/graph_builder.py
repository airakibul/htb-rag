"""Backward-compatible shim — delegates to src.graph.builder and src.graph.querier."""

from src.graph.builder import (  # noqa: F401
    CANONICAL_TECHNIQUES,
    CATEGORY_KEYWORDS,
    GRAPH_PATH,
    KNOWN_CVE_ALIASES,
    KNOWN_TOOL_ALIASES,
    TECHNIQUE_KEYWORDS,
    TOOL_CATEGORIES,
    _CVE_RE,
    _as_list,
    _categorize,
    _is_technique,
    build_graph,
    load_graph,
    main,
    save_graph,
)
from src.graph.manifest import (  # noqa: F401
    generate_machine_manifest,
    generate_manifest_for_query,
)
from src.graph.querier import (  # noqa: F401
    get_cves_for_machine,
    get_machines_for_technique,
    get_techniques_for_category,
    get_tools_for_machine,
    query_graph,
)

if __name__ == "__main__":
    main()
