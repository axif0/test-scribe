# SPDX-License-Identifier: GPL-3.0-or-later
"""
Download Wikidata lexeme dump.
"""
from scribe_data.cli.download import wd_lexeme_dump_download_wrapper

def wd_lexeme_dump_download(wikidata_dump=None, output_dir=None, default=True):
    """
    Download Wikidata lexeme dumps automatically.

    Parameters
    ----------
    wikidata_dump : str, optional
        Date string in YYYYMMDD format for specific dumps.
        If None, downloads the latest dump.

    output_dir : str, optional
        Directory path for the downloaded file.
        If None, uses DEFAULT_DUMP_EXPORT_DIR.

    default : bool, optional
        If True, skips the user confirmation prompt.
        Defaults to True.

    Returns
    -------
    str or False
        Path to downloaded file if successful, False otherwise.

    Notes
    -----
    - Downloads are skipped if the file already exists in the output directory.
    - Progress is displayed every 50MB during download.
    - Creates output directory if it doesn't exist.
    """
    # Directly call wd_lexeme_dump_download_wrapper with default=True to skip questionary prompt
    return wd_lexeme_dump_download_wrapper(wikidata_dump, output_dir, default)


if __name__ == "__main__":
    if output_path := wd_lexeme_dump_download():
        print(f"DOWNLOAD_PATH={output_path}")
