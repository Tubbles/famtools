#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class FactorioSettings:
    @staticmethod
    def get_default_config_dir() -> str:
        from sys import platform
        import os

        if platform == "linux":
            path = "~/.factorio"
        elif platform == "darwin":
            path = "~/Library/Application Support/factorio"  # TODO : Untested
        elif platform == "win32":
            path = r"%APPDATA%\Factorio"  # TODO : Untested

        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        path = os.path.realpath(path)
        return path

    def __init__(self, config_dir_path: str | None = None):
        self.config_dir_path = config_dir_path

        if not self.config_dir_path:
            self.config_dir_path = FactorioSettings.get_default_config_dir()

    def get_credentials(self) -> dict[str, str]:
        import json

        # TODO : Use a path lib instead
        with open(f"{self.config_dir_path}/player-data.json", "r") as file:
            settings = json.load(file)
        keys = ["service-username", "service-token"]
        return {key.replace("service-", ""): settings[key] for key in settings.keys() if key in keys}


class FactorioMod:
    official_mod_names = ["base", "elevated-rails", "quality", "space-age"]

    @staticmethod
    def download_file_from_url(url: str, outfile_path: str):
        from tqdm import tqdm
        import requests

        response = requests.get(url, stream=True)

        if response.status_code != 200:
            raise Exception(f"Response code is {response.status_code} for {url}")

        with open(outfile_path, "wb") as outfile:
            for data in tqdm(response.iter_content(), desc=outfile_path, dynamic_ncols=True):
                outfile.write(data)

    def __init__(self, name: str, settings: FactorioSettings | None = None):
        import requests
        import json

        self.name = name
        self.settings = settings

        if not self.name:
            raise Exception("Requires name")

        if not self.settings:
            self.settings = FactorioSettings()

        url = f"https://mods.factorio.com/api/mods/{self.name}/full"
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception(f"Response code is {response.status_code} for {url}")

        self._data = json.loads(response.text)

    def get_all_versions(self) -> list[str]:
        from packaging.version import Version

        return sorted([release["version"] for release in self._data["releases"]], key=Version)

    def _version_exists(self, version: str) -> bool:
        return version in self.get_all_versions()

    def get_highest_version(self) -> str:
        return self.get_all_versions()[-1]

    def _check_version(self, version: str | None = None) -> str:
        if not version:
            version = self.get_highest_version()

        if not self._version_exists(version):
            raise Exception(f"Version {version} of {self.name} not found")

        return version

    def get_release_info(self, version: str | None = None) -> dict[str, str]:
        version = self._check_version(version)

        for release in self._data["releases"]:
            if release["version"] == version:
                return release

    def get_sha1(self, version: str | None = None) -> str:
        version = self._check_version(version)

        return self.get_release_info(version)["sha1"]

    def get_download_url(self, version: str | None = None) -> str | None:
        version = self._check_version(version)

        return self.get_release_info(version)["download_url"]

    def download(self, version: str | None = None, output_directory: str | None = None) -> str:
        version = self._check_version(version)

        download_stem = self.get_download_url(version)
        credentials = self.settings.get_credentials()

        dl_url = (
            f"https://mods.factorio.com{download_stem}?username={credentials["username"]}&token={credentials["token"]}"
        )
        outfile_path = f"{self.name}_{version}.zip"
        if output_directory:
            outfile_path = f"{output_directory}/{outfile_path}"

        FactorioMod.download_file_from_url(dl_url, outfile_path)
        return outfile_path

    def exists(self, version: str | None = None, output_directory: str | None = None) -> str:
        import os
        import json

        version = self._check_version(version)

        zip_path = f"{self.name}_{version}.zip"
        if output_directory:
            zip_path = f"{output_directory}/{zip_path}"
        if os.path.isfile(zip_path):
            return True

        dir_path = f"{self.name}_{version}"
        if output_directory:
            dir_path = f"{output_directory}/{dir_path}"
        if os.path.isdir(dir_path):
            return True

        json_path = f"{self.name}/info.json"
        if output_directory:
            json_path = f"{output_directory}/{json_path}"
        if os.path.isfile(json_path):
            with open(json_path, "r") as json_file:
                info = json.load(json_file)
                if "version" in info and info["version"] == version:
                    return True

        return False

    @staticmethod
    def get_mods_from_log(filepath: str) -> dict[str, str]:
        """
        Returns a dict with the keys being the names of the mods in the log, and their values being their versions
        E.g.:
        {"AutoDeconstruct": "1.0.2"}
        """
        import re

        mods = {}
        with open(filepath, "r") as file:
            mod_mentions = [line.strip() for line in file if " Loading mod " in line]
            for mention in mod_mentions:
                groups = re.match(
                    r"(?P<time>[0-9.]+) Loading mod (settings )?(?P<name>[a-zA-Z0-9._-]+) (?P<version>[0-9.]+) \((?P<file>[a-zA-Z0-9._-]+)\)",
                    mention,
                )
                name = groups["name"]
                version = groups["version"]
                if name in mods and mods[name] != version:
                    raise Exception(f"Multiple versions of mod {name} found: {mods[name]} {version}")
                mods[name] = version

        if "core" in mods:
            del mods["core"]

        # Fix the sorting - requires python 3.7 for dict ordering to be preserved
        official_mods = dict(filter(lambda tup: tup[0] in FactorioMod.official_mod_names, mods.items()))
        official_mods = dict(sorted(official_mods.items(), key=lambda tup: tup[0].casefold()))
        third_party_mods = dict(filter(lambda tup: tup[0] not in FactorioMod.official_mod_names, mods.items()))
        third_party_mods = dict(sorted(third_party_mods.items(), key=lambda tup: tup[0].casefold()))
        mods = official_mods | third_party_mods

        return mods


