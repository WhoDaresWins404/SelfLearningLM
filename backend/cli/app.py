import typer

app = typer.Typer(name="selflearninglm", help="SelfLearningLM - Intelligent Crawler & Data Processor")


def _ensure_db():
    from backend.app.database import init_main_db, migrate_main_db, init_lake_db
    init_main_db()
    migrate_main_db()
    init_lake_db()


@app.command("serve")
def serve(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the FastAPI web application."""
    import uvicorn
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=reload)


@app.command("crawl")
def crawl(domain: str, urls: list[str] = typer.Option(..., "--url", "-u"), max_pages: int = 100):
    """Run a crawl session."""
    from backend.app.crawler.engine import run_spider
    typer.echo(f"Starting crawl for {domain}...")
    run_spider(domain=domain, start_urls=urls, max_pages=max_pages)


@app.command("process")
def process(domain: str = ""):
    """Run the processor pipeline on scraped data."""
    _ensure_db()
    from backend.processor.pipeline import run_pipeline
    typer.echo(f"Processing data for {domain or 'all domains'}...")
    run_pipeline(domain=domain)


@app.command("backfill-training")
def backfill(domain: str = ""):
    """Generate training data for existing records that don't have it yet."""
    _ensure_db()
    from backend.processor.pipeline import backfill_training_data
    typer.echo(f"Backfilling training data for {domain or 'all domains'}...")
    count = backfill_training_data(domain=domain)
    typer.echo(f"Done. Processed {count} records.")


@app.command("reextract")
def reextract(domain: str = ""):
    """Re-extract content for existing records using updated extractors and regenerate training data."""
    _ensure_db()
    from backend.processor.pipeline import reextract_records
    typer.echo(f"Re-extracting content for {domain or 'all domains'}...")
    count = reextract_records(domain=domain)
    typer.echo(f"Done. Re-extracted {count} records.")


@app.command("cleanup-jsonl")
def cleanup_jsonl(input: str = typer.Argument(..., help="Path to input JSONL file"),
                  output: str = typer.Argument(..., help="Path to output JSONL file")):
    """Clean glued words and code bracket spacing in an exported JSONL file."""
    from backend.processor.cleanup import clean_jsonl_file
    typer.echo(f"Cleaning {input} -> {output}...")
    count = clean_jsonl_file(input, output)
    typer.echo(f"Done. Cleaned {count} records.")


if __name__ == "__main__":
    app()
