import sys
import os
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from demo_data.generate_data import generate_all_demo_data
from core.data_federation import DataFederationHub
from core.quality_scorer import DataQualityScorer

def test():
    print("Generating demo data...")
    start = time.time()
    demo_paths = generate_all_demo_data()
    print(f"Demo data generated in {time.time() - start:.2f} seconds.")
    
    print("\nInitializing federation hub...")
    hub = DataFederationHub()
    for name, path in demo_paths.items():
        hub.ingest_auto(path, source_name=name)
        
    print("\nScoring quality...")
    scorer = DataQualityScorer()
    start_score = time.time()
    reports = scorer.score_all(hub.sources)
    print(f"Scored all sources in {time.time() - start_score:.4f} seconds!")
    
    for name, rpt in reports.items():
        print(f"Source: {rpt.source_name} | Overall Score: {rpt.overall_score:.2f} | Grade: {rpt.grade}")
        print(f"  Null cells: {rpt.null_count} | Duplicates: {rpt.duplicate_count}")
        print(f"  Issues found: {len(rpt.issues)}")

if __name__ == "__main__":
    test()