class FactorioModList:
    def __init__(self, file_path: str | None = None, template: dict | None = None):
        import json

        self._file_path = file_path

        if self._file_path and template:
            raise Exception("Only max one of file_path and template can be given")

        if template:
            self.mod_list = template
        else:
            if not self._file_path:
                self._file_path = f"{FactorioSettings().config_dir_path}/mods/mod-list.json"

            # TODO : Use a path lib instead
            with open(self._file_path, "r") as file:
                self.mod_list = json.load(file)

    def disable_all_and_remove_versions(self):
        """
        Disables all mods in the mod list and removes any version tag
        """
        self.mod_list = {"mods": [{"name": mod["name"], "enabled": False} for mod in self.mod_list["mods"]]}

    def update_mod(self, updated_mod: dict):
        """
        Updates a mod in the list or appends it if it does not exist
        """
        index = next(
            (index for index, mod in enumerate(self.mod_list["mods"]) if mod["name"] == updated_mod["name"]), None
        )
        if index is not None:
            self.mod_list["mods"][index] = updated_mod
        else:
            self.mod_list["mods"].append(updated_mod)

    def sort(self):
        """
        Sorts the list of mods according to the same ordering as the factorio game defaults to
        """

        official_mods = list(filter(lambda elem: elem["name"] in FactorioMod.official_mod_names, self.mod_list["mods"]))
        official_mods = list(sorted(official_mods, key=lambda elem: elem["name"].casefold()))
        third_party_mods = list(
            filter(lambda elem: elem["name"] not in FactorioMod.official_mod_names, self.mod_list["mods"])
        )
        third_party_mods = list(sorted(third_party_mods, key=lambda elem: elem["name"].casefold()))

        self.mod_list["mods"] = official_mods + third_party_mods


def logsync(args):
    from pathlib import Path
    import json

    config_dir = FactorioSettings.get_default_config_dir()

    if args.output:
        path = str(Path(args.output).absolute())
    else:
        path = str(Path(f"{config_dir}/mods").absolute())

    print(path)
    factorio_version = ""
    mods_from_log = {"mods": []}
    for name, version in FactorioMod.get_mods_from_log(args.input).items():

        # Check factorio game version
        if name in FactorioMod.official_mod_names:
            mods_from_log["mods"].append({"name": name, "enabled": True})
            if not factorio_version:
                factorio_version = version
            else:
                if factorio_version != version:
                    raise Exception(f"Multiple versions of mod {name} found: {factorio_version} {version}")
        else:
            mods_from_log["mods"].append({"name": name, "enabled": True, "version": version})
            mod = FactorioMod(name)
            if not mod.exists(version=version, output_directory=path):
                mod.download(version=version, output_directory=path)
            else:
                print(f"{name} {version} already exists")

    modlist = FactorioModList(f"{path}/mod-list.json")
    modlist.disable_all_and_remove_versions()

    for logmod in mods_from_log["mods"]:
        modlist.update_mod(logmod)

    modlist.sort()

    with open(f"{config_dir}/mods/mod-list.json", "w") as file:
        json.dump(modlist.mod_list, file, indent=2)
        print("Updated mod-list.json")

    if factorio_version:
        print(f"INFO: Remember to ensure that the base factorio game version is: {factorio_version}")


def dl(args):
    mod = FactorioMod(args.name)
    mod.download(version=args.version, output_directory=args.output)


if __name__ == "__main__":
    import argparse
    from test import test

    argparser = argparse.ArgumentParser("famtools", description="Factorio Modding Tools Suite")
    subargparser = argparser.add_subparsers(title="subcommands")

    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("-c", "--config", type=str, help="Path to factorio settings directory", default=None)

    dl_parser = subargparser.add_parser("dl", help="Download a mod", parents=[common_parser])
    dl_parser.set_defaults(func=dl)
    dl_parser.add_argument("name", type=str, help="Name of the mod")
    dl_parser.add_argument("-v", "--version", type=str, help="Mod version to fetch, defaults to latest")
    dl_parser.add_argument("-o", "--output", type=str, help="Output directory")

    sync_log_parser = subargparser.add_parser(
        "logsync", help="Sync the list of mods with a factorio log file", parents=[common_parser]
    )
    sync_log_parser.set_defaults(func=logsync)
    sync_log_parser.add_argument("-i", "--input", type=str, required=True, help="Factorio log file")
    sync_log_parser.add_argument("-o", "--output", type=str, help="Factorio mod directory")

    test_parser = subargparser.add_parser("test", help="Run all unit tests", parents=[common_parser])
    test_parser.set_defaults(func=test)
    test_parser.add_argument("-v", "--verbose", action="store_true", help="Show more verbose progress")
    test_parser.add_argument("tests", nargs="*", type=str, help="Test cases to run")

    args = argparser.parse_args()

    if "func" in vars(args):
        args.func(args)
    else:
        argparser.print_help()
