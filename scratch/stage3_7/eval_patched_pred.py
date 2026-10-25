import sys
import os

sys.path.insert(0, os.path.abspath("."))
from scratch.stage3_5.independent_evaluator import evaluate

res = evaluate("scratch/stage3_7/test_sample_pred.csv", "dataset/sample_output.csv")
print("=== EVALUATION OF ISOLATED PATCHED ENGINE ON SAMPLE (32 CASES) ===")
print(f"Status Accuracy: {res['status_accuracy'][0]}/{res['status_accuracy'][1]} ({res['status_accuracy'][2]*100:.2f}%)")
print(f"Exact Ordered Sequence Accuracy: {res['exact_sequence_accuracy'][0]}/{res['exact_sequence_accuracy'][1]} ({res['exact_sequence_accuracy'][2]*100:.2f}%)")
print(f"Semantic Step Precision: {res['semantic_tp']}/{res['total_pred_steps']} ({res['semantic_precision']*100:.2f}%)")
print(f"Semantic Step Recall: {res['semantic_tp']}/{res['total_truth_steps']} ({res['semantic_recall']*100:.2f}%)")
print(f"Semantic Step F1: {res['semantic_f1']*100:.2f}%")
print(f"Strict Step Precision: {res['strict_tp']}/{res['total_pred_steps']} ({res['strict_precision']*100:.2f}%)")
print(f"Strict Step Recall: {res['strict_tp']}/{res['total_truth_steps']} ({res['strict_recall']*100:.2f}%)")
print(f"Strict Step F1: {res['strict_f1']*100:.2f}%")
print(f"Key-Aligned Field Accuracy: {res['aligned_field_accuracy'][0]}/{res['aligned_field_accuracy'][1]} ({res['aligned_field_accuracy'][2]*100:.2f}%)")
print(f"Semantic Unmatched Predictions (FP): {len(res['sem_unmatched_preds'])}")
print(f"Semantic Unmatched Truths (FN): {len(res['sem_unmatched_truths'])}")
