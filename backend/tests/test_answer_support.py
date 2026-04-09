import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.answer_support import detect_agent_support, detect_chat_support, select_sources_for_support
from services.rag import RAGService


class AnswerSupportTests(unittest.TestCase):
    def test_chat_without_results_is_uncertain(self):
        self.assertEqual(detect_chat_support("I can help.", []), "uncertain")

    def test_chat_uncertain_phrase_is_uncertain(self):
        self.assertEqual(
            detect_chat_support("I am not sure based on the documentation.", [{"source": "a"}]),
            "uncertain",
        )

    def test_chat_with_results_and_supported_answer_is_supported(self):
        self.assertEqual(detect_chat_support("KDAI is a documentation system.", [{"source": "a"}]), "supported")

    def test_agent_with_collected_sources_is_supported(self):
        self.assertEqual(detect_agent_support("Answer", [{"source": "a"}], []), "supported")

    def test_agent_with_insufficient_observation_is_uncertain(self):
        self.assertEqual(
            detect_agent_support("Answer", [], [{"observation": "No relevant documentation found for this query."}]),
            "uncertain",
        )

    def test_uncertain_support_limits_sources_to_three(self):
        sources = [
            {"source": "a", "title": "A"},
            {"source": "b", "title": "B"},
            {"source": "c", "title": "C"},
            {"source": "d", "title": "D"},
        ]
        self.assertEqual(len(select_sources_for_support(sources, "uncertain")), 3)

    def test_source_deduplication_keeps_one_entry_per_file(self):
        sources = [
            {"source": "docker-setup.mdx", "title": "Running All Services"},
            {"source": "docker-setup.mdx", "title": "AI Services"},
            {"source": "quick-start.mdx", "title": "Quick Start"},
        ]
        selected = select_sources_for_support(sources, "supported")

        self.assertEqual(
            selected,
            [
                {"source": "docker-setup.mdx", "title": "Running All Services"},
                {"source": "quick-start.mdx", "title": "Quick Start"},
            ],
        )

    def test_rag_build_sources_keeps_one_entry_per_file(self):
        rag = RAGService()
        results = [
            {"source": "docker-setup.mdx", "title": "Running All Services", "score": 0.9},
            {"source": "docker-setup.mdx", "title": "AI Services", "score": 0.8},
            {"source": "quick-start.mdx", "title": "Quick Start", "score": 0.7},
        ]

        self.assertEqual(
            rag.build_sources(results),
            [
                {"source": "docker-setup.mdx", "title": "Running All Services", "score": 0.9},
                {"source": "quick-start.mdx", "title": "Quick Start", "score": 0.7},
            ],
        )


if __name__ == "__main__":
    unittest.main()
