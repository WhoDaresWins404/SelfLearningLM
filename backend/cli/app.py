import typer

app = typer.Typer(name="selflearninglm", help="SelfLearningLM - Intelligent Crawler & Data Processor")


@app.command("serve")
def serve(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the FastAPI web application."""
    import uvicorn
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=reload)


@app.command("seed")
def seed():
    """Run seed data manually."""
    from backend.app.database import init_main_db
    from backend.app.seed import seed_if_empty
    init_main_db()
    seed_if_empty()
    typer.echo("Seed completed.")


@app.command("crawl")
def crawl(domain: str, urls: list[str] = typer.Option(..., "--url", "-u"), max_pages: int = 100):
    """Run a crawl session."""
    from backend.app.crawler.engine import run_spider
    typer.echo(f"Starting crawl for {domain}...")
    run_spider(domain=domain, start_urls=urls, max_pages=max_pages)


@app.command("process")
def process(domain: str = ""):
    """Run the processor pipeline on scraped data."""
    from backend.app.processor.pipeline import run_pipeline
    typer.echo(f"Processing data for {domain or 'all domains'}...")
    run_pipeline(domain=domain)


if __name__ == "__main__":
    app()
