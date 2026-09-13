from validate_knowledge_base import validate


def test_phase_one_knowledge_corpus_is_valid():
    assert validate() == []