"""
Simple benchmark utility for Contract‑Bot.

Reads `eval_set.csv` (columns: question,answer) and reports accuracy
and P95 latency of the current RAG pipeline.
"""

import csv
import os
import time

import dotenv

from rag_chat import get_chain, ask

dotenv.load_dotenv()

# Instantiate the chain once for all evaluations
_chain = get_chain()


def evaluate(csv_path: str = "eval_set.csv") -> None:
    """
    Run the benchmark.

    Args:
        csv_path: Path to the CSV file containing two columns:
                  `question` and `answer`.
    """
    if not os.path.exists(csv_path):
        print(f"⚠️  {csv_path} not found – nothing to evaluate.")
        return

    total = correct = 0
    latencies: list[float] = []

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            total += 1
            question, expected = row["question"], row["answer"].lower()

            start = time.time()
            actual, _ = ask(_chain, question, [])
            latencies.append(time.time() - start)

            if expected in actual.lower():
                correct += 1

    if total == 0:
        print("⚠️  Empty evaluation file.")
        return

    latencies.sort()
    p95_latency = latencies[int(0.95 * len(latencies)) - 1]
    accuracy = correct / total

    print(f"Accuracy : {correct}/{total} = {accuracy:.2%}")
    print(f"P95 time : {p95_latency:.2f}s")


if __name__ == "__main__":
    evaluate()