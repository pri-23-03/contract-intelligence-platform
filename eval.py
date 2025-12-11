"""Tiered benchmark for accuracy and latency of the RAG pipeline."""

import csv
import logging
import os
import time
from collections import defaultdict
from typing import List, Dict

from rag_chat import get_chain, ask

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def percentile(sorted_vals: List[float], p: float) -> float:
    """Calculate percentile using linear interpolation."""
    if not sorted_vals:
        return 0.0
    n = len(sorted_vals)
    idx = (p / 100) * (n - 1)
    lo, hi = int(idx), min(int(idx) + 1, n - 1)
    return sorted_vals[lo] * (1 - (idx - lo)) + sorted_vals[hi] * (idx - lo)


def check_answer(expected: str, actual: str) -> bool:
    """Check if expected answer is contained in actual response."""
    expected_lower = expected.lower().strip()
    actual_lower = actual.lower().strip()
    
    # Direct containment
    if expected_lower in actual_lower:
        return True
    
    # Handle numeric comparisons (e.g., "$1234.56" vs "1234.56")
    expected_nums = ''.join(c for c in expected_lower if c.isdigit() or c == '.')
    actual_nums = ''.join(c for c in actual_lower if c.isdigit() or c == '.')
    if expected_nums and expected_nums in actual_nums:
        return True
    
    return False


def evaluate(csv_path: str = "eval_set.csv") -> None:
    """Run tiered benchmark and report per-tier metrics."""
    if not os.path.exists(csv_path):
        logger.warning(f"{csv_path} not found.")
        return

    logger.info("Loading chain...")
    chain = get_chain()

    # Track metrics per tier
    results: Dict[str, Dict] = defaultdict(lambda: {
        "total": 0, "correct": 0, "latencies": [], "errors": []
    })

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    total_rows = len(rows)
    logger.info(f"Running {total_rows} questions...")

    for i, row in enumerate(rows):
        question = row["question"]
        expected = row["answer"]
        tier = row.get("tier", "simple")  # Default to simple if no tier column
        
        results[tier]["total"] += 1

        start = time.time()
        try:
            actual, _ = ask(chain, question, [])
            latency = time.time() - start
            results[tier]["latencies"].append(latency)

            if check_answer(expected, actual):
                results[tier]["correct"] += 1
            else:
                results[tier]["errors"].append({
                    "question": question,
                    "expected": expected,
                    "actual": actual[:200] + "..." if len(actual) > 200 else actual
                })
        except Exception as e:
            logger.error(f"Error: {question}: {e}")
            results[tier]["latencies"].append(time.time() - start)
            results[tier]["errors"].append({
                "question": question,
                "expected": expected,
                "actual": f"ERROR: {e}"
            })
        
        # Progress
        if (i + 1) % 20 == 0:
            logger.info(f"  Progress: {i + 1}/{total_rows}")

    # Print results
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    
    all_latencies = []
    total_correct = 0
    total_questions = 0
    
    for tier in ["simple", "calculated", "comparison"]:
        if tier not in results:
            continue
        
        r = results[tier]
        r["latencies"].sort()
        all_latencies.extend(r["latencies"])
        total_correct += r["correct"]
        total_questions += r["total"]
        
        accuracy = r["correct"] / r["total"] if r["total"] > 0 else 0
        p50 = percentile(r["latencies"], 50)
        p95 = percentile(r["latencies"], 95)
        
        print(f"\n{tier.upper()} ({r['total']} questions)")
        print(f"  Accuracy: {r['correct']}/{r['total']} = {accuracy:.1%}")
        print(f"  Latency:  P50={p50:.2f}s, P95={p95:.2f}s")
        
        if r["errors"] and len(r["errors"]) <= 5:
            print(f"  Errors:")
            for err in r["errors"][:3]:
                print(f"    Q: {err['question'][:60]}...")
                print(f"    Expected: {err['expected']}")
                print(f"    Got: {err['actual'][:80]}...")
    
    # Overall
    all_latencies.sort()
    overall_accuracy = total_correct / total_questions if total_questions > 0 else 0
    
    print(f"\n{'=' * 60}")
    print("OVERALL")
    print(f"  Accuracy: {total_correct}/{total_questions} = {overall_accuracy:.1%}")
    print(f"  Latency:  P50={percentile(all_latencies, 50):.2f}s, P95={percentile(all_latencies, 95):.2f}s")
    print("=" * 60)
    
    # Save detailed errors to file
    all_errors = []
    for tier, r in results.items():
        for err in r["errors"]:
            err["tier"] = tier
            all_errors.append(err)
    
    if all_errors:
        with open("eval_errors.json", "w") as f:
            import json
            json.dump(all_errors, f, indent=2)
        print(f"\nDetailed errors saved to eval_errors.json ({len(all_errors)} errors)")


if __name__ == "__main__":
    evaluate()
