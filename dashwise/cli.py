"""
DashWise AI — command-line interface.

    dashwise generate-data --output data/dashboards.json
    dashwise analyze --input data/dashboards.json --output output/analysis_results.json
    dashwise report --input output/analysis_results.json --output output/executive_report.md
    dashwise run          # full pipeline: generate-data -> analyze -> report
"""
import json
import shutil
from pathlib import Path

import click

from dashwise import __version__
from dashwise.datagen import generate as generate_data
from dashwise.pipeline import run as run_pipeline
from dashwise.reporting import write_report

DEFAULT_DASHBOARDS = "data/dashboards.json"
DEFAULT_ANALYSIS = "output/analysis_results.json"
DEFAULT_REPORT = "output/executive_report.md"
# Where the React app reads its data from (so `npm run dev` / the built app
# picks up the freshest analysis automatically).
FRONTEND_DATA = "frontend/public/analysis_results.json"


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="dashwise")
def cli():
    """DashWise AI — BI Dashboard FinOps & Usage Audit."""


@cli.command("generate-data")
@click.option("--output", "-o", default=DEFAULT_DASHBOARDS, show_default=True,
              help="Where to write the synthetic dashboards JSON.")
@click.option("--dashboards", "-n", "n_dashboards", default=12, show_default=True,
              help="Number of dashboards to generate.")
@click.option("--seed", default=42, show_default=True,
              help="Random seed (fixed seed = reproducible output).")
def generate_data_cmd(output, n_dashboards, seed):
    """Generate synthetic dashboards/charts/usage data."""
    data = generate_data(output, n_dashboards=n_dashboards, seed=seed)
    total_charts = sum(len(d["charts"]) for d in data)
    click.echo(f"Generated {len(data)} dashboards with {total_charts} charts -> {output}")


@cli.command("analyze")
@click.option("--input", "-i", "input_path", default=DEFAULT_DASHBOARDS, show_default=True,
              help="Dashboards JSON to analyze.")
@click.option("--output", "-o", default=DEFAULT_ANALYSIS, show_default=True,
              help="Where to write the analysis results JSON.")
def analyze_cmd(input_path, output):
    """Run the SQL / cost / decision agents and write analysis results."""
    if not Path(input_path).exists():
        raise click.ClickException(
            f"Input not found: {input_path}\nRun `dashwise generate-data` first, or pass --input."
        )
    result = run_pipeline(input_path, output)
    click.echo(json.dumps(result["summary"], indent=2, ensure_ascii=False))
    click.echo(f"\nAnalysis written -> {output}")


@cli.command("report")
@click.option("--input", "-i", "input_path", default=DEFAULT_ANALYSIS, show_default=True,
              help="Analysis results JSON to render.")
@click.option("--output", "-o", default=DEFAULT_REPORT, show_default=True,
              help="Where to write the markdown report.")
def report_cmd(input_path, output):
    """Render a human-readable executive report from analysis results."""
    if not Path(input_path).exists():
        raise click.ClickException(
            f"Input not found: {input_path}\nRun `dashwise analyze` first, or pass --input."
        )
    report = write_report(input_path, output)
    click.echo(f"Report written ({len(report)} chars) -> {output}")


@cli.command("run")
@click.option("--dashboards", "-n", "n_dashboards", default=12, show_default=True,
              help="Number of dashboards to generate.")
@click.option("--seed", default=42, show_default=True, help="Random seed.")
def run_cmd(n_dashboards, seed):
    """End-to-end demo: generate data -> analyze -> report -> feed the frontend."""
    click.echo("1/3  Generating synthetic data...")
    data = generate_data(DEFAULT_DASHBOARDS, n_dashboards=n_dashboards, seed=seed)
    total_charts = sum(len(d["charts"]) for d in data)
    click.echo(f"     {len(data)} dashboards / {total_charts} charts -> {DEFAULT_DASHBOARDS}")

    click.echo("2/3  Running analysis pipeline...")
    result = run_pipeline(DEFAULT_DASHBOARDS, DEFAULT_ANALYSIS)
    click.echo(json.dumps(result["summary"], indent=2, ensure_ascii=False))

    click.echo("3/3  Rendering executive report...")
    write_report(DEFAULT_ANALYSIS, DEFAULT_REPORT)
    click.echo(f"     Report -> {DEFAULT_REPORT}")

    # Make the results available to the React dashboard, if it's present.
    frontend_target = Path(FRONTEND_DATA)
    if frontend_target.parent.exists():
        shutil.copyfile(DEFAULT_ANALYSIS, frontend_target)
        click.echo(f"     Frontend data -> {FRONTEND_DATA}")

    click.echo("\nDone. Open the dashboard with:  cd frontend && npm install && npm run dev")


if __name__ == "__main__":
    cli()
