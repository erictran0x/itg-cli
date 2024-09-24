import argparse
from itg_cli import add_pack, add_song, censor, uncensor
from pathlib import Path
from _config import CLISettings, DEFAULT_CONFIG_PATH

subparser_dict = {
    # "subcommand": (
    #     { subcommand kwargs },
    #     { "subcommand arg": { subcommand arg kwargs } }
    # ),
    "add-pack": (
        {"help": "Add a pack from a supplied directory or link"},
        {
            "path": {"help": "path or url to pack"},
            "--overwrite": {
                "help": "skip overwrite confirmation",
                "action": "store_true",
            },
        },
    ),
    "add-song": (
        {"help": "Add a song from a supplied directory or link"},
        {
            "path": {"help": "path or url to song"},
            "--overwrite": {
                "help": "skip overwrite confirmation",
                "action": "store_true",
            },
        },
    ),
    "censor": (
        {"help": "Move a song from the songs folder to the quarantine folder"},
        {"path": {"help": "path to song to quarantine"}},
    ),
    "uncensor": (
        {
            "help": "Displays a list of quarantined songs. Select a song to move back to the songs folder."
        },
        {},
    ),
    "ping": ({"help": "responds with pong :3"}, {}),
}


def process_args(subparser_dict) -> dict[str, str]:
    """
    Builds a parser based off of the command description in `subparser_dict`.
    Parses the arguments that were passed into the program using this parser
    and returns the resulting dictionary.
    """
    parser = argparse.ArgumentParser(description="ITG CLI")
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )
    for subcommand, (kwargs, subcommand_args) in subparser_dict.items():
        subparser = subparsers.add_parser(subcommand, **kwargs)
        for arg, kwargs in subcommand_args.items():
            subparser.add_argument(arg, **kwargs)
    return parser.parse_args()


def main():
    args = process_args(subparser_dict)
    if "config" in args:
        settings = CLISettings.from_toml(args.config)
    elif DEFAULT_CONFIG_PATH.exists():
        settings = CLISettings.from_toml(DEFAULT_CONFIG_PATH)
    else:
        settings = CLISettings(DEFAULT_CONFIG_PATH)

    match args.command:
        case "add-pack":
            add_pack(
                Path(args.path),
                settings.packs,
                settings.courses,
                downloads=settings.downloads,
                overwrite=args.overwrite,
                delete_macos_files_flag=settings.delete_macos_files,
            )
        case "add-song":
            add_song(
                Path(args.path),
                settings.singles,
                settings.cache,
                downloads=settings.downloads,
                overwrite=args.overwrite,
                delete_macos_files_flag=settings.delete_macos_files,
            )
        case "censor":
            censor(Path(args.path), settings.packs, settings.censored, settings.cache)
        case "uncensor":
            uncensor(settings.censored, settings.packs)
        case "ping":
            print("pong")


if __name__ == "__main__":
    main()
