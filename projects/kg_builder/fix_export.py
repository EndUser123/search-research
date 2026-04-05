#!/usr/bin/env python3
"""
Quick fix to handle numpy array serialization for knowledge graph export.
"""

import json
from pathlib import Path

import numpy as np


def convert_numpy_to_list(obj):
    """Convert numpy arrays to lists for JSON serialization."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_to_list(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_list(item) for item in obj]
    else:
        return obj

def fix_knowledge_graph_export():
    """Fix the knowledge graph export by converting numpy arrays to lists."""

    # Load the existing entities data
    entities_file = Path("P:/projects/kg_builder/knowledge_graph_output/entities.json")

    try:
        with open(entities_file, encoding='utf-8') as f:
            entities_data = json.load(f)

        # Convert numpy arrays to lists
        entities_data_fixed = convert_numpy_to_list(entities_data)

        # Save the fixed data
        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump(entities_data_fixed, f, indent=2, ensure_ascii=False)

        print("Successfully fixed entities.json file")

    except Exception as e:
        print(f"Error fixing entities file: {e}")
        # Create a version without embeddings
        try:
            with open(entities_file, encoding='utf-8') as f:
                entities_data = json.load(f)

            # Remove embeddings from all entities
            for entity in entities_data:
                if 'embedding' in entity:
                    del entity['embedding']

            # Save the data without embeddings
            with open(entities_file, 'w', encoding='utf-8') as f:
                json.dump(entities_data, f, indent=2, ensure_ascii=False)

            print("Successfully created entities.json without embeddings")

        except Exception as e2:
            print(f"Error creating entities without embeddings: {e2}")

if __name__ == "__main__":
    fix_knowledge_graph_export()
