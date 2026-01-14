import sys
import os
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import scraper

console = Console()

def get_date_input(prompt_text, default=None):
    """Prompts for a date input in DD/MM/YYYY format."""
    while True:
        date_str = Prompt.ask(prompt_text, default=default)
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            console.print("[red]Invalid date format. Please use DD/MM/YYYY.[/red]")

def main():
    console.print(Panel.fit("[bold green]Mandi Price Scraper CLI[/bold green]\n[dim]Interactive Mode[/dim]"))

    # Check for API Key
    api_key = scraper.get_api_key()
    if not api_key:
        console.print("[red]API Key not found. Please set DATA_GOV_IN_API_KEY environment variable.[/red]")
        return

    while True:
        console.print("\n[bold]Step 1: Define Filters[/bold] (Press Enter to skip/leave empty)")
        
        commodity = Prompt.ask("Commodity (e.g. [green]Wheat[/green])").strip() or None
        state = Prompt.ask("State (e.g. [green]Punjab[/green])").strip() or None
        district = Prompt.ask("District (e.g. [green]Agra[/green])").strip() or None
        
        console.print("\n[bold]Step 2: Define Date Range[/bold]")
        use_today = Confirm.ask("Do you want to fetch data for [bold]TODAY[/bold] only?", default=True)
        
        if use_today:
            from_date = datetime.now()
            to_date = datetime.now()
        else:
            from_date = get_date_input("From Date (DD/MM/YYYY)")
            to_date = get_date_input("To Date (DD/MM/YYYY)")

        # Summary
        console.print("\n[bold yellow]Ready to Scrape with:[/bold yellow]")
        console.print(f"Commodity: {commodity or 'All'}")
        console.print(f"State:     {state or 'All'}")
        console.print(f"District:  {district or 'All'}")
        console.print(f"From:      {from_date.strftime('%d/%m/%Y') if from_date else 'Any'}")
        console.print(f"To:        {to_date.strftime('%d/%m/%Y') if to_date else 'Any'}")
        
        if not Confirm.ask("Proceed?", default=True):
            console.print("[yellow]Scrape cancelled.[/yellow]")
            if not Confirm.ask("Do you want to try again?", default=True):
                break
            continue

        # Fetch Data
        records = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="Fetching data...", total=None)
            
            # Since scraper.fetch_data prints to stdout, we might want to suppress it or capture it
            # But normally CLI users might want to see the logs. 
            # We'll just let it print, but the progress bar might get messy.
            # For simplicity in this interactive CLI, we will NOT suppress output,
            # but we'll stop the spinner before calling the main fetch if it's too noisy,
            # or just let it be. Let's redirect stdout to os.devnull ideally if we want a clean TUI-like feel,
            # but the user might want to see debug info.
            # Let's simple call it.
            
            try:
                records = scraper.fetch_data(
                    api_key,
                    commodity=commodity,
                    state=state,
                    district=district,
                    from_date=from_date,
                    to_date=to_date
                )
            except Exception as e:
                console.print(f"[bold red]Error during fetch:[/bold red] {e}")

        # Save Data
        if records:
            console.print(f"\n[bold green]Success![/bold green] Found {len(records)} records.")
            filename = Prompt.ask("Output Filename", default="mandi_prices_master.csv")
            scraper.save_to_csv(records, filename)
        else:
            console.print("\n[bold red]No records found matching your criteria.[/bold red]")

        if not Confirm.ask("\nDo you want to scrape more data?", default=False):
            break
            
    console.print("[bold blue]Goodbye![/bold blue]")

if __name__ == "__main__":
    main()
