#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from famtools import *
from test_runner import *


def test_download(args):
    import os
    import hashlib

    mod = FactorioMod("AutoDeconstruct")
    version = "1.0.2"

    file_path = mod.download(version=version)

    assert hashlib.sha1(open(file_path, "rb").read()).hexdigest() == mod.get_sha1(version)


def test_get_mods_from_log(args):
    import json

    modlist = FactorioMod.get_mods_from_log(f"{FactorioSettings.get_default_config_dir()}/factorio-current.log")

    print(json.dumps(modlist, indent=4))

    assert len(modlist)


def test_get_credentials(args):
    import json

    settings = FactorioSettings()
    creds = settings.get_credentials()
    print(json.dumps(settings.get_credentials(), indent=4))
    assert "username" in creds
    assert "token" in creds


def test_get_mod_highest_version(args):
    mod = FactorioMod("AutoDeconstruct")
    versions = mod.get_all_versions()
    print(versions)
    assert mod.get_highest_version() == versions[-1]


def test_modlist_disable_all_and_remove_versions(args):
    modlist = FactorioModList(
        template={
            "mods": [
                {"name": "aai-vehicles-ironclad", "enabled": False},
                {"name": "Advanced-Electric-Revamped-v16", "enabled": True},
                {"name": "afraid-of-the-dark", "enabled": True, "version": "1.2.3"},
            ]
        }
    )
    modlist.disable_all_and_remove_versions()

    assert not any([mod["enabled"] or mod.get("version", False) for mod in modlist.mod_list["mods"]])


def test_modlist_sort(args):
    import json

    modlist = FactorioModList(
        template={
            "mods": [
                {"name": "afraid-of-the-dark", "enabled": True, "version": "1.2.3"},
                {"name": "elevated-rails", "enabled": True},
                {"name": "aai-vehicles-ironclad", "enabled": False},
                {"name": "base", "enabled": True},
                {"name": "Advanced-Electric-Revamped-v16", "enabled": True},
                {"name": "ConfigurableVehicles", "enabled": False},
            ]
        }
    )
    modlist.sort()
    expected = {
        "mods": [
            {"name": "base", "enabled": True},
            {"name": "elevated-rails", "enabled": True},
            {"name": "aai-vehicles-ironclad", "enabled": False},
            {"name": "Advanced-Electric-Revamped-v16", "enabled": True},
            {"name": "afraid-of-the-dark", "enabled": True, "version": "1.2.3"},
            {"name": "ConfigurableVehicles", "enabled": False},
        ]
    }

    print(json.dumps(modlist.mod_list, indent=4))
    assert modlist.mod_list == expected


test_list = [
    test_download,
    test_get_mods_from_log,
    test_get_credentials,
    test_get_mod_highest_version,
    test_modlist_disable_all_and_remove_versions,
    test_modlist_sort,
]


def test(args):
    test_runner(test_list, verbose=args.verbose, active_tests=args.tests, arg=args)
