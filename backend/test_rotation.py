import unittest
from unittest.mock import MagicMock, patch
from google.api_core.exceptions import ResourceExhausted

# We must import services and classes we want to test
from services.key_manager import key_manager
from services.testgen_service import generate_test_cases
from services.embedder import add_chunks_to_store, similarity_search, get_embeddings, get_vector_store
from services.rag_pipeline import ask_question

class TestKeyRotation(unittest.TestCase):
    def setUp(self):
        # Save original state of key_manager
        self.original_keys = key_manager.keys
        self.original_current_index = key_manager.current_index
        # Configure with dummy keys for testing
        key_manager.keys = ["key1", "key2", "key3"]
        key_manager.current_index = 0

    def tearDown(self):
        # Restore key_manager state
        key_manager.keys = self.original_keys
        key_manager.current_index = self.original_current_index
        key_manager._clear_caches()

    @patch("google.generativeai.GenerativeModel")
    @patch("google.generativeai.configure")
    def test_testgen_rotation(self, mock_configure, mock_model_class):
        # We want to test that when key1 and key2 are exhausted, we eventually hit key3 and succeed.
        mock_model_1 = MagicMock()
        mock_model_2 = MagicMock()
        mock_model_3 = MagicMock()

        # Mock the models to raise ResourceExhausted for first two keys
        # We raise ResourceExhausted. The Exception constructor needs a message.
        mock_model_1.generate_content.side_effect = ResourceExhausted("Rate limit exceeded on key1")
        mock_model_2.generate_content.side_effect = ResourceExhausted("Rate limit exceeded on key2")

        # Mock success for key3
        mock_response = MagicMock()
        mock_response.text = '{"feature_name": "Test Feature", "positive_tests": ["test1"], "negative_tests": ["test2"], "edge_cases": ["test3"]}'
        mock_model_3.generate_content.return_value = mock_response

        # Setup side effect for GenerativeModel instantiation
        # Whenever GenerativeModel is instantiated, check which key is active and return the corresponding mock model
        def model_side_effect(*args, **kwargs):
            current_key = key_manager.get_key()
            if current_key == "key1":
                return mock_model_1
            elif current_key == "key2":
                return mock_model_2
            elif current_key == "key3":
                return mock_model_3
            raise ValueError(f"Unexpected key: {current_key}")

        mock_model_class.side_effect = model_side_effect

        # Call generate_test_cases. It should rotate twice and succeed on key3.
        result = generate_test_cases("chunk text", "source document")

        self.assertEqual(result["feature_name"], "Test Feature")
        self.assertEqual(key_manager.get_key(), "key3")
        self.assertEqual(key_manager.current_index, 2)
        # Verify configure was called with different keys
        mock_configure.assert_any_call(api_key="key1")
        mock_configure.assert_any_call(api_key="key2")
        mock_configure.assert_any_call(api_key="key3")

    @patch("services.embedder.get_vector_store")
    def test_embedder_add_chunks_rotation(self, mock_get_vector_store):
        mock_store_1 = MagicMock()
        mock_store_2 = MagicMock()
        mock_store_3 = MagicMock()

        mock_store_1.add_texts.side_effect = ResourceExhausted("Rate limit on key1")
        mock_store_2.add_texts.side_effect = ResourceExhausted("Rate limit on key2")
        mock_store_3.add_texts.return_value = ["id1", "id2"]

        # Track store retrieval depending on active key
        def store_side_effect(*args, **kwargs):
            current_key = key_manager.get_key()
            if current_key == "key1":
                return mock_store_1
            elif current_key == "key2":
                return mock_store_2
            elif current_key == "key3":
                return mock_store_3
            raise ValueError(f"Unexpected key: {current_key}")

        mock_get_vector_store.side_effect = store_side_effect

        # Call add_chunks_to_store. It should rotate twice and succeed on key3.
        chunks = [{"text": "chunk1", "doc_id": 1, "filename": "f.txt", "page_num": 1, "chunk_index": 0, "source": "f.txt"}]
        ids = add_chunks_to_store(chunks)

        self.assertEqual(ids, ["id1", "id2"])
        self.assertEqual(key_manager.get_key(), "key3")
        self.assertEqual(key_manager.current_index, 2)

    @patch("services.embedder.get_vector_store")
    def test_embedder_similarity_search_rotation(self, mock_get_vector_store):
        mock_store_1 = MagicMock()
        mock_store_2 = MagicMock()

        mock_store_1.similarity_search_with_score.side_effect = ResourceExhausted("Rate limit on key1")
        mock_store_2.similarity_search_with_score.return_value = [("doc1", 0.9)]

        def store_side_effect(*args, **kwargs):
            current_key = key_manager.get_key()
            if current_key == "key1":
                return mock_store_1
            elif current_key == "key2":
                return mock_store_2
            raise ValueError(f"Unexpected key: {current_key}")

        mock_get_vector_store.side_effect = store_side_effect

        results = similarity_search("query", k=1)
        self.assertEqual(results, [("doc1", 0.9)])
        self.assertEqual(key_manager.get_key(), "key2")
        self.assertEqual(key_manager.current_index, 1)

    @patch("services.rag_pipeline.build_chain")
    def test_rag_pipeline_rotation(self, mock_build_chain):
        mock_chain_1 = MagicMock()
        mock_chain_2 = MagicMock()

        mock_chain_1.invoke.side_effect = ResourceExhausted("Rate limit on key1")
        mock_chain_2.invoke.return_value = {
            "result": "Grounded answer text",
            "source_documents": []
        }

        def chain_side_effect(*args, **kwargs):
            current_key = key_manager.get_key()
            if current_key == "key1":
                return mock_chain_1
            elif current_key == "key2":
                return mock_chain_2
            raise ValueError(f"Unexpected key: {current_key}")

        mock_build_chain.side_effect = chain_side_effect

        result = ask_question("What is the meaning of life?")
        self.assertEqual(result["answer"], "Grounded answer text")
        self.assertEqual(key_manager.get_key(), "key2")
        self.assertEqual(key_manager.current_index, 1)

if __name__ == "__main__":
    unittest.main()
