from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.progress import Progress
from app.storage.database import LabelingDatabase
from app.storage.schemas import LabeledSample
from app.pipeline.accuracy_tracker import AccuracyTracker
from app.config import settings


class LabelingSystem:
    def __init__(self, database: LabelingDatabase = None):
        self.db = database or LabelingDatabase()
        self.tracker = AccuracyTracker(self.db)
        self.console = Console()
        self.categories = settings.categories

    def start_labeling_session(self, batch_size: int = 10):
        self.console.print("\n[bold cyan]Starting Labeling Session[/bold cyan]")
        self.console.print(f"Batch size: {batch_size}\n")

        samples = self.db.get_samples_needing_review(limit=batch_size)

        if not samples:
            self.console.print("[yellow]No samples need review![/yellow]")
            return

        self.console.print(f"[green]Found {len(samples)} samples to review[/green]\n")

        labeled_count = 0
        skipped_count = 0

        for idx, sample in enumerate(samples, 1):
            self.console.print(f"\n[bold]Sample {idx}/{len(samples)}[/bold]")

            action = self._review_sample(sample)

            if action == "labeled":
                labeled_count += 1
            elif action == "skipped":
                skipped_count += 1
            elif action == "quit":
                break

        self._print_session_summary(labeled_count, skipped_count)

    def _review_sample(self, sample: LabeledSample) -> str:
        self._display_sample(sample)

        choice = Prompt.ask(
            "\n[cyan]Action[/cyan]",
            choices=["accept", "change", "skip", "quit"],
            default="accept"
        )

        if choice == "accept":
            if sample.ensemble_predictions:
                self._label_sample(sample, sample.ensemble_predictions)
                self.console.print(f"[green]✓ Accepted: {', '.join(sample.ensemble_predictions)}[/green]")
                return "labeled"
            else:
                self.console.print("[yellow]No ensemble predictions available[/yellow]")
                return "skipped"

        elif choice == "change":
            labels = self._get_multi_category_selection()
            if labels:
                self._label_sample(sample, labels)
                self.console.print(f"[green]✓ Labeled as: {', '.join(labels)}[/green]")
                return "labeled"
            return "skipped"

        elif choice == "skip":
            self.console.print("[yellow]Skipped[/yellow]")
            return "skipped"

        elif choice == "quit":
            self.console.print("[red]Exiting session[/red]")
            return "quit"

        return "skipped"

    def _display_sample(self, sample: LabeledSample):
        panel_content = f"[bold white]{sample.sentence}[/bold white]\n\n"

        predictions_str = ', '.join(sample.ensemble_predictions) if sample.ensemble_predictions else "None"
        panel_content += f"[cyan]Ensemble Predictions:[/cyan] {predictions_str}\n"
        panel_content += f"[cyan]Confidence:[/cyan] {sample.confidence:.2%}\n"
        panel_content += f"[cyan]Entropy:[/cyan] {sample.entropy:.3f}\n"

        if sample.agreement_scores:
            panel_content += f"[cyan]Agreements:[/cyan]\n"
            for label, score in sample.agreement_scores.items():
                panel_content += f"  • {label}: {score:.2%}\n"
        panel_content += "\n"

        if sample.model_predictions:
            panel_content += "[cyan]Individual Model Votes:[/cyan]\n"
            for model, predictions in sample.model_predictions.items():
                model_short = model.split('/')[-1][:30]
                preds_str = ', '.join(predictions) if isinstance(predictions, list) else str(predictions)
                panel_content += f"  • {model_short}: {preds_str}\n"

        panel = Panel(panel_content, title="Sample Review", border_style="blue")
        self.console.print(panel)

    def _get_multi_category_selection(self) -> List[str]:
        self.console.print("\n[cyan]Select categories (comma-separated numbers):[/cyan]")

        for idx, category in enumerate(self.categories, 1):
            self.console.print(f"  {idx}. {category}")

        choice = Prompt.ask("Enter numbers (e.g., 1,3,5)")

        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected = [self.categories[i] for i in indices if 0 <= i < len(self.categories)]
            return selected
        except:
            self.console.print("[red]Invalid input[/red]")
            return []

    def _label_sample(self, sample: LabeledSample, labels: List[str]):
        self.db.update_sample(sample.id, labels, needs_review=False)

        updated_sample = self.db.get_sample_by_id(sample.id)
        self.tracker.update_metrics(updated_sample)

    def _print_session_summary(self, labeled: int, skipped: int):
        self.console.print("\n" + "="*60)
        self.console.print("[bold cyan]Session Summary[/bold cyan]")
        self.console.print(f"  Labeled: [green]{labeled}[/green]")
        self.console.print(f"  Skipped: [yellow]{skipped}[/yellow]")
        self.console.print("="*60 + "\n")

    def display_stats(self):
        stats = self.db.get_stats()

        table = Table(title="Database Statistics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green", justify="right")

        table.add_row("Total Samples", str(stats["total_samples"]))
        table.add_row("Labeled Samples", str(stats["labeled_samples"]))
        table.add_row("Needs Review", str(stats["needs_review"]))
        table.add_row("Unlabeled", str(stats["unlabeled_samples"]))

        self.console.print(table)

    def display_metrics(self):
        summary = self.tracker.get_metrics_summary()

        table = Table(title="Per-Category Metrics", show_header=True)
        table.add_column("Category", style="cyan")
        table.add_column("Samples", justify="right")
        table.add_column("Accuracy", justify="right")
        table.add_column("F1", justify="right")
        table.add_column("Auto-Accept", justify="center")

        for category, metrics in summary["categories"].items():
            auto_accept = "✓" if metrics["can_auto_accept"] else "✗"
            table.add_row(
                category,
                str(metrics["total_samples"]),
                f"{metrics['accuracy']:.2%}",
                f"{metrics['f1_score']:.3f}",
                auto_accept
            )

        self.console.print(table)

        self.console.print(f"\n[cyan]Overall:[/cyan]")
        self.console.print(f"  Auto-accept enabled: {summary['overall']['auto_accept_enabled']}/{len(self.categories)}")
        self.console.print(f"  Still need review: {summary['overall']['needs_review']}")

    def display_category_report(self, category: str):
        report = self.tracker.get_category_report(category)

        self.console.print(f"\n[bold cyan]Report for: {category}[/bold cyan]\n")

        if report["status"] == "no_data":
            self.console.print(f"[yellow]{report['message']}[/yellow]")
            return

        metrics = report["metrics"]

        self.console.print(f"Status: [{'green' if report['status'] == 'ready' else 'yellow'}]{report['status']}[/]")
        self.console.print(f"Total Samples: {metrics['total_samples']}")
        self.console.print(f"Accuracy: {metrics['accuracy']:.2%}")
        self.console.print(f"Precision: {metrics['precision']:.3f}")
        self.console.print(f"Recall: {metrics['recall']:.3f}")
        self.console.print(f"F1 Score: {metrics['f1_score']:.3f}")
        self.console.print(f"Auto-Accept: {'Yes' if metrics['can_auto_accept'] else 'No'}")

        self.console.print(f"\n[cyan]Recommendation:[/cyan] {report['recommendation']}")

    def bulk_label_synthetic(self, synthetic_data: Dict[str, List[str]]):
        self.console.print("\n[bold cyan]Bulk Labeling Synthetic Data[/bold cyan]\n")

        total_samples = sum(len(sentences) for sentences in synthetic_data.values())

        with Progress() as progress:
            task = progress.add_task("[cyan]Processing...", total=total_samples)

            for category, sentences in synthetic_data.items():
                for sentence in sentences:
                    sample = LabeledSample(
                        sentence=sentence,
                        ensemble_predictions=[category],
                        human_labels=[],
                        confidence=1.0,
                        entropy=0.0,
                        agreement_scores={category: 1.0},
                        needs_review=True,
                        source="synthetic"
                    )

                    self.db.insert_sample(sample)
                    progress.update(task, advance=1)

        self.console.print(f"[green]✓ Inserted {total_samples} synthetic samples for review[/green]")

    def auto_accept_ready_categories(self):
        self.console.print("\n[bold cyan]Checking categories for auto-accept...[/bold cyan]\n")

        summary = self.tracker.get_metrics_summary()

        for category, metrics in summary["categories"].items():
            if (metrics["total_samples"] >= settings.min_samples_for_handoff and
                metrics["accuracy"] >= settings.category_accuracy_threshold):

                if settings.human_review_enabled.get(category, True):
                    enable = Confirm.ask(
                        f"Enable auto-accept for [cyan]{category}[/cyan]? "
                        f"(Accuracy: {metrics['accuracy']:.2%}, Samples: {metrics['total_samples']})"
                    )

                    if enable:
                        self.tracker.enable_auto_accept(category)
                        self.console.print(f"[green]✓ Enabled auto-accept for {category}[/green]")

