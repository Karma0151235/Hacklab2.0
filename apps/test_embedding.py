
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    print("Importing EmbeddingGenerator...")
    from etl.embeddings.generator import EmbeddingGenerator
    print("Initializing Generator...")
    gen = EmbeddingGenerator()
    print("Generating embedding...")
    emb = gen.generate("test")
    print(f"Embedding generated: len={len(emb)}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
