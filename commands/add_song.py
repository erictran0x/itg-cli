import json
import os
import shutil
import sys
import simfile
from tempfile import TemporaryDirectory
from simfile.types import Simfile
from .utils.download_file import download_file
from .utils.add_utils import (
    get_charts_string,
    move_to_temp,
    find_simfile_dirs,
    delete_macos_files,
    print_simfile_data,
    prompt_overwrite,
)
from config import settings

TEMP = TemporaryDirectory()
SINGLES = settings.singles
CACHE = settings.cache


def print_simfile_choices(simfiles: list[Simfile], jsonOutput=False) -> None:
    total = len(simfiles)
    if jsonOutput:
        simfileDict = []
        for i, sm in enumerate(simfiles):
            simfile = {
                "index": i + 1,
                "title": sm.title,
                "artist": sm.artist,
                "charts": get_charts_string(sm, difficulty_labels=True),
            }
            simfileDict.append(simfile)
        print(json.dumps(simfileDict, indent=4))
    else:
        for i, sm in enumerate(simfiles):
            # format chart list output
            charts = get_charts_string(sm, difficulty_labels=True)
            charts = str(charts).replace("'", "")
            indent = len(str(total)) - len(str(i + 1))
            chartIndent = len(str(total)) + 3
            print(
                " " * indent + f"[{i+1}] {sm.title} - {sm.artist}",
                " " * chartIndent + f"{charts}",
                sep="\n",
            )


def add_song(args):
    # download file if URL
    if args.path.startswith("http"):
        path = download_file(args.path)
        # print("path to download:", path)
    else:
        path = os.path.abspath(args.path)
    
    if os.path.exists(path) is False:
        raise Exception("Invalid path:", path)
    move_to_temp(path, TEMP)

    # identify simfile
    print("Searching for valid simfiles...")
    sm_dirs = find_simfile_dirs(TEMP)
    if len(sm_dirs) == 0:
        raise Exception("No valid simfiles found")
    elif len(sm_dirs) == 1:
        root = sm_dirs[0]
    else:
        # TODO: Exit in this case
        print("Prompt: Multiple valid simfiles found:")
        found_simfiles: list[Simfile] = []
        found_simfile_paths: list[str] = []
        for sm_dir in sm_dirs:
            try:
                found_simfiles.append(simfile.opendir(sm_dir, strict=False)[0])
                found_simfile_paths.append(sm_dir)
            except Exception as e:
                print(f"Error reading simfile in {sm_dir}: {e}")
                continue
        print_simfile_choices(found_simfiles)
        total = len(found_simfiles)
        while True:
            print(f"Please choose a simfile to add [1-{total}]: ", end="")
            choice = input()
            if choice.isdigit() and int(choice) < total + 1 and int(choice) > 0:
                # print(sm_dirs)
                print(f"Chosen dir: {sm_dirs[int(choice) - 1]}")
                root = found_simfile_paths[int(choice) - 1]
                break
            else:
                print("Invalid choice. Please choose again.")

    print("Moving song to singles folder...")

    if settings.delete_macos_files:  # delete macos files if enabled
        delete_macos_files(root)

    # rename folder to zip name if no containing folder
    if root == TEMP:
        # TODO: Test if this works. Is importing from archive the only way this can happen?
        # What about other archive formats? (rar, 7z, etc.)
        # TODO: Consider using sm file name instead? Or sm.title?
        zip_name = os.path.basename(path).replace(".zip", "")
        if zip_name == "":
            # use name of .ssc or .sm file if no zip_name
            for file in os.listdir(root):
                if file.endswith(".ssc") or file.endswith(".sm"):
                    zip_name = file.replace(".ssc", "").replace(".sm", "")
                    break
        new_root = os.path.join(TemporaryDirectory(), zip_name)
        shutil.move(root, new_root)
        root = new_root

    # check if song folder already exists in singles folder
    dest = os.path.join(SINGLES, os.path.basename(root))
    if os.path.exists(dest):
        if "overwrite" not in args:
            # TODO: output a diff of simfile metadata
            if settings.delete_macos_files:  # delete macos files if enabled
                delete_macos_files(dest)

            print("Prompt: A folder with the same name already exists.")
            sm_old = simfile.opendir(dest, strict=False)[0]
            print_simfile_data(sm_old, "Old Simfile")
            sm_new = simfile.opendir(root, strict=False)[0]
            print_simfile_data(sm_new, "New Simfile")
            prompt_overwrite("simfile")

        shutil.rmtree(dest)
        # Also delete cache entry if chache is supplied in config
        if CACHE != "":
            song_folder_name = os.path.basename(root)
            singles_packname = os.path.basename(os.path.normpath(SINGLES))
            cache_entry_name = f"Songs_{singles_packname}_{song_folder_name}"
            cache_entry = os.path.join(CACHE, "Songs", cache_entry_name)
            if os.path.exists(cache_entry):
                os.remove(cache_entry)
            else:
                print("Warning: Cache entry not found. Skipping.")

    # Move the song to the singles folder
    shutil.move(root, dest)
    try:
        sm = simfile.opendir(dest)[0]
    except Exception as e:
        if e.__class__.__name__ == "MSDParseError":
            print(
                "Warning: Simfile is malformed. Proceeding with unstrict parsing.",
                file=sys.stderr,
            )
            sm = simfile.opendir(dest, strict=False)[0]
        else:
            raise e
    print_simfile_data(sm, "Song added successfully")
