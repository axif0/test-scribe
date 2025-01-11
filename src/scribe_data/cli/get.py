"""
Functions for getting languages-data types packs for the Scribe-Data CLI.

.. raw:: html
    <!--
    * Copyright (C) 2024 Scribe
    *
    * This program is free software: you can redistribute it and/or modify
    * it under the terms of the GNU General Public License as published by
    * the Free Software Foundation, either version 3 of the License, or
    * (at your option) any later version.
    *
    * This program is distributed in the hope that it will be useful,
    * but WITHOUT ANY WARRANTY; without even the implied warranty of
    * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    * GNU General Public License for more details.
    *
    * You should have received a copy of the GNU General Public License
    * along with this program.  If not, see <https://www.gnu.org/licenses/>.
    -->
"""

import os  # for removing original JSON files
from pathlib import Path
from typing import List, Union

import questionary
from rich import print as rprint

from scribe_data.cli.convert import convert_wrapper
from scribe_data.unicode.generate_emoji_keywords import generate_emoji
from scribe_data.utils import (
    DEFAULT_CSV_EXPORT_DIR,
    DEFAULT_JSON_EXPORT_DIR,
    DEFAULT_SQLITE_EXPORT_DIR,
    DEFAULT_TSV_EXPORT_DIR,
)
from scribe_data.wikidata.query_data import query_data
from scribe_data.wikidata.wikidata_utils import parse_wd_lexeme_dump


def get_data(
    language: str = None,
    data_type: Union[str, List[str]] = None,
    output_type: str = None,
    output_dir: str = None,
    overwrite: bool = False,
    outputs_per_entry: int = None,
    all_bool: bool = False,
    interactive: bool = False,
    identifier_case: str = "camel",
    wikidata_dump: str = None,
) -> None:
    """
    Function for controlling the data get process for the CLI.

    Parameters
    ----------
    language : str
        The language(s) to get.

    data_type : str
        The data type(s) to get.

    output_type : str
        The output file type.

    output_dir : str
        The output directory path for results.

    outputs_per_entry : str
        How many outputs should be generated per data entry.

    overwrite : bool (default: False)
        Whether to overwrite existing files.

    all_bool : bool
        Get all languages and data types.

    interactive : bool (default: False)
        Whether it's running in interactive mode.

    identifier_case : str
        The case format for identifiers. Default is "camel".

    wikidata_dump : str
        The local Wikidata lexeme dump that can be used to process data.

    Returns
    -------
    The requested data saved locally given file type and location arguments.
    """
    # MARK: Defaults

    output_type = output_type or "json"
    if output_dir is None:
        output_dir = {
            "csv": DEFAULT_CSV_EXPORT_DIR,
            "json": DEFAULT_JSON_EXPORT_DIR,
            "sqlite": DEFAULT_SQLITE_EXPORT_DIR,
            "tsv": DEFAULT_TSV_EXPORT_DIR,
        }.get(output_type, DEFAULT_JSON_EXPORT_DIR)

    data_types = [data_type] if data_type else None

    # MARK: Get All

    def prompt_user_download_all():
        """
        Checks with the user if they'd rather use Wikidata lexeme dumps before a download all call.
        """
        return questionary.confirm(
            "Do you want to query Wikidata directly? (selecting 'no' will use Wikidata lexeme dumps)",
            default=False,
        ).ask()

    if all_bool:
        if language:
            if prompt_user_download_all():
                parse_wd_lexeme_dump(
                    language=language,
                    wikidata_dump_type=["form"],
                    data_types=data_types,
                    type_output_dir=output_dir,
                )
            else:
                language_or_sub_language = language.split(" ")[0]
                print(f"Updating all data types for language: {language.title()}")
                query_data(
                    languages=[language_or_sub_language],
                    data_type=None,
                    output_dir=output_dir,
                    overwrite=overwrite,
                )
                print(
                    f"Query completed for all data types for language {language.title()}."
                )

        elif data_type:
            if prompt_user_download_all():
                parse_wd_lexeme_dump(
                    language="all",
                    wikidata_dump_type=["form"],
                    data_types=[data_type],
                    type_output_dir=output_dir,
                )
            else:
                print(f"Updating all languages for data type: {data_type.capitalize()}")
                query_data(
                    languages=None,
                    data_type=[data_type],
                    output_dir=output_dir,
                    overwrite=overwrite,
                )
                print(
                    f"Query completed for all languages for data type {data_type.capitalize()}."
                )

        else:
            print("Updating all languages and data types...")
            rprint(
                "[bold red]Note that the download all functionality must use Wikidata lexeme dumps to observe responsible Wikidata Query Service usage practices.[/bold red]"
            )
            parse_wd_lexeme_dump(
                language="all",
                wikidata_dump_type=["form", "translations"],
                data_types="all",
                type_output_dir=output_dir,
                wikidata_dump_path=wikidata_dump,
            )

    # MARK: Emojis

    elif data_type in {"emoji-keywords", "emoji_keywords"}:
        generate_emoji(language=language, output_dir=output_dir)

    # MARK: Translations

    elif data_type == "translations":
        if language is None:
            language = "all"
        parse_wd_lexeme_dump(
            language=language,
            wikidata_dump_type=["translations"],
            type_output_dir=output_dir,
            wikidata_dump_path=wikidata_dump,
        )
        return

    # MARK: Form Dump

    elif wikidata_dump:
        parse_wd_lexeme_dump(
            language=language,
            wikidata_dump_type=["form"],
            data_types=data_types,
            type_output_dir=output_dir,
            wikidata_dump_path=wikidata_dump,
        )
        return

    # MARK: Query Data

    elif language or data_type:
        language_or_sub_language = language.split(" ")[0]
        data_type = data_type[0] if isinstance(data_type, list) else data_type
        print(
            f"Updating data for language(s): {language.title()}; data type(s): {data_type.capitalize()}"
        )
        existing_files = list(Path(output_dir).glob(f"{language}/{data_type}.json"))
        if existing_files and not overwrite:
            print(
                f"Existing file(s) found for {language.title()} and {data_type.capitalize()} in the {output_dir} directory."
            )
            for idx, file in enumerate(existing_files, start=1):
                print(f"{idx}. {file.name}")

            user_choice = questionary.confirm(
                "Overwrite existing data?", default=False
            ).ask()

            if user_choice:
                print("Overwrite chosen. Removing existing files...")
                for file in existing_files:
                    if file.exists():  # check if the file exists before unlinking
                        file.unlink()
            else:
                print(f"Skipping update for {language.title()} {data_type}.")
                return {"success": False, "skipped": True}

        query_data(
            languages=[language_or_sub_language],
            data_type=data_types,
            output_dir=output_dir,
            overwrite=overwrite,
            interactive=interactive,
        )

        if not all_bool:
            print(f"Updated data was saved in: {Path(output_dir).resolve()}.")

    else:
        raise ValueError(
            "You must provide at least one of the --language (-l) or --data-type (-dt) options, or use --all (-a)."
        )

    # Output Conversion

    json_input_path = Path(output_dir) / f"{language}/{data_type}.json"

    if output_type != "json" and json_input_path.exists():
        convert_wrapper(
            language=language,
            data_type=data_type,
            output_type=output_type,
            input_file=str(json_input_path),
            output_dir=output_dir,
            overwrite=overwrite,
            identifier_case=identifier_case,
        )
        os.remove(json_input_path)
