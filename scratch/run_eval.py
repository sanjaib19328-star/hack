import importlib.util

spec = importlib.util.spec_from_file_location("evaluator", "code/evaluation/main.py")
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)

metrics = evaluator.evaluate_predictions("scratch/test_patched_pred.csv", "dataset/sample_output.csv")
print("Status Accuracy:", f"{metrics['status_accuracy']*100:.2f}% ({metrics['status_matches']}/{metrics['total_cases']})")
print("Exact Sequence Accuracy:", f"{metrics['sequence_accuracy']*100:.2f}% ({metrics['sequence_matches']}/{metrics['total_cases']})")
print("Field-Level Accuracy:", f"{metrics['field_accuracy']*100:.2f}% ({metrics['field_matches']}/{metrics['total_fields']})")
print("Total Mismatches:", len(metrics['mismatches']))
for m in metrics['mismatches'][:10]:
    print("  ", m)
