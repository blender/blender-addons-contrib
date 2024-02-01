# SPDX-FileCopyrightText: 2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Non-blocking access to package management.

- No ``bpy`` module use.
"""

__all__ = (
    # Public Repository Actions.
    "repo_sync",
    "repo_upgrade",
    "repo_listing",

    # Public Package Actions.
    "pkg_install",
    "pkg_uninstall",

    "pkg_make_obsolete_for_testing",

    "dummy_progress",

    # Public API.
    "json_from_filepath",
    "toml_from_filepath",
    "json_to_filepath",

    "CommandBatch",
    "RepoCacheStore",

    # Directory Lock.
    "RepoLock",
    "RepoLockContext",
)

import json
import os
import sys
import signal
import stat
import subprocess
import time
import tomllib


from typing import (
    Any,
    Callable,
    Generator,
    IO,
    List,
    Optional,
    Dict,
    Sequence,
    Tuple,
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

BLENDER_EXT_CMD = (
    # When run from within Blender, it will point to Blender's local Python binary.
    sys.executable,
    os.path.normpath(os.path.join(BASE_DIR, "cli", "blender_ext.py")),
)

# This directory is in the local repository.
REPO_LOCAL_PRIVATE_DIR = ".blender_ext"
# Locate inside `REPO_LOCAL_PRIVATE_DIR`.
REPO_LOCAL_PRIVATE_LOCK = "bl_ext_repo.lock"

PKG_REPO_LIST_FILENAME = "bl_ext_repo.json"
PKG_MANIFEST_FILENAME_TOML = "blender_manifest.toml"

# Add this to the local JSON file.
REPO_LOCAL_JSON = os.path.join(REPO_LOCAL_PRIVATE_DIR, PKG_REPO_LIST_FILENAME)

# An item we communicate back to Blender.
InfoItem = Tuple[str, Any]
InfoItemSeq = Sequence[InfoItem]

COMPLETE_ITEM = ('DONE', "")

# Time to wait when there is no output, avoid 0 as it causes high CPU usage.
IDLE_WAIT_ON_READ = 0.05
# IDLE_WAIT_ON_READ = 0.2


# -----------------------------------------------------------------------------
# Internal Functions.
#

def file_handle_make_non_blocking(file_handle: IO[bytes]) -> None:
    import fcntl

    # Get current `file_handle` flags.
    flags = fcntl.fcntl(file_handle.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(file_handle, fcntl.F_SETFL, flags | os.O_NONBLOCK)


def file_mtime_or_none(filepath: str) -> Optional[int]:
    try:
        # For some reason `mypy` thinks this is a float.
        return int(os.stat(filepath)[stat.ST_MTIME])
    except FileNotFoundError:
        return None


# -----------------------------------------------------------------------------
# Call JSON.
#

def non_blocking_call(cmd: Sequence[str]) -> subprocess.Popen[bytes]:
    # pylint: disable-next=consider-using-with
    ps = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout = ps.stdout
    assert stdout is not None
    # Needed so whatever is available can be read (without waiting).
    file_handle_make_non_blocking(stdout)
    return ps


def command_output_from_json_0(
        args: Sequence[str],
        use_idle: bool,
) -> Generator[InfoItemSeq, bool, None]:
    cmd = [*BLENDER_EXT_CMD, *args, "--output-type=JSON_0"]
    ps = non_blocking_call(cmd)
    stdout = ps.stdout
    assert stdout is not None
    chunk_list = []
    request_exit_signal_sent = False

    while True:
        # It's possible this is multiple chunks.
        chunk = stdout.read()
        if not chunk:
            if ps.poll() is not None:
                break
            if use_idle:
                time.sleep(IDLE_WAIT_ON_READ)
            continue

        # Extract contiguous data from `chunk_list`.
        chunk_zero_index = chunk.find(b'\0')
        if chunk_zero_index == -1:
            chunk_list.append(chunk)
        else:
            json_messages = []
            chunk_list.append(chunk[:chunk_zero_index])

            json_bytes_list = [b''.join(chunk_list)]
            chunk_list.clear()

            # There may be data afterwards, even whole chunks.
            if chunk_zero_index + 1 != len(chunk):
                chunk = chunk[chunk_zero_index + 1:]
                # Add whole chunks.
                while (chunk_zero_index := chunk.find(b'\0')) != -1:
                    json_bytes_list.append(chunk[:chunk_zero_index])
                    chunk = chunk[chunk_zero_index + 1:]
                if chunk:
                    chunk_list.append(chunk)

            request_exit = False

            for json_bytes in json_bytes_list:
                json_data = json.loads(json_bytes.decode("utf-8"))

                assert len(json_data) == 2
                assert isinstance(json_data[0], str)

                json_messages.append((json_data[0], json_data[1]))

            request_exit = yield json_messages
            if request_exit and not request_exit_signal_sent:
                ps.send_signal(signal.SIGINT)
                request_exit_signal_sent = True


# -----------------------------------------------------------------------------
# Internal Functions.
#


def repositories_validate_or_errors(repos: Sequence[str]) -> Optional[InfoItemSeq]:
    return None


# -----------------------------------------------------------------------------
# Public Repository Actions
#

def repo_sync(
        *,
        directory: str,
        repo_url: str,
        use_idle: bool,
) -> Generator[InfoItemSeq, None, None]:
    """
    Implementation:
    ``bpy.ops.ext.repo_sync(directory)``.
    """
    yield from command_output_from_json_0([
        "sync",
        "--local-dir", directory,
        "--repo-dir", repo_url,
    ], use_idle=use_idle)
    yield [COMPLETE_ITEM]


def repo_upgrade(
        *,
        directory: str,
        repo_url: str,
        use_idle: bool,
) -> Generator[InfoItemSeq, None, None]:
    """
    Implementation:
    ``bpy.ops.ext.repo_upgrade(directory)``.
    """
    yield from command_output_from_json_0([
        "upgrade",
        "--local-dir", directory,
        "--repo-dir", repo_url,
    ], use_idle=use_idle)
    yield [COMPLETE_ITEM]


def repo_listing(
        *,
        repos: Sequence[str],
) -> Generator[InfoItemSeq, None, None]:
    """
    Implementation:
    ``bpy.ops.ext.repo_listing(directory)``.
    """
    if result := repositories_validate_or_errors(repos):
        yield result
        return

    yield [COMPLETE_ITEM]


# -----------------------------------------------------------------------------
# Public Package Actions
#

def pkg_install(
        *,
        directory: str,
        repo_url: str,
        pkg_id_sequence: Sequence[str],
        use_cache: bool,
        use_idle: bool,
) -> Generator[InfoItemSeq, None, None]:
    """
    Implementation:
    ``bpy.ops.ext.pkg_install(directory, pkg_id)``.
    """
    yield from command_output_from_json_0([
        "install", ",".join(pkg_id_sequence),
        "--local-dir", directory,
        "--repo-dir", repo_url,
        "--local-cache", str(int(use_cache)),
    ], use_idle=use_idle)
    yield [COMPLETE_ITEM]


def pkg_uninstall(
        *,
        directory: str,
        pkg_id_sequence: Sequence[str],
        use_idle: bool,
) -> Generator[InfoItemSeq, None, None]:
    """
    Implementation:
    ``bpy.ops.ext.pkg_uninstall(directory, pkg_id)``.
    """
    yield from command_output_from_json_0([
        "uninstall", ",".join(pkg_id_sequence),
        "--local-dir", directory,
    ], use_idle=use_idle)
    yield [COMPLETE_ITEM]


# -----------------------------------------------------------------------------
# Public Demo Actions
#

def dummy_progress(
        *,
        use_idle: bool,
) -> Generator[InfoItemSeq, bool, None]:
    """
    Implementation:
    ``bpy.ops.ext.dummy_progress()``.
    """
    yield from command_output_from_json_0(["dummy-progress", "--time-duration=1.0"], use_idle=use_idle)
    yield [COMPLETE_ITEM]


# -----------------------------------------------------------------------------
# Public (non-command-line-wrapping) functions
#

def json_from_filepath(filepath_json: str) -> Optional[Dict[str, Any]]:
    if os.path.exists(filepath_json):
        with open(filepath_json, "r", encoding="utf-8") as fh:
            result = json.loads(fh.read())
            assert isinstance(result, dict)
            return result
    return None


def toml_from_filepath(filepath_json: str) -> Optional[Dict[str, Any]]:
    if os.path.exists(filepath_json):
        with open(filepath_json, "r", encoding="utf-8") as fh:
            return tomllib.loads(fh.read())
    return None


def json_to_filepath(filepath_json: str, data: Any) -> None:
    with open(filepath_json, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(data))


def pkg_make_obsolete_for_testing(local_dir: str, pkg_id: str) -> None:
    import re
    filepath = os.path.join(local_dir, pkg_id, PKG_MANIFEST_FILENAME_TOML)
    # Weak! use basic matching to replace the version, not nice but OK as a debugging option.
    with open(filepath, "r", encoding="utf-8") as fh:
        data = fh.read()

    def key_replace(match: re.Match[str]) -> str:
        return "version = \"0.0.0\""

    data = re.sub(r"^\s*version\s*=\s*\"[^\"]+\"", key_replace, data, flags=re.MULTILINE)
    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write(data)


def pkg_validate_data_or_error(
        pkg_idname: str,
        data: Dict[str, Any],
        from_repo: bool,
) -> Optional[str]:
    # Exception! In in general `cli` shouldn't be considered a Python module,
    # it's validation function is handy to reuse.
    from .cli.blender_ext import pkg_manifest_from_dict_and_validate
    assert "id" not in data
    result = pkg_manifest_from_dict_and_validate(pkg_idname, data, from_repo=from_repo)
    if isinstance(result, str):
        return "{:s}: {:s}".format(pkg_idname, result)
    return None


# -----------------------------------------------------------------------------
# Public Command Pool (non-command-line wrapper)
#

InfoItemCallable = Callable[[], Generator[InfoItemSeq, bool, None]]


class CommandBatchItem:
    __slots__ = (
        "fn_with_args",
        "fn_iter",
        "status",
        "msg_log",

        "msg_type",
        "msg_info",
    )

    STATUS_NOT_YET_STARTED = 0
    STATUS_RUNNING = 1
    STATUS_COMPLETE = -1

    def __init__(self, fn_with_args: InfoItemCallable):
        self.fn_with_args = fn_with_args
        self.fn_iter: Optional[Generator[InfoItemSeq, bool, None]] = None
        self.status = CommandBatchItem.STATUS_NOT_YET_STARTED
        self.msg_log: List[Tuple[str, Any]] = []
        self.msg_type = ""
        self.msg_info = ""

    def invoke(self) -> Generator[InfoItemSeq, bool, None]:
        return self.fn_with_args()


class CommandBatch:
    __slots__ = (
        "title",

        "_batch",
        "_request_exit",
        "_log_added_since_accessed",
    )

    def __init__(
            self,
            *,
            title: str,
            batch: Sequence[InfoItemCallable],
    ):
        self.title = title
        self._batch = [CommandBatchItem(fn_with_args) for fn_with_args in batch]
        self._request_exit = False
        self._log_added_since_accessed = True

    def _exec_blocking_single(
            self,
            report_fn: Callable[[str, str], None],
            request_exit_fn: Callable[[], bool],
    ) -> bool:
        for cmd in self._batch:
            assert cmd.fn_iter is None
            cmd.fn_iter = cmd.invoke()
            request_exit: Optional[bool] = None
            while True:
                try:
                    # Request `request_exit` starts of as None, then it's a boolean.
                    json_messages = cmd.fn_iter.send(request_exit)  # type: ignore
                except StopIteration:
                    break

                for ty, msg in json_messages:
                    report_fn(ty, msg)

                if request_exit is None:
                    request_exit = False

            if request_exit is True:
                break
        if request_exit is None:
            return True
        return request_exit

    def _exec_blocking_multi(
            self,
            *,
            report_fn: Callable[[str, str], None],
            request_exit_fn: Callable[[], bool],
    ) -> bool:
        # TODO, concurrent execution.
        return self._exec_blocking_single(report_fn, request_exit_fn)

    def exec_blocking(
            self,
            report_fn: Callable[[str, str], None],
            request_exit_fn: Callable[[], bool],
            concurrent: bool,
    ) -> bool:
        # Blocking execution & finish.
        if concurrent:
            return self._exec_blocking_multi(
                report_fn=report_fn,
                request_exit_fn=request_exit_fn,
            )
        return self._exec_blocking_single(report_fn, request_exit_fn)

    def exec_non_blocking(
            self,
            *,
            request_exit: bool,
    ) -> Optional[Tuple[List[Tuple[str, str]], ...]]:
        """
        For each command, return a list of commands for each command.
        """
        command_output: Tuple[List[Tuple[str, str]], ...] = tuple([] for _ in range(len(self._batch)))

        if request_exit:
            self._request_exit = True

        all_complete = True
        for cmd_index in reversed(range(len(self._batch))):
            cmd = self._batch[cmd_index]
            if cmd.status == CommandBatchItem.STATUS_COMPLETE:
                continue

            all_complete = False
            send_arg: Optional[bool] = self._request_exit

            # First time initialization.
            if cmd.fn_iter is None:
                cmd.fn_iter = cmd.invoke()
                send_arg = None

            try:
                json_messages = cmd.fn_iter.send(send_arg)  # type: ignore
            except StopIteration:
                # FIXME: This should not happen, we should get a "DONE" instead.
                cmd.status = CommandBatchItem.STATUS_COMPLETE
                continue

            if json_messages:
                for ty, msg in json_messages:
                    self._log_added_since_accessed = True

                    cmd.msg_type = ty
                    cmd.msg_info = msg
                    if ty == 'DONE':
                        assert msg == ""
                        cmd.status = CommandBatchItem.STATUS_COMPLETE
                        break

                    command_output[cmd_index].append((ty, msg))
                    if ty != 'PROGRESS':
                        cmd.msg_log.append((ty, msg))

        if all_complete:
            return None

        return command_output

    def calc_status_string(self) -> List[str]:
        return [
            "{:s}: {:s}".format(cmd.msg_type, cmd.msg_info)
            for cmd in self._batch if (cmd.msg_type or cmd.msg_info)
        ]

    def calc_status_log_or_none(self) -> Optional[List[Tuple[str, str]]]:
        """
        Return the log or None if there were no changes since the last call.
        """
        if self._log_added_since_accessed is False:
            return None
        self._log_added_since_accessed = False

        return [
            (ty, msg)
            for cmd in self._batch
            for ty, msg in (cmd.msg_log + ([(cmd.msg_type, cmd.msg_info)] if cmd.msg_type == 'PROGRESS' else []))
        ]


# -----------------------------------------------------------------------------
# Public Repo Cache (non-command-line wrapper)
#

class _RepoCacheEntry:
    __slots__ = (
        "directory",
        "repo_url",

        "_pkg_manifest_local",
        "_pkg_manifest_remote",
        "_pkg_manifest_remote_mtime",
        "_pkg_manifest_remote_has_warning"
    )

    def __init__(self, directory: str, repo_url: str) -> None:
        assert directory != ""
        self.directory = directory
        self.repo_url = repo_url
        # Manifest data per package loaded from the packages local JSON.
        self._pkg_manifest_local: Optional[Dict[str, Dict[str, Any]]] = None
        self._pkg_manifest_remote: Optional[Dict[str, Dict[str, Any]]] = None
        self._pkg_manifest_remote_mtime = 0
        # Avoid many noisy prints.
        self._pkg_manifest_remote_has_warning = False

    def _json_data_ensure(
            self,
            *,
            error_fn: Callable[[BaseException], None],
            check_files: bool = False,
            ignore_missing: bool = False,
    ) -> Any:
        if self._pkg_manifest_remote is not None:
            if check_files:
                self._json_data_refresh(error_fn=error_fn)
            return self._pkg_manifest_remote

        filepath_json = os.path.join(self.directory, REPO_LOCAL_JSON)

        try:
            self._pkg_manifest_remote = json_from_filepath(filepath_json)
        except BaseException as ex:
            self._pkg_manifest_remote = None
            error_fn(ex)

        self._pkg_manifest_local = None
        if self._pkg_manifest_remote is not None:
            json_mtime = file_mtime_or_none(filepath_json)
            assert json_mtime is not None
            self._pkg_manifest_remote_mtime = json_mtime
            self._pkg_manifest_local = None
            self._pkg_manifest_remote_has_warning = False
        else:
            if not ignore_missing:
                # NOTE: this warning will occur when setting up a new repository.
                # It could be removed but it's also useful to know when the JSON is missing.
                if self.repo_url:
                    if not self._pkg_manifest_remote_has_warning:
                        print("Repository file:", filepath_json, "not found, sync required!")
                        self._pkg_manifest_remote_has_warning = True

        return self._pkg_manifest_remote

    def _json_data_refresh_from_toml(
            self,
            *,
            error_fn: Callable[[BaseException], None],
            force: bool = False,
    ) -> None:
        assert self.repo_url == ""
        # Since there is no remote repo the ID name is defined by the directory name only.
        local_json_data = self.pkg_manifest_from_local_ensure(error_fn=error_fn)
        if local_json_data is None:
            return

        filepath_json = os.path.join(self.directory, REPO_LOCAL_JSON)
        with open(filepath_json, "w", encoding="utf-8") as fh:
            # Indent because it can be useful to check this file if there are any issues.
            fh.write(json.dumps(local_json_data, indent=2))

    def _json_data_refresh(
            self,
            *,
            error_fn: Callable[[BaseException], None],
            force: bool = False,
    ) -> None:
        if force or (self._pkg_manifest_remote is None) or (self._pkg_manifest_remote_mtime == 0):
            self._pkg_manifest_remote = None
            self._pkg_manifest_remote_mtime = 0
            self._pkg_manifest_local = None

        # Detect a local-only repository, there is no server to sync with
        # so generate the JSON from the TOML files.
        # While redundant this avoids having support multiple code-paths for local-only/remote repos.
        if self.repo_url == "":
            self._json_data_refresh_from_toml(error_fn=error_fn, force=force)

        filepath_json = os.path.join(self.directory, REPO_LOCAL_JSON)
        mtime_test = file_mtime_or_none(filepath_json)
        if self._pkg_manifest_remote is not None:
            # TODO: check the time of every installed package.
            if mtime_test == self._pkg_manifest_remote_mtime:
                return

        try:
            self._pkg_manifest_remote = json_from_filepath(filepath_json)
        except BaseException as ex:
            self._pkg_manifest_remote = None
            error_fn(ex)

        self._pkg_manifest_local = None
        if self._pkg_manifest_remote is not None:
            json_mtime = file_mtime_or_none(filepath_json)
            assert json_mtime is not None
            self._pkg_manifest_remote_mtime = json_mtime

    def pkg_manifest_from_local_ensure(
            self,
            *,
            error_fn: Callable[[BaseException], None],
            ignore_missing: bool = False,
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        # Important for local-only repositories (where the directory name defines the ID).
        has_remote = self.repo_url != ""

        if self._pkg_manifest_local is None:
            self._json_data_ensure(
                ignore_missing=ignore_missing,
                error_fn=error_fn,
            )
            pkg_manifest_local = {}
            try:
                dir_entries = os.scandir(self.directory)
            except BaseException as ex:
                dir_entries = None
                error_fn(ex)

            for entry in (dir_entries if dir_entries is not None else ()):
                # Only check directories.
                if not entry.is_dir(follow_symlinks=True):
                    continue

                filename = entry.name

                # Simply ignore these paths without any warnings (accounts for `.git`, `__pycache__`, etc).
                if filename.startswith((".", "_")):
                    continue

                # Report any paths that cannot be used.
                if not filename.isidentifier():
                    error_fn(Exception("\"{:s}\" is not a supported module name, skipping".format(
                        os.path.join(self.directory, filename)
                    )))
                    continue

                filepath_toml = os.path.join(self.directory, filename, PKG_MANIFEST_FILENAME_TOML)
                try:
                    item_local = toml_from_filepath(filepath_toml)
                except BaseException as ex:
                    item_local = None
                    error_fn(ex)

                if item_local is None:
                    continue

                pkg_idname = item_local.pop("id")
                if has_remote:
                    # This should never happen, the user may have manually renamed a directory.
                    if pkg_idname != filename:
                        print("Skipping package with inconsistent name: \"{:s}\" mismatch \"{:s}\"".format(
                            filename,
                            pkg_idname,
                        ))
                        continue
                else:
                    pkg_idname = filename

                # Validate so local-only packages with invalid manifests aren't used.
                if (error_str := pkg_validate_data_or_error(pkg_idname, item_local, from_repo=False)):
                    error_fn(Exception(error_str))
                    continue

                pkg_manifest_local[pkg_idname] = item_local
            self._pkg_manifest_local = pkg_manifest_local
        return self._pkg_manifest_local

    def pkg_manifest_from_remote_ensure(
            self,
            *,
            error_fn: Callable[[BaseException], None],
            ignore_missing: bool = False,
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        if self._pkg_manifest_remote is None:
            self._json_data_ensure(
                ignore_missing=ignore_missing,
                error_fn=error_fn,
            )
        return self._pkg_manifest_remote

    def force_local_refresh(self) -> None:
        self._pkg_manifest_local = None


class RepoCacheStore:
    __slots__ = (
        "_repos",
        "_is_init",
    )

    def __init__(self) -> None:
        self._repos: List[_RepoCacheEntry] = []
        self._is_init = False

    def is_init(self) -> bool:
        return self._is_init

    def refresh_from_repos(
            self, *,
            repos: List[Tuple[str, str]],
            force: bool = False,
    ) -> None:
        """
        Initialize or update repositories.
        """
        repos_prev = {}
        if not force:
            for repo_entry in self._repos:
                repos_prev[repo_entry.directory, repo_entry.repo_url] = repo_entry
        self._repos.clear()

        for directory, repo_url in repos:
            repo_entry_test = repos_prev.get((directory, repo_url))
            if repo_entry_test is None:
                repo_entry_test = _RepoCacheEntry(directory, repo_url)
            self._repos.append(repo_entry_test)
        self._is_init = True

    def refresh_remote_from_directory(
            self,
            directory: str,
            *,
            error_fn: Callable[[BaseException], None],
            force: bool = False,
    ) -> None:
        for repo_entry in self._repos:
            if directory == repo_entry.directory:
                repo_entry._json_data_refresh(force=force, error_fn=error_fn)
                return
        raise ValueError("Directory {:s} not a known repo".format(directory))

    def refresh_local_from_directory(
            self,
            directory: str,
            *,
            error_fn: Callable[[BaseException], None],
            ignore_missing: bool = False,
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        for repo_entry in self._repos:
            if directory == repo_entry.directory:
                # Force refresh.
                repo_entry.force_local_refresh()
                return repo_entry.pkg_manifest_from_local_ensure(
                    ignore_missing=ignore_missing,
                    error_fn=error_fn,
                )
        raise ValueError("Directory {:s} not a known repo".format(directory))

    def pkg_manifest_from_remote_ensure(
            self,
            *,
            error_fn: Callable[[BaseException], None],
            check_files: bool = False,
            ignore_missing: bool = False,
    ) -> Generator[Optional[Dict[str, Dict[str, Any]]], None, None]:
        for repo_entry in self._repos:
            json_data = repo_entry._json_data_ensure(
                check_files=check_files,
                ignore_missing=ignore_missing,
                error_fn=error_fn,
            )
            if json_data is None:
                # The repository may be fresh, not yet initialized.
                yield None
            else:
                pkg_manifest_remote = {}
                for pkg_idname, item_remote in json_data.items():
                    pkg_manifest_remote[pkg_idname] = item_remote
                yield pkg_manifest_remote

    def pkg_manifest_from_local_ensure(
            self,
            *,
            error_fn: Callable[[BaseException], None],
            check_files: bool = False,
    ) -> Generator[Optional[Dict[str, Dict[str, Any]]], None, None]:
        if check_files:
            for repo_entry in self._repos:
                repo_entry.force_local_refresh()
        for repo_entry in self._repos:
            yield repo_entry.pkg_manifest_from_local_ensure(error_fn=error_fn)

    def clear(self) -> None:
        self._repos.clear()
        self._is_init = False


# -----------------------------------------------------------------------------
# Public Repo Lock
#


class RepoLock:
    """
    Lock multiple repositories, one or all may fail,
    it's up to the caller to check.

    Access via the ``RepoLockContext`` where possible to avoid the lock being left held.
    """
    __slots__ = (
        "_repo_directories",
        "_repo_lock_files",
        "_cookie",
        "_held",
    )

    def __init__(self, *, repo_directories: Sequence[str], cookie: str):
        """
        :arg repo_directories:
            Directories to attempt to lock.
        :arg cookie:
            A path which is used as a reference.
            It must point to a path that exists.
            When a lock exists, check if the cookie path exists, if it doesn't, allow acquiring the lock.
        """
        self._repo_directories = tuple(repo_directories)
        self._repo_lock_files: List[Tuple[str, str]] = []
        self._held = False
        self._cookie = cookie

    def __del__(self) -> None:
        if not self._held:
            return
        sys.stderr.write("{:s}: freed without releasing lock!".format(type(self).__name__))

    @staticmethod
    def _is_locked_with_stale_cookie_removal(local_lock_file: str, cookie: str) -> Optional[str]:
        if os.path.exists(local_lock_file):
            try:
                with open(local_lock_file, "r", encoding="utf8") as fh:
                    data = fh.read()
            except BaseException as ex:
                return "lock file could not be read: {:s}".format(str(ex))

            # The lock is held.
            if os.path.exists(data):
                if data == cookie:
                    return "lock is already held by this session"
                return "lock is held by other session: {:s}".format(data)

            # The lock is held (but stale), remove it.
            try:
                os.remove(local_lock_file)
            except BaseException as ex:
                return "lock file could not be removed: {:s}".format(str(ex))
        return None

    def acquire(self) -> Dict[str, Optional[str]]:
        """
        Return directories and the lock status,
        with None if locking succeeded.
        """
        if self._held:
            raise Exception("acquire(): called with an existing lock!")
        if not os.path.exists(self._cookie):
            raise Exception("acquire(): cookie doesn't exist! (when it should)")

        # Assume all succeed.
        result: Dict[str, Optional[str]] = {directory: None for directory in self._repo_directories}
        for directory in self._repo_directories:
            local_private_dir = os.path.join(directory, REPO_LOCAL_PRIVATE_DIR)

            # This most likely exists, create if it doesn't.
            if not os.path.isdir(local_private_dir):
                os.makedirs(local_private_dir)

            local_lock_file = os.path.join(local_private_dir, REPO_LOCAL_PRIVATE_LOCK)
            # Attempt to get the lock, kick out stale locks.
            if (lock_msg := self._is_locked_with_stale_cookie_removal(local_lock_file, self._cookie)) is not None:
                result[directory] = "Lock exists: {:s}".format(lock_msg)
                continue
            try:
                with open(local_lock_file, "w", encoding="utf8") as fh:
                    fh.write(self._cookie)
            except BaseException as ex:
                result[directory] = "Lock could not be created: {:s}".format(str(ex))
                # Remove if it was created (but failed to write)... disk-full?
                try:
                    os.remove(local_lock_file)
                except BaseException:
                    pass
                continue

            # Success, the file is locked.
            self._repo_lock_files.append((directory, local_lock_file))
        self._held = True
        return result

    def release(self) -> Dict[str, Optional[str]]:
        # NOTE: lots of error checks here, mostly to give insights in the very unlikely case this fails.
        if not self._held:
            raise Exception("release(): called without a lock!")

        result: Dict[str, Optional[str]] = {directory: None for directory in self._repo_directories}
        for directory, local_lock_file in self._repo_lock_files:
            if not os.path.exists(local_lock_file):
                result[directory] = "release(): lock missing when expected, continuing."
                continue
            try:
                with open(local_lock_file, "r", encoding="utf8") as fh:
                    data = fh.read()
            except BaseException as ex:
                result[directory] = "release(): lock file could not be read: {:s}".format(str(ex))
                continue
            # Owned by another application, this shouldn't happen.
            if data != self._cookie:
                result[directory] = "release(): lock was unexpectedly stolen by another program: {:s}".format(data)
                continue

            # This is our lock file, we're allowed to remove it!
            try:
                os.remove(local_lock_file)
            except BaseException as ex:
                result[directory] = "release(): failed to remove file {!r}".format(ex)

        self._held = False
        return result


class RepoLockContext:
    __slots__ = (
        "_repo_lock",
    )

    def __init__(self, *, repo_directories: Sequence[str], cookie: str):
        self._repo_lock = RepoLock(repo_directories=repo_directories, cookie=cookie)

    def __enter__(self) -> Dict[str, Optional[str]]:
        return self._repo_lock.acquire()

    def __exit__(self, _ty: Any, _value: Any, _traceback: Any) -> None:
        self._repo_lock.release()