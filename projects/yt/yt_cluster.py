"""
YouTube Transcript Clusterer (Modified - No _COMBINED)
---------------------------
Clusters transcripts into thematic groups using ML
"""

import argparse
import os
import sys

from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# -------------------- CONFIGURATION --------------------
INPUT_FOLDER = "_TXT"
OUTPUT_FOLDER = "_CLUSTER"
FILE_EXTENSION = ".txt"
MODEL_NAME = "all-MiniLM-L6-v2"
# --------------------------------------------------------


def load_combined_files(
    text_path: str,
) -> tuple:  # Renamed parameter to text_path for clarity
    """Load and parse transcript files from TEXT folder"""  # Modified docstring
    all_transcripts = []
    all_filenames = []

    try:
        transcript_files = [  # Renamed variable for clarity
            f
            for f in os.listdir(text_path)  # Changed to text_path
            if f.endswith(FILE_EXTENSION)
        ]

        if not transcript_files:  # Modified condition and message
            print(
                f"No {FILE_EXTENSION} files found in {text_path}"
            )  # Changed to text_path
            sys.exit(1)

        for file in transcript_files:  # Renamed variable
            file_path = os.path.join(text_path, file)  # Changed to text_path
            with open(file_path, encoding="utf-8") as f:
                content = f.read().strip()
                # Assuming each file in _TEXT is a full transcript, not split by "-----"
                all_filenames.append(file.strip())  # Use filename directly
                all_transcripts.append(content)  # Use entire content as transcript

        return all_transcripts, all_filenames

    except Exception as e:
        print(f"Error loading files: {str(e)}")
        sys.exit(1)


def perform_clustering(embeddings, max_clusters=55):
    """Cluster embeddings and return optimal grouping"""
    trial_results = []
    cluster_range = range(3, min(max_clusters, len(embeddings)) + 1)

    for n_clusters in cluster_range:
        print(f"\nTesting {n_clusters} clusters...")
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)

        if len(set(labels)) < 2:
            continue  # Skip invalid cluster counts

        score = silhouette_score(embeddings, labels)
        print(f"Silhouette Score: {score:.3f}")

        trial_results.append(
            {"n_clusters": n_clusters, "score": score, "labels": labels}
        )

    if not trial_results:
        print("No valid clustering results")
        sys.exit(1)

    return max(trial_results, key=lambda x: x["score"])


def main():
    parser = argparse.ArgumentParser(
        description="Cluster transcript files using ML",
        epilog="Example: python yt_cluster.py C:\\TEMP\\_yt\\ChannelName",
    )
    parser.add_argument(
        "channel_folder", help="Channel directory created by workflow.bat"
    )

    args = parser.parse_args()
    channel_folder = os.path.abspath(args.channel_folder.strip('"'))

    # Validate folder structure - Now checking for _TEXT instead of _COMBINED
    text_path = os.path.join(
        channel_folder, INPUT_FOLDER
    )  # INPUT_FOLDER is now "_TEXT"
    cluster_path = os.path.join(channel_folder, OUTPUT_FOLDER)

    if not os.path.exists(text_path):  # Checking for _TEXT folder existence
        print(
            f"Error: Missing {INPUT_FOLDER} folder\nExpected at: {text_path}"
        )  # Modified message
        sys.exit(1)

    os.makedirs(cluster_path, exist_ok=True)

    # Load and process data
    print("Loading transcripts...")
    transcripts, filenames = load_combined_files(text_path)  # Changed to text_path

    print("Generating embeddings...")
    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(transcripts, show_progress_bar=True)

    # Cluster analysis
    print("\nStarting cluster analysis...")
    best_result = perform_clustering(embeddings)

    # Save results
    print(
        f"\nBest clustering: {best_result['n_clusters']} clusters (score: {best_result['score']:.3f})"
    )
    clusters = {}
    for idx, cluster_id in enumerate(best_result["labels"]):
        clusters.setdefault(cluster_id, []).append(filenames[idx])

    for cluster_id, files in clusters.items():
        output_path = os.path.join(
            cluster_path, f"cluster_{cluster_id}_score{best_result['score']:.2f}.txt"
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(files))
        print(f"Saved cluster {cluster_id} ({len(files)} files) to {output_path}")

    print("\nClustering complete!")


if __name__ == "__main__":
    main()
