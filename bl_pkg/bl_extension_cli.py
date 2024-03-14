# SPDX-FileCopyrightText: 2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Command line access for extension operations see:

   blender --command extension --help
"""

__all__ = (
    "cli_extension_handler",
)

import argparse
import os
import sys

show_color = (
    False if os.environ.get("NO_COLOR") else
    sys.stdout.isatty()
)


if show_color:
    color_codes = {
        'black': '\033[0;30m',
        'bright_gray': '\033[0;37m',
        'blue': '\033[0;34m',
        'white': '\033[1;37m',
        'green': '\033[0;32m',
        'bright_blue': '\033[1;34m',
        'cyan': '\033[0;36m',
        'bright_green': '\033[1;32m',
        'red': '\033[0;31m',
        'bright_cyan': '\033[1;36m',
        'purple': '\033[0;35m',
        'bright_red': '\033[1;31m',
        'yellow': '\033[0;33m',
        'bright_purple': '\033[1;35m',
        'dark_gray': '\033[1;30m',
        'bright_yellow': '\033[1;33m',
        'normal': '\033[0m',
    }

    def colorize(text, color):
        return (color_codes[color] + text + color_codes["normal"])
else:
    def colorize(text, _color):
        return text


def arg_handle_int_as_bool(value: str) -> bool:
    result = int(value)
    if result not in {0, 1}:
        raise argparse.ArgumentTypeError("Expected a 0 or 1")
    return bool(result)


def generic_arg_sync(subparse):
    subparse.add_argument(
        "-s",
        "--sync",
        dest="sync",
        action="store_true",
        default=False,
        help=(
            "Sync the remote directory before performing the action."
        ),
    )


def generic_arg_enable_on_install(subparse):
    subparse.add_argument(
        "--enable",
        dest="enable",
        action="store_true",
        default=False,
        help=(
            "Enable the extension after installation."
        ),
    )


def generic_arg_package_list_positional(subparse):
    subparse.add_argument(
        dest="packages",
        type=str,
        help=(
            "The packages to operate on (separated by ``,`` without spaces)."
        ),
    )


def generic_arg_package_file_positional(subparse):
    subparse.add_argument(
        dest="file",
        type=str,
        help=(
            "The packages file."
        ),
    )


def generic_arg_repo_id(subparse):
    subparse.add_argument(
        "-r",
        "--repo",
        dest="repo",
        type=str,
        help=(
            "The repository identifier."
        ),
        required=True,
    )


class subcmd_utils:

    def sync(show_done=True):
        import bpy
        try:
            bpy.ops.bl_pkg.repo_sync_all()
            if show_done:
                sys.stdout.write("Done...\n\n")
        except BaseException:
            print("Error synchronizing")
            import traceback
            traceback.print_exc()
            return False
        return True

    def _expand_package_ids(packages, *, use_local):
        # Takes a terse lists of package names and expands to repo index and name list,
        # returning an error string if any can't be resolved.
        from . import repo_cache_store
        from .bl_extension_ops import extension_repos_read

        repo_map = {}
        errors = []

        repos_all = extension_repos_read()
        for (
                repo_index,
                pkg_manifest,
        ) in enumerate(
            repo_cache_store.pkg_manifest_from_local_ensure(error_fn=print)
            if use_local else
            repo_cache_store.pkg_manifest_from_remote_ensure(error_fn=print)
        ):
            # Show any exceptions created while accessing the JSON,
            repo = repos_all[repo_index]
            repo_map[repo.module] = (repo_index, set(pkg_manifest.keys()))

        repos_and_packages = []

        for pkg_id_full in packages:
            repo_id, pkg_id = pkg_id_full.rpartition(".")[0::2]
            if not pkg_id:
                errors.append("Malformed package name \"{:s}\", expected \"repo_id.pkg_id\"!".format(pkg_id_full))
                continue
            if repo_id:
                repo_index, repo_packages = repo_map.get(repo_id, (None, None))
                if repo_index is None:
                    errors.append("Repository \"{:s}\" not found in [{:s}]!".format(
                        repo_id,
                        ", ".join(sorted("\"{:s}\"".format(x) for x in repo_map.keys()))
                    ))
                    continue
            else:
                repo_index = None
                for repo_id_iter, (repo_index_iter, repo_packages_iter) in repo_map.items():
                    if pkg_id in repo_packages_iter:
                        repo_index = repo_index_iter
                        break
                if repo_index is None:
                    if use_local:
                        errors.append("Package \"{:s}\" not installed in local repositories!".format(pkg_id))
                    else:
                        errors.append("Package \"{:s}\" not found in remote repositories!".format(pkg_id))
                    continue
            repos_and_packages.append((repo_index, pkg_id))

        if errors:
            return "\n".join(errors)

        return repos_and_packages

    def expand_package_ids_from_remote(packages):
        return subcmd_utils._expand_package_ids(packages, use_local=False)

    def expand_package_ids_from_local(packages):
        return subcmd_utils._expand_package_ids(packages, use_local=True)


class subcmd_query:

    def __new__(cls):
        raise RuntimeError("{:s} should not be instantiated".format(cls))

    def list(sync):

        def list_item(pkg_id, item_remote, item_local):
            if item_remote is not None:
                item_version = item_remote["version"]
                if item_local is None:
                    item_local_version = None
                    is_outdated = False
                else:
                    item_local_version = item_local["version"]
                    is_outdated = item_local_version != item_version

                if item_local is not None:
                    if is_outdated:
                        status_info = " [{:s}]".format(colorize("outdated: {:s} -> {:s}".format(
                            item_local_version,
                            item_version,
                        ), "red"))
                    else:
                        status_info = " [{:s}]".format(colorize("installed", "green"))
                else:
                    status_info = ""
                item = item_remote
            else:
                # All local-only packages are installed.
                status_info = " [{:s}]".format(colorize("installed", "green"))
                item = item_local

            print(
                "  {:s}{:s}: {:s}".format(
                    pkg_id,
                    status_info,
                    colorize("\"{:s}\", {:s}".format(item["name"], item.get("tagline", "<no tagline>")), "dark_gray"),
                ))

        if sync:
            if not subcmd_utils.sync():
                return False

        # NOTE: exactly how this data is extracted is rather arbitrary.
        # This uses the same code paths as drawing code.
        from .bl_extension_ops import extension_repos_read
        from . import repo_cache_store

        repos_all = extension_repos_read()

        for repo_index, (
                pkg_manifest_remote,
                pkg_manifest_local,
        ) in enumerate(zip(
            repo_cache_store.pkg_manifest_from_remote_ensure(error_fn=print),
            repo_cache_store.pkg_manifest_from_local_ensure(error_fn=print),
        )):
            # Show any exceptions created while accessing the JSON,
            repo = repos_all[repo_index]

            print("Repository: \"{:s}\" (id={:s})".format(repo.name, repo.module))
            if pkg_manifest_remote is not None:
                for pkg_id, item_remote in pkg_manifest_remote.items():
                    item_local = pkg_manifest_local is not None and pkg_manifest_local.get(pkg_id)
                    list_item(pkg_id, item_remote, item_local)
            else:
                for pkg_id, item_local in pkg_manifest_local.items():
                    list_item(pkg_id, None, item_local)

        return True


class subcmd_pkg:

    def __new__(cls):
        raise RuntimeError("{:s} should not be instantiated".format(cls))

    def update(sync):
        if sync:
            if not subcmd_utils.sync():
                return False

        import bpy
        try:
            bpy.ops.bl_pkg.pkg_upgrade_all()
        except RuntimeError:
            return False  # The error will have been printed.
        return True

    def install(*, sync, packages, enable_on_install):
        if sync:
            if not subcmd_utils.sync():
                return False

        # Expand all package ID's.
        repos_and_packages = subcmd_utils.expand_package_ids_from_remote(packages)
        if isinstance(repos_and_packages, str):
            sys.stderr.write(repos_and_packages)
            sys.stderr.write("\n")
            return False

        import bpy
        for repo_index, pkg_id in repos_and_packages:
            bpy.ops.bl_pkg.pkg_mark_set(
                repo_index=repo_index,
                pkg_id=pkg_id,
            )

        try:
            bpy.ops.bl_pkg.pkg_install_marked(enable_on_install=enable_on_install)
        except RuntimeError:
            return False  # The error will have been printed.

        if enable_on_install:
            bpy.ops.wm.save_userpref()

        return True

    def remove(packages):
        # Expand all package ID's.
        repos_and_packages = subcmd_utils.expand_package_ids_from_local(packages)
        if isinstance(repos_and_packages, str):
            sys.stderr.write(repos_and_packages)
            sys.stderr.write("\n")
            return False

        import bpy
        for repo_index, pkg_id in repos_and_packages:
            bpy.ops.bl_pkg.pkg_mark_set(repo_index=repo_index, pkg_id=pkg_id)

        try:
            bpy.ops.bl_pkg.pkg_uninstall_marked()
        except RuntimeError:
            return False  # The error will have been printed.

        bpy.ops.wm.save_userpref()
        return True

    def install_file(
            *,
            filepath,
            repo_id,
            enable_on_install,
    ):
        import bpy
        try:
            bpy.ops.bl_pkg.pkg_install_files(
                filepath=filepath,
                repo=repo_id,
                enable_on_install=enable_on_install,
            )
        except RuntimeError:
            return False  # The error will have been printed.
        except BaseException as ex:
            sys.stderr.write(str(ex))
            sys.stderr.write("\n")

        if enable_on_install:
            bpy.ops.wm.save_userpref()

        return True


class subcmd_repo:

    def __new__(cls):
        raise RuntimeError("{:s} should not be instantiated".format(cls))

    def list():
        from .bl_extension_ops import extension_repos_read
        repos_all = extension_repos_read()
        for repo in repos_all:
            print("{:s}:".format(repo.module))
            print("    name: \"{:s}\"".format(repo.name))
            print("    directory: \"{:s}\"".format(repo.directory))
            if url := repo.repo_url:
                print("    url: \"{:s}\"".format(url))

        return True

    def add(name, id, directory, url, cache):
        from bpy import context
        repo = context.preferences.filepaths.extension_repos.new(
            name=name,
            module=id,
            custom_directory=directory,
            remote_path=url,
        )
        repo.use_cache = cache

        import bpy
        bpy.ops.wm.save_userpref()

        return True

    def remove(id):
        from bpy import context
        extension_repos = context.preferences.filepaths.extension_repos
        extension_repos_module_map = {repo.module: repo for repo in extension_repos}
        repo = extension_repos_module_map.get(id)
        if repo is None:
            sys.stderr.write("Repository: \"{:s}\" not found in [{:s}]\n".format(
                id,
                ", ".join(["\"{:s}\"".format(x) for x in sorted(extension_repos_module_map.keys())])
            ))
            return False
        extension_repos.remove(repo)
        print("Removed repo \"{:s}\"".format(id))

        import bpy
        bpy.ops.wm.save_userpref()
        return True


# -----------------------------------------------------------------------------
# Blender Package Manipulation

def cli_extension_args_list(subparsers):
    # Implement "list".
    subparse = subparsers.add_parser(
        "list",
        help="List all packages.",
        description=(
            "List packages from all enabled repositories."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    generic_arg_sync(subparse)

    subparse.set_defaults(
        func=lambda args: subcmd_query.list(
            sync=args.sync,
        ),
    )


def cli_extension_args_sync(subparsers):
    # Implement "sync".
    subparse = subparsers.add_parser(
        "sync",
        help="Synchronize with remote repositories.",
        description=(
            "Download package information for remote repositories."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparse.set_defaults(
        func=lambda args: subcmd_utils.sync(show_done=False),
    )


def cli_extension_args_upgrade(subparsers):
    # Implement "update".
    subparse = subparsers.add_parser(
        "update",
        help="Upgrade any outdated packages.",
        description=(
            "Download and update any outdated packages."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    generic_arg_sync(subparse)

    subparse.set_defaults(
        func=lambda args: subcmd_pkg.update(sync=args.sync),
    )


def cli_extension_args_install(subparsers):
    # Implement "install".
    subparse = subparsers.add_parser(
        "install",
        help="Install packages.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    generic_arg_sync(subparse)
    generic_arg_package_list_positional(subparse)

    generic_arg_enable_on_install(subparse)

    subparse.set_defaults(
        func=lambda args: subcmd_pkg.install(
            sync=args.sync,
            packages=args.packages.split(","),
            enable_on_install=args.enable,
        ),
    )


def cli_extension_args_install_file(subparsers):
    # Implement "install-file".
    subparse = subparsers.add_parser(
        "install-file",
        help="Install package from file.",
        description=(
            "Install a package file into a local repository."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    generic_arg_package_file_positional(subparse)
    generic_arg_repo_id(subparse)

    generic_arg_enable_on_install(subparse)

    subparse.set_defaults(
        func=lambda args: subcmd_pkg.install_file(
            filepath=args.file,
            repo_id=args.repo,
            enable_on_install=args.enable,
        ),
    )


def cli_extension_args_remove(subparsers):
    # Implement "remove".
    subparse = subparsers.add_parser(
        "remove",
        help="Remove packages.",
        description=(
            "Disable & remove package(s)."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    generic_arg_package_list_positional(subparse)

    subparse.set_defaults(
        func=lambda args: subcmd_pkg.remove(
            packages=args.packages.split(","),
        ),
    )


# -----------------------------------------------------------------------------
# Blender Repository Manipulation

def cli_extension_args_repo_list(subparsers):
    # Implement "repo-list".
    subparse = subparsers.add_parser(
        "repo-list",
        help="List repositories.",
        description=(
            "List all repositories stored in Blender's preferences."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparse.set_defaults(
        func=lambda args: subcmd_repo.list(),
    )


def cli_extension_args_repo_add(subparsers):
    # Implement "repo-add".
    subparse = subparsers.add_parser(
        "repo-add",
        help="Add repository.",
        description=(
            "Add a new local or remote repository."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparse.add_argument(
        dest="id",
        type=str,
        help=(
            "The repository identifier."
        ),
    )

    # Optional.
    subparse.add_argument(
        "--name",
        dest="name",
        type=str,
        default="",
        metavar="NAME",
        help=(
            "The name to display in the interface (optional)."
        ),
    )

    subparse.add_argument(
        "--directory",
        dest="directory",
        type=str,
        default="",
        help=(
            "The directory where the repository stores local files (optional).\n"
            "When omitted a directory in the users directory is automatically selected."
        ),
    )
    subparse.add_argument(
        "--url",
        dest="url",
        type=str,
        default="",
        metavar="URL",
        help=(
            "The URL, for remote repositories (optional).\n"
            "When omitted the repository is considered \"local\"\n"
            "as it is not connected to an external repository,\n"
            "where packages may be installed by file or managed manually."
        ),
    )

    subparse.add_argument(
        "--cache",
        dest="cache",
        metavar="BOOLEAN",
        type=arg_handle_int_as_bool,
        default=True,
        help=(
            "Use package cache (default=1)."
        ),
    )

    subparse.set_defaults(
        func=lambda args: subcmd_repo.add(
            id=args.id,
            name=args.name,
            directory=args.directory,
            url=args.url,
            cache=args.cache,
        ),
    )


def cli_extension_args_repo_remove(subparsers):
    # Implement "repo-remove".
    subparse = subparsers.add_parser(
        "repo-remove",
        help="Remove repository.",
        description=(
            "Remove a repository."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparse.add_argument(
        dest="id",
        type=str,
        help=(
            "The repository identifier."
        ),
    )

    subparse.set_defaults(
        func=lambda args: subcmd_repo.remove(
            id=args.id,
        ),
    )


# -----------------------------------------------------------------------------
# Implement Additional Arguments

def cli_extension_args_extra(subparsers):
    # Package commands.
    cli_extension_args_list(subparsers)
    cli_extension_args_sync(subparsers)
    cli_extension_args_upgrade(subparsers)
    cli_extension_args_install(subparsers)
    cli_extension_args_install_file(subparsers)
    cli_extension_args_remove(subparsers)

    # Preference commands.
    cli_extension_args_repo_list(subparsers)
    cli_extension_args_repo_add(subparsers)
    cli_extension_args_repo_remove(subparsers)


def cli_extension_handler(args):
    from .cli import blender_ext
    return blender_ext.main(
        args,
        args_internal=False,
        args_extra_subcommands_fn=cli_extension_args_extra,
        prog="blender --command extension",
    )
