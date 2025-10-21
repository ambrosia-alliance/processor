import argparse
import sys
import os

from app.config import settings
from app.database.schema import initialize_database
from app.labeling.sample_collector import SampleCollector
from app.labeling.cli_labeler import CLILabeler


def main():
    parser = argparse.ArgumentParser(description="Label therapy classification data")
    parser.add_argument('input_file', nargs='?', help='Text file to extract samples from')
    parser.add_argument('--db', default=settings.db_path, help='Database path')
    parser.add_argument('--batch-size', type=int, default=50, help='Number of samples to label in session')
    parser.add_argument('--collect-only', action='store_true', help='Only collect samples, do not label')

    args = parser.parse_args()

    initialize_database(args.db)

    if args.input_file:
        if not os.path.exists(args.input_file):
            print(f"Error: File '{args.input_file}' not found")
            sys.exit(1)

        print(f"Collecting samples from {args.input_file}...")
        collector = SampleCollector(args.db)
        num_samples = collector.collect_from_file(args.input_file)
        print(f"Collected {num_samples} samples\n")

        if args.collect_only:
            print("Collection complete. Use 'python label.py' to start labeling.")
            return

    labeler = CLILabeler(args.db)
    labeler.start_labeling_session(batch_size=args.batch_size)


if __name__ == "__main__":
    main()

