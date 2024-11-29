#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import *


def test_runner(test_list: list[Callable[[Any | None], None]], verbose=False, active_tests: list[str] = [], arg=None):
    import os
    import shutil
    import tempfile
    import colorama
    import traceback
    import io
    import contextlib
    import sys

    colorama.init()
    Fore = colorama.Fore
    Style = colorama.Style
    original_cwd = os.getcwd()
    exception_list: list[Exception] = []

    if active_tests:
        test_list = [test for test in test_list if test.__name__ in active_tests]

    # Run the tests
    for index, test_func in enumerate(test_list):
        # Test setup
        tmpdir = tempfile.mkdtemp()
        os.chdir(tmpdir)
        progress = f"{index+1}/{len(test_list)}"
        print_kwargs = {"end": "", "flush": True} if not verbose else {}
        print(f"  {progress} {test_func.__name__} ", **print_kwargs)
        stringio = io.StringIO()

        # Run the test
        try:
            if verbose:
                test_func(arg)
            else:
                with contextlib.redirect_stderr(stringio):
                    with contextlib.redirect_stdout(stringio):
                        test_func(arg)
            print(f"{Fore.GREEN}✅{Style.RESET_ALL}")

        except BaseException as e:
            print(f"{Fore.RED}❌{Style.RESET_ALL}")
            text = f"{Fore.RED}❌{Style.RESET_ALL} {test_func.__name__}\n"
            text += f"{stringio.getvalue()}{traceback.format_exc()}"
            exception_list.append(text)
            if type(e) in (BaseExceptionGroup, GeneratorExit, KeyboardInterrupt, SystemExit):
                break

        # Cleanup
        os.chdir(original_cwd)
        shutil.rmtree(tmpdir)

    # Print final report
    if exception_list:
        for exception in exception_list:
            print(exception)
        sys.exit(len(exception_list))
