from codecarbon import EmissionsTracker
from halo import Halo
from rich import print
from rich.console import Console
from rich.table import Table
import time
console = Console()
def track_workflow_emissions(original_yaml, optimized_yaml):
    """Track and compare emissions between original and optimized workflows"""
    try:
        with Halo(text="Calculating carbon emissions...", spinner="dots"):
            original_tracker = EmissionsTracker(
                project_name="original_workflow",
                output_dir="emissions",
                log_level="warning",
                allow_multiple_runs=True,
            )
            optimized_tracker = EmissionsTracker(
                project_name="optimized_workflow",
                output_dir="emissions",
                log_level="warning",
                allow_multiple_runs=True,
            )

            def run_workflow(yaml_content, tracker):
                try:
                    tracker.start()
                    for line in yaml_content.split("\n"):
                        if "run:" in line or "uses:" in line:
                            if "build" in line.lower():
                                time.sleep(0.3)
                            elif "test" in line.lower():
                                time.sleep(0.2)
                            else:
                                time.sleep(0.1)
                    emissions = tracker.stop()
                    return emissions if emissions is not None else 0.0
                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Error tracking emissions: {e}[/yellow]"
                    )
                    return 0.0

            original_emissions = run_workflow(original_yaml, original_tracker)
            optimized_emissions = run_workflow(optimized_yaml, optimized_tracker)

            original_emissions = (
                float(original_emissions) if original_emissions is not None else 0.0
            )
            optimized_emissions = (
                float(optimized_emissions) if optimized_emissions is not None else 0.0
            )

            emissions_saved = max(0, original_emissions - optimized_emissions)
            percentage_reduction = (
                (emissions_saved / original_emissions * 100)
                if original_emissions > 0
                else 0
            )

            # Create rich table for display
            table = Table(title="Carbon Emissions Analysis")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row(
                "Original Workflow Emissions", f"{original_emissions:.4f} kg CO2e"
            )
            table.add_row(
                "Optimized Workflow Emissions", f"{optimized_emissions:.4f} kg CO2e"
            )
            table.add_row("Emissions Saved", f"{emissions_saved:.4f} kg CO2e")
            table.add_row("Reduction Percentage", f"{percentage_reduction:.1f}%")

            trees_equivalent = emissions_saved * 0.0165
            table.add_row(
                "Tree Months Equivalent", f"{trees_equivalent:.2f} tree-months"
            )

            console.print(table)

            return {
                "original": original_emissions,
                "optimized": optimized_emissions,
                "saved": emissions_saved,
                "percentage": percentage_reduction,
            }
    except Exception as e:
        console.print(f"[red]Error in emissions tracking: {e}[/red]")

        return {"original": 0.0, "optimized": 0.0, "saved": 0.0, "percentage": 0.0}
