"""Unit tests for domain models."""

from src.domain.models import Chunk, EnhancedQuery, QueryIntent, RetrievalResult, SynthesisResult


def test_chunk_creation():
    chunk = Chunk(text="test", metadata={"source": "htb-box"})
    assert chunk.score == 0.0
    assert chunk.rank == 0
    assert chunk.rrf_score == 0.0
    assert chunk.ce_score is None
    assert chunk.text == "test"
    assert chunk.metadata == {"source": "htb-box"}


def test_retrieval_result_with_manifest():
    result = RetrievalResult(
        chunks=[],
        graph_hits={},
        query="test",
        filters_applied={},
        manifest=[{"machine": "Box", "os": "linux"}],
    )
    assert result.manifest is not None
    assert len(result.manifest) == 1
    assert result.manifest[0]["machine"] == "Box"
    assert result["manifest"] == [{"machine": "Box", "os": "linux"}]
    assert result.to_dict()["manifest"] == [{"machine": "Box", "os": "linux"}]


def test_retrieval_result_dict_access():
    result = RetrievalResult(
        chunks=[{"text": "sample"}],
        graph_hits={"categories": ["Active Directory"]},
        query="kerberos",
        filters_applied={"os": "windows"},
    )
    assert result["graph"] == {"categories": ["Active Directory"]}
    assert result.get("graph_hits") == {"categories": ["Active Directory"]}
    assert "chunks" in result
    assert result.get("nonexistent", "fallback") == "fallback"
    assert len(result.keys()) >= 5
    assert len(result.items()) >= 5


def test_synthesis_result():
    res = SynthesisResult(
        answer="Exploit with EternalBlue",
        sources=["htb-blue"],
        chunks_used=3,
        graph_used=True,
        provider="groq",
    )
    assert res.answer == "Exploit with EternalBlue"
    assert res.sources == ["htb-blue"]
    assert res.chunks_used == 3
    assert res.graph_used is True
    assert res.provider == "groq"


def test_enhanced_query():
    eq = EnhancedQuery(
        query="privesc",
        expanded_query="privesc suid sudo",
        expanded_terms=["suid", "sudo"],
        target_os="linux",
        query_scope="broad",
        target_phase="privesc",
        difficulty=None,
    )
    assert eq.query == "privesc"
    assert eq.query_scope == "broad"
    assert eq.target_os == "linux"
    assert eq.target_phase == "privesc"
    assert len(eq.expanded_terms) == 2


def test_query_intent():
    intent = QueryIntent(
        os="windows",
        difficulty="easy",
        query_type="structured",
        phase="foothold",
        scope="specific",
    )
    assert intent.os == "windows"
    assert intent.difficulty == "easy"
    assert intent.query_type == "structured"
