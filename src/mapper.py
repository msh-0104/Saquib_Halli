import json
import os

def load_docs_map(config_path="docs-map.json"):
    if not os.path.exists(config_path):
        return {"mappings": []}
    with open(config_path, "r") as f:
        return json.load(f)

def map_changes_to_docs(modified_files, config_path="docs-map.json"):
    config = load_docs_map(config_path)
    mapping_results = {}
    
    for item in config.get("mappings", []):
        src_prefix = item["source_path"]
        target_doc = item["target_doc"]
        
        matched = [f for f in modified_files if f.startswith(src_prefix)]
        if matched:
            if target_doc not in mapping_results:
                mapping_results[target_doc] = []
            mapping_results[target_doc].extend(matched)
            
    return mapping_results
