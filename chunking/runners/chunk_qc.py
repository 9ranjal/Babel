import os
import glob
import argparse

from chunking.core.analysis.qa_utils import (
    load_chunks, compute_metrics, save_sample, save_flagged_json, 
    export_flagged_csv, save_metrics_json, save_summary_md,
    analyze_semantic_types_histogram, print_semantic_summary, save_semantic_analysis
)

def get_latest_chunk_file(input_dir: str) -> str:
    """Get the latest chunk file from a directory."""
    files = glob.glob(os.path.join(input_dir, "*_chunks_*.json"))
    if not files:
        raise FileNotFoundError(f"No chunk files found in {input_dir}")
    return max(files, key=os.path.getctime)

# Removed duplicate functions - now imported from chunking.core.qa_utils
    
    print(f"\n📊 Semantic Types Analysis")
    print(f"Total chunks: {total_chunks}")
    print(f"Usable chunks: {summary['usable_chunks']}")
    print(f"Omitted chunks: {summary['omitted_chunks']} ({summary['omission_rate']}%)")
    
    print(f"\n🔍 Primary Types (Top 10):")
    for primary_type, count in Counter(primary_types).most_common(10):
        percentage = round(count / total_chunks * 100, 1)
        print(f"  {primary_type}: {count} ({percentage}%)")
    
    print(f"\n🏷️  Secondary Types (Top 10):")
    for secondary_type, count in Counter(secondary_types).most_common(10):
        percentage = round(count / total_chunks * 100, 1)
        print(f"  {secondary_type}: {count} ({percentage}%)")
    
    print(f"\n🌍 Domains (Top 10):")
    for domain, count in Counter(domains).most_common(10):
        percentage = round(count / total_chunks * 100, 1)
        print(f"  {domain}: {count} ({percentage}%)")
    
    print(f"\n🧠 Cognitive Levels (Top 10):")
    for cognitive, count in Counter(cognitive_levels).most_common(10):
        percentage = round(count / total_chunks * 100, 1)
        print(f"  {cognitive}: {count} ({percentage}%)")

# Removed duplicate functions - now imported from chunking.core.qa_utils

def main() -> None:
    parser = argparse.ArgumentParser(description="Chunk QA Pipeline (Markdown/Excel)")
    parser.add_argument("--input_dir", type=str, required=True, help="Directory containing chunked JSON files")
    parser.add_argument("--qa_dir", type=str, required=True, help="Directory to save QA outputs")
    parser.add_argument("--semantic_only", action="store_true", help="Only run semantic analysis")
    args = parser.parse_args()

    os.makedirs(args.qa_dir, exist_ok=True)
    history_dir = os.path.join(args.qa_dir, "metrics_history")
    os.makedirs(history_dir, exist_ok=True)

    input_path = get_latest_chunk_file(args.input_dir)
    chunks = load_chunks(input_path)
    
    # Semantic analysis
    semantic_json_path = os.path.join(args.qa_dir, "semantic_analysis.json")
    histogram_data = analyze_semantic_types_histogram(chunks)
    save_semantic_analysis(histogram_data, semantic_json_path)
    print_semantic_summary(histogram_data)
    
    if args.semantic_only:
        print("\n✅ Semantic analysis complete.")
        return
    
    # Regular QA pipeline
    sample_path = os.path.join(args.qa_dir, "chunk_sample.json")
    summary_md_path = os.path.join(args.qa_dir, "chunk_summary.md")
    summary_json_path = os.path.join(args.qa_dir, "chunk_metrics.json")
    flagged_json_path = os.path.join(args.qa_dir, "chunks_flagged.json")
    csv_path = os.path.join(args.qa_dir, "chunk_qc.csv")

    metrics = compute_metrics(chunks)

    save_summary_md(metrics, summary_md_path)
    save_metrics_json(metrics, summary_json_path, history_dir)
    save_sample(chunks, sample_path)
    save_flagged_json(chunks, flagged_json_path)
    export_flagged_csv(chunks, csv_path)

    print("\n✅ All QA exports complete.")

if __name__ == "__main__":
    main() 