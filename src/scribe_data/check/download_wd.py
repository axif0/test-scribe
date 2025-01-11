from pathlib import Path
from scribe_data.cli.download import download_wd_lexeme_dump
from scribe_data.utils import DEFAULT_DUMP_EXPORT_DIR


import requests
from rich import print as rprint
from tqdm import tqdm
import os
 


def wd_lexeme_dump_download(wikidata_dump=None, output_dir=None):
    """
    Download Wikidata lexeme dumps without user confirmation if the file does not already exist.

    Parameters
    ----------
    wikidata_dump : str
        Optional date string in YYYYMMDD format for specific dumps.

    output_dir : str
        Optional directory path for the downloaded file.
    """
    dump_url = download_wd_lexeme_dump(wikidata_dump or "latest-lexemes")

    if not dump_url:
        rprint("[bold red]No dump URL found.[/bold red]")
        return False

    output_dir = output_dir or DEFAULT_DUMP_EXPORT_DIR
    os.makedirs(output_dir, exist_ok=True)

    filename = dump_url.split("/")[-1]
    output_path = str(Path(output_dir) / filename)

    # Check if the file already exists
    if os.path.exists(output_path):
        rprint(f"[bold yellow]File already exists: {output_path}. Skipping download.[/bold yellow]")
        return output_path

    # Proceed with the download if the file does not exist
    rprint(f"[bold blue]Downloading dump to {output_path}...[/bold blue]")

    try:
        response = requests.get(dump_url, stream=True)
        total_size = int(response.headers.get("content-length", 0))

        with open(output_path, "wb") as f:
            with tqdm(
                total=total_size, unit="iB", unit_scale=True, desc=output_path
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        print("[bold green]Download completed successfully![/bold green]")

        return output_path

    except requests.exceptions.RequestException as e:
        print(f"[bold red]Error downloading dump: {e}[/bold red]")

    except Exception as e:
        print(f"[bold red]An error occurred: {e}[/bold red]")
 

if __name__ == "__main__":
    output_path = wd_lexeme_dump_download()
    if output_path:
        print(f"DOWNLOAD_PATH={output_path}")
 