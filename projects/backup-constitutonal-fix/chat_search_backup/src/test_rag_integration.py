#!/usr/bin/env python3
"""Test RAG integration dependencies and functionality"""

import logging
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Add CSF NIP src/lib to path
csf_nip_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))

def test_rag_dependencies():
    """Test if all RAG dependencies are available and functional"""
    print("🔍 Testing RAG Integration Dependencies")
    print("=" * 50)

    # Test 1: Core RAG components
    print("\n1. Testing Core RAG Components...")
    try:
        from hybrid_searcher import HybridSearcherFactory
        from simple_chunker import ConversationChunkerFactory
        print("✅ RAG components imported successfully")
    except ImportError as e:
        print(f"❌ RAG component import failed: {e}")
        return False

    # Test 2: Core utilities
    print("\n2. Testing Core Utilities...")
    try:
        from lib.core_utils.embedding_manager import ComponentManager
        from lib.core_utils.vector_store import VectorStore
        print("✅ Core utilities imported successfully")
    except ImportError as e:
        print(f"❌ Core utilities import failed: {e}")
        print("   This suggests missing dependencies in src/lib/")
        return False

    # Test 3: PyTorch availability
    print("\n3. Testing PyTorch...")
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__} available")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   CUDA device: {torch.cuda.get_device_name()}")
    except ImportError:
        print("❌ PyTorch not available - RAG will use CPU fallback")
        # This is not fatal, we can still use CPU

    # Test 4: NumPy
    print("\n4. Testing NumPy...")
    try:
        import numpy as np
        print(f"✅ NumPy {np.__version__} available")
    except ImportError:
        print("❌ NumPy not available - This is required for RAG")
        return False

    # Test 5: Sentence Transformers
    print("\n5. Testing Sentence Transformers...")
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ Sentence Transformers available")

        # Test model loading
        try:
            model = SentenceTransformer('all-mpnet-base-v2')
            print("✅ Model 'all-mpnet-base-v2' can be loaded")
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            return False
    except ImportError:
        print("❌ Sentence Transformers not available")
        print("   Install with: pip install sentence-transformers")
        return False

    # Test 6: Vector database
    print("\n6. Testing Vector Database...")
    try:
        # Try to create vector store
        vector_store = ComponentManager.get_vector_store()
        print("✅ Vector store can be initialized")

        # Test basic functionality
        test_embedding = [0.1] * 768  # Dummy embedding
        vector_store.add_vectors(
            embeddings=[test_embedding],
            payloads=[{"test": "data"}],
            ids=["test_id"]
        )
        print("✅ Can add vectors to store")

        # Test search
        results = vector_store.search(test_embedding, limit=1)
        print("✅ Can search vectors in store")

    except Exception as e:
        print(f"❌ Vector database test failed: {e}")
        print("   This could be due to missing FAISS or other vector DB")
        return False

    return True

def test_rag_functionality():
    """Test actual RAG functionality with sample data"""
    print("\n🧪 Testing RAG Functionality")
    print("=" * 30)

    try:
        from hybrid_searcher import HybridSearcherFactory
        from simple_chunker import ConversationChunkerFactory

        # Create sample data
        sample_documents = [
            {
                "text": "Error occurred while processing user input. The system failed to validate the input parameters.",
                "metadata": {"type": "error", "timestamp": "2025-01-15T10:30:00"}
            },
            {
                "text": "Successfully implemented the new feature for user authentication. All tests are passing.",
                "metadata": {"type": "success", "timestamp": "2025-01-15T11:00:00"}
            },
            {
                "text": "The database connection is timing out. Need to optimize the query performance.",
                "metadata": {"type": "performance", "timestamp": "2025-01-15T11:30:00"}
            }
        ]

        # Test chunker
        print("\n1. Testing Conversation Chunker...")
        chunker = ConversationChunkerFactory.create_default_chunker()

        sample_entry = {
            "display": sample_documents[0]["text"],
            "timestamp": 1642248600000,  # Sample timestamp
            "project": "test_project"
        }

        chunks = chunker.chunk_conversation_entry(sample_entry)
        print(f"✅ Created {len(chunks)} chunks from sample entry")

        # Test hybrid searcher
        print("\n2. Testing Hybrid Searcher...")
        searcher = HybridSearcherFactory.create_default_searcher()

        # Add documents
        doc_ids = searcher.add_documents(sample_documents)
        print(f"✅ Added {len(doc_ids)} documents to hybrid index")

        # Test search
        results = searcher.search("error", limit=2)
        print(f"✅ Search for 'error' returned {len(results)} results")

        if results:
            print("   Sample result:")
            result = results[0]
            print(f"     Score: {result['combined_score']:.3f}")
            print(f"     Source: {result['source']}")
            print(f"     Text: {result['text'][:100]}...")

        # Test statistics
        stats = searcher.get_statistics()
        print(f"✅ Got statistics: {stats['total_documents']} documents indexed")

        return True

    except Exception as e:
        print(f"❌ RAG functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 CHS RAG Integration Test")
    print("=" * 40)

    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Test dependencies
    deps_ok = test_rag_dependencies()

    if not deps_ok:
        print("\n❌ Dependency tests failed - RAG integration not ready")
        print("\n🔧 To fix RAG integration:")
        print("1. Install missing Python packages:")
        print("   pip install sentence-transformers torch numpy")
        print("2. Ensure vector database (FAISS/ChromaDB) is available")
        print("3. Check src/lib/core_utils/ components are properly implemented")
        return

    print("\n✅ All dependencies available - testing functionality...")

    # Test functionality
    func_ok = test_rag_functionality()

    if func_ok:
        print("\n🎉 RAG Integration Test PASSED")
        print("✅ RAG components are functional and ready for use")
        print("✅ Semantic search should work in CHS")
    else:
        print("\n❌ RAG Integration Test FAILED")
        print("🔧 Check the error messages above for specific issues")

if __name__ == "__main__":
    main()
