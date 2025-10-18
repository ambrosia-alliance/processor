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
            if sample.ensemble_prediction:
                self._label_sample(sample, sample.ensemble_prediction)
                self.console.print("[green]✓ Accepted ensemble prediction[/green]")
                return "labeled"
            else:
                self.console.print("[yellow]No ensemble prediction available[/yellow]")
                return "skipped"

        elif choice == "change":
            label = self._get_category_selection()
            if label:
                self._label_sample(sample, label)
                self.console.print(f"[green]✓ Labeled as: {label}[/green]")
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

        panel_content += f"[cyan]Ensemble Prediction:[/cyan] {sample.ensemble_prediction}\n"
        panel_content += f"[cyan]Confidence:[/cyan] {sample.confidence:.2%}\n"
        panel_content += f"[cyan]Entropy:[/cyan] {sample.entropy:.3f}\n"
        panel_content += f"[cyan]Agreement:[/cyan] {sample.agreement_score:.2%}\n\n"

        if sample.model_predictions:
            panel_content += "[cyan]Individual Model Votes:[/cyan]\n"
            for model, prediction in sample.model_predictions.items():
                model_short = model.split('/')[-1][:30]
                panel_content += f"  • {model_short}: {prediction}\n"

        panel = Panel(panel_content, title="Sample Review", border_style="blue")
        self.console.print(panel)

    def _get_category_selection(self) -> Optional[str]:
        self.console.print("\n[cyan]Select category:[/cyan]")

        for idx, category in enumerate(self.categories, 1):
            self.console.print(f"  {idx}. {category}")

        choice = Prompt.ask(
            "Enter number",
            choices=[str(i) for i in range(1, len(self.categories) + 1)]
        )

        return self.categories[int(choice) - 1]

    def _label_sample(self, sample: LabeledSample, label: str):
        self.db.update_sample(sample.id, label, needs_review=False)

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
                        ensemble_prediction=category,
                        human_label=None,
                        confidence=1.0,
                        entropy=0.0,
                        agreement_score=1.0,
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

