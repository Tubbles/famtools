#!/usr/bin/env bash
# -*- coding: utf-8 -*-

set -Eeo pipefail

my_script="$(realpath "$0")"
my_dir="$(dirname "${my_script}")"

# Set the environment variable 'username' to your mod portal username
# Set the environment variable 'token' to your "service-token", according to
# https://wiki.factorio.com/Mod_portal_API#Downloading_Mods
# Or put them as a source-able bash file called `cred' next to this file

: "${username:=""}"
: "${token:=""}"

if [[ -z "${username}" ]] || [[ -z "${token}" ]]; then
    credentials_file="${my_dir}/cred"
    if [[ -r "${credentials_file}" ]]; then
        # shellcheck source=cred
        source "${credentials_file}"
    fi
fi

if [[ -z "${username}" ]] || [[ -z "${token}" ]]; then
    echo "Please supply mod portal username and token as environment variables"
    exit 1
fi

mod_name="$1"
mod_version="$2"

mod_list=(
    "AutoDeconstruct=1.0.2"
    "BottleneckLite=1.3.2"
    "Cursed-FMD=0.2.0"
    "CursorEnhancements=2.2.1"
    "DiscoScience=2.0.1"
    "EditorExtensions=2.3.1"
    "Flare_Stack_SA=2.3.2"
    "GUI_Unifyer_Unified=2.0.6"
    "PicksRocketStats=1.2.1"
    "RateCalculator=3.3.2"
    "StatsGui=1.6.1"
    "Todo-List-Continued=20.0.2"
    "Warehousing=0.6.0"
    "alien-biomes=0.7.1"
    "alien-biomes-graphics=0.7.0"
    "base=2.0.12"
    "bobinserters=1.3.2"
    "elevated-rails=2.0.12"
    "even-distribution=2.0.2"
    "flib=0.15.0"
    "helmod=2.0.4"
    "informatron=0.4.0"
    "inventory-repair=20.0.2"
    "jetpack=0.4.5"
    "pump=2.0.1"
    "quality=2.0.12"
    "space-age=2.0.12"
    "squeak-through-2=0.1.2"
    "textplates=0.7.1"
)

function download_mod_version() {
    mod_name="$1"
    mod_version="$2"
    username="$3"
    token="$4"
    output_dir="$5"
    : "${output_dir:="$(pwd)"}"

    download_stem="$(curl "https://mods.factorio.com/api/mods/${mod_name}/full" |
        jq -r '.releases[] | select(.version == "'"${mod_version}"'") | .download_url')"

    wget "https://mods.factorio.com${download_stem}?username=${username}&token=${token}" -O"${output_dir}/${mod_name}_${mod_version}.zip"
}

function main() {
    if [[ -z "${mod_name}" ]]; then
        for modinfo in "${mod_list[@]}"; do
            mod_name="$(echo "${modinfo}" | awk -F'=' '{print $1}')"
            mod_version="$(echo "${modinfo}" | awk -F'=' '{print $2}')"
            download_mod_version "${mod_name}" "${mod_version}" "${username}" "${token}"
        done
    else
        download_mod_version "${mod_name}" "${mod_version}" "${username}" "${token}"
        # TODO : If mod version is not given, automatically fall back to the latest version
    fi
}

function test() {
    test_dir="$(mktemp --directory)"

    # Trap handler
    # shellcheck disable=SC2317
    function cleanup() {
        if [[ -n "$1" ]] && [[ -n "$2" ]]; then
            echo "Error: ($1) occurred on line $2"
            exitcode="$1"
        else
            exitcode=0
        fi
        rm -fr "${test_dir}"
        exit "${exitcode}"
    }
    trap 'cleanup $? $LINENO' ERR

    # Start tests
    download_mod_version "AutoDeconstruct" "1.0.2" "${username}" "${token}" "${test_dir}"
    echo "5aee3fecca835e284bfff832e2a54b5d  AutoDeconstruct_1.0.2.zip" | md5sum --check -
    cleanup "" ""
}

if [[ -z "${TEST}" ]]; then
    main
else
    test
fi
