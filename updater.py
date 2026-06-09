import logging
import os
import shutil
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path


APP_EXE_NAME = "MyApp.exe"
UPDATER_EXE_NAME = "updater.exe"
LOG_FILE_NAME = "updater.log"

WAIT_POLL_SECONDS = 0.5
WAIT_TIMEOUT_SECONDS = 0
FILE_RETRY_COUNT = 10
FILE_RETRY_DELAY_SECONDS = 0.5


def usage():
    return (
        "Usage: updater.exe --zip <archive.zip> "
        "--install-dir <application directory> --pid <application pid>"
    )


def parse_args(argv):
    values = {
        "zip": "",
        "install_dir": "",
        "pid": "",
    }
    positionals = []
    index = 1

    while index < len(argv):
        token = argv[index]
        if token in ("--zip", "--archive"):
            index += 1
            if index >= len(argv):
                raise ValueError("--zip requires a value")
            values["zip"] = argv[index]
        elif token in ("--install-dir", "--target-dir", "--app-dir"):
            index += 1
            if index >= len(argv):
                raise ValueError("--install-dir requires a value")
            values["install_dir"] = argv[index]
        elif token == "--pid":
            index += 1
            if index >= len(argv):
                raise ValueError("--pid requires a value")
            values["pid"] = argv[index]
        elif token in ("--help", "-h", "/?"):
            raise ValueError(usage())
        else:
            positionals.append(token)
        index += 1

    if positionals:
        if len(positionals) != 3:
            raise ValueError(usage())
        values["zip"] = values["zip"] or positionals[0]
        values["install_dir"] = values["install_dir"] or positionals[1]
        values["pid"] = values["pid"] or positionals[2]

    if not values["zip"] or not values["install_dir"] or not values["pid"]:
        raise ValueError(usage())

    try:
        pid = int(values["pid"])
    except ValueError as exc:
        raise ValueError("PID must be an integer") from exc

    return Path(values["zip"]), Path(values["install_dir"]), pid


def configure_logging(install_dir):
    handlers = []
    log_path = install_dir / LOG_FILE_NAME

    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, mode="a", encoding="utf-8"))
    except OSError:
        fallback_dir = Path(tempfile.gettempdir()) / "MyApp"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        log_path = fallback_dir / LOG_FILE_NAME
        handlers.append(logging.FileHandler(log_path, mode="a", encoding="utf-8"))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )
    logging.info("=" * 60)
    logging.info("Updater started")
    logging.info("Log file: %s", log_path)


def creation_flags(*names):
    flags = 0
    for name in names:
        flags |= int(getattr(subprocess, name, 0) or 0)
    return flags


def process_running_windows(pid):
    command = ["tasklist", "/FI", f"PID eq {pid}", "/NH"]
    kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.DEVNULL,
    }
    flags = creation_flags("CREATE_NO_WINDOW")
    if flags:
        kwargs["creationflags"] = flags

    try:
        result = subprocess.run(command, **kwargs)
    except OSError as exc:
        logging.warning("Unable to run tasklist: %s", exc)
        return False

    output = result.stdout.decode(errors="ignore")
    pid_text = str(pid)
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == pid_text:
            return True
    return False


def process_running_posix(pid):
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def process_running(pid):
    if os.name == "nt":
        return process_running_windows(pid)
    return process_running_posix(pid)


def wait_for_process_exit(pid):
    if pid <= 0:
        raise RuntimeError("PID must be greater than zero")

    logging.info("Waiting for application process to exit: pid=%s", pid)
    started_at = time.time()
    while process_running(pid):
        elapsed = time.time() - started_at
        if WAIT_TIMEOUT_SECONDS > 0 and elapsed > WAIT_TIMEOUT_SECONDS:
            raise RuntimeError(f"Application process did not exit in {WAIT_TIMEOUT_SECONDS} seconds")
        time.sleep(WAIT_POLL_SECONDS)
    logging.info("Application process has exited")


def validate_inputs(zip_path, install_dir, pid):
    if pid <= 0:
        raise RuntimeError("PID must be greater than zero")
    if not zip_path.exists():
        raise RuntimeError(f"Update archive does not exist: {zip_path}")
    if not zip_path.is_file():
        raise RuntimeError(f"Update archive is not a file: {zip_path}")
    if not install_dir.exists():
        raise RuntimeError(f"Install directory does not exist: {install_dir}")
    if not install_dir.is_dir():
        raise RuntimeError(f"Install path is not a directory: {install_dir}")

    app_exe = install_dir / APP_EXE_NAME
    if not app_exe.exists():
        raise RuntimeError(f"Application executable was not found: {app_exe}")


def path_is_inside(path, root):
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def safe_extract_zip(zip_path, extract_dir):
    root = extract_dir.resolve()
    logging.info("Extracting archive: %s", zip_path)
    logging.info("Extraction directory: %s", extract_dir)

    with zipfile.ZipFile(zip_path, "r") as archive:
        for member in archive.infolist():
            member_name = member.filename.replace("\\", "/")
            while member_name.startswith("/"):
                member_name = member_name[1:]
            if not member_name:
                continue

            destination = (root / member_name).resolve()
            if not path_is_inside(destination, root):
                raise RuntimeError(f"Unsafe archive entry: {member.filename}")

            if member.is_dir() or member_name.endswith("/"):
                destination.mkdir(parents=True, exist_ok=True)
                continue

            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member, "r") as source:
                with open(destination, "wb") as target:
                    shutil.copyfileobj(source, target)

    logging.info("Archive extracted successfully")


def resolve_payload_root(extract_dir):
    if (extract_dir / APP_EXE_NAME).exists():
        logging.info("Payload root: %s", extract_dir)
        return extract_dir

    children = list(extract_dir.iterdir())
    directories = [path for path in children if path.is_dir()]
    files = [path for path in children if path.is_file()]

    if not files and len(directories) == 1 and (directories[0] / APP_EXE_NAME).exists():
        logging.info("Payload root: %s", directories[0])
        return directories[0]

    for directory in directories:
        if (directory / APP_EXE_NAME).exists():
            logging.info("Payload root: %s", directory)
            return directory

    raise RuntimeError(f"Archive does not contain {APP_EXE_NAME}")


def should_skip(relative_path):
    return relative_path.name.lower() == UPDATER_EXE_NAME.lower()


def collect_payload(payload_root):
    directory_set = set()
    files = []

    for current_root, dir_names, file_names in os.walk(payload_root):
        current_path = Path(current_root)

        for dir_name in dir_names:
            directory_path = current_path / dir_name
            relative_path = directory_path.relative_to(payload_root)
            directory_set.add(relative_path)

        for file_name in file_names:
            source_path = current_path / file_name
            relative_path = source_path.relative_to(payload_root)
            if should_skip(relative_path):
                logging.info("Skipping updater binary: %s", relative_path)
                continue
            parent_path = relative_path.parent
            while str(parent_path) != ".":
                directory_set.add(parent_path)
                parent_path = parent_path.parent
            files.append((source_path, relative_path))

    directories = list(directory_set)
    directories.sort(key=lambda path: (len(path.parts), str(path).lower()))
    files.sort(key=lambda item: str(item[1]).lower())
    logging.info("Payload directories: %s", len(directories))
    logging.info("Payload files to copy: %s", len(files))
    return directories, files


def remove_path(path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def backup_target(target_path, backup_path, backup_records):
    if target_path.exists():
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.is_dir() and not target_path.is_symlink():
            shutil.copytree(target_path, backup_path)
            kind = "dir"
        else:
            shutil.copy2(target_path, backup_path)
            kind = "file"
        backup_records.append(
            {
                "target": target_path,
                "backup": backup_path,
                "kind": kind,
            }
        )
        logging.info("Backed up %s: %s", kind, target_path)
        return

    backup_records.append(
        {
            "target": target_path,
            "backup": None,
            "kind": "missing",
        }
    )


def create_backups(files, install_dir, backup_dir):
    backup_records = []
    logging.info("Creating backups")

    for _source_path, relative_path in files:
        target_path = install_dir / relative_path
        backup_path = backup_dir / relative_path
        backup_target(target_path, backup_path, backup_records)

    logging.info("Backup records created: %s", len(backup_records))
    return backup_records


def create_payload_directories(directories, install_dir):
    created_dirs = []

    for relative_path in directories:
        target_dir = install_dir / relative_path
        if target_dir.exists() and not target_dir.is_dir():
            raise RuntimeError(f"Cannot create directory, file exists: {target_dir}")
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            created_dirs.append(target_dir)
            logging.info("Created directory: %s", target_dir)

    return created_dirs


def copy_file_with_retries(source_path, target_path):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    last_error = None

    for attempt in range(1, FILE_RETRY_COUNT + 1):
        try:
            if target_path.exists():
                remove_path(target_path)
            shutil.copy2(source_path, target_path)
            return
        except OSError as exc:
            last_error = exc
            logging.warning(
                "Copy attempt %s/%s failed for %s: %s",
                attempt,
                FILE_RETRY_COUNT,
                target_path,
                exc,
            )
            time.sleep(FILE_RETRY_DELAY_SECONDS)

    raise RuntimeError(f"Unable to copy {source_path} to {target_path}: {last_error}")


def copy_payload_files(files, install_dir):
    copied_count = 0
    for source_path, relative_path in files:
        target_path = install_dir / relative_path
        copy_file_with_retries(source_path, target_path)
        copied_count += 1
        logging.info("Copied: %s", relative_path)
    logging.info("Copied files: %s", copied_count)


def rollback(backup_records, created_dirs):
    logging.info("Starting rollback")

    for record in reversed(backup_records):
        target_path = record["target"]
        backup_path = record["backup"]
        kind = record["kind"]

        try:
            if kind == "missing":
                if target_path.exists():
                    remove_path(target_path)
                    logging.info("Removed new file during rollback: %s", target_path)
                continue

            if target_path.exists():
                remove_path(target_path)

            target_path.parent.mkdir(parents=True, exist_ok=True)
            if kind == "dir":
                shutil.copytree(backup_path, target_path)
            else:
                shutil.copy2(backup_path, target_path)
            logging.info("Restored %s: %s", kind, target_path)
        except OSError as exc:
            logging.exception("Rollback failed for %s: %s", target_path, exc)

    for directory in reversed(created_dirs):
        try:
            if directory.exists():
                directory.rmdir()
                logging.info("Removed empty directory during rollback: %s", directory)
        except OSError:
            pass

    logging.info("Rollback finished")


def apply_update(payload_root, install_dir, backup_dir):
    directories, files = collect_payload(payload_root)
    if not files:
        raise RuntimeError("Archive does not contain files to update")

    backup_records = []
    created_dirs = []

    try:
        backup_records = create_backups(files, install_dir, backup_dir)
        created_dirs = create_payload_directories(directories, install_dir)
        copy_payload_files(files, install_dir)
    except Exception:
        logging.exception("Update failed, rollback is required")
        rollback(backup_records, created_dirs)
        raise


def remove_file_quietly(path):
    try:
        if path.exists() and path.is_file():
            path.unlink()
            logging.info("Removed temporary file: %s", path)
    except OSError as exc:
        logging.warning("Unable to remove temporary file %s: %s", path, exc)


def launch_application(install_dir):
    app_exe = install_dir / APP_EXE_NAME
    if not app_exe.exists():
        raise RuntimeError(f"Updated executable was not found: {app_exe}")

    flags = creation_flags("DETACHED_PROCESS", "CREATE_NEW_PROCESS_GROUP", "CREATE_NO_WINDOW")
    kwargs = {
        "cwd": str(install_dir),
        "close_fds": True,
    }
    if flags:
        kwargs["creationflags"] = flags

    logging.info("Launching application: %s", app_exe)
    subprocess.Popen([str(app_exe)], **kwargs)


def run_update(zip_path, install_dir, pid):
    validate_inputs(zip_path, install_dir, pid)
    wait_for_process_exit(pid)

    workspace = Path(tempfile.mkdtemp(prefix="myapp_update_"))
    extract_dir = workspace / "extracted"
    backup_dir = workspace / "backup"
    extract_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    try:
        safe_extract_zip(zip_path, extract_dir)
        payload_root = resolve_payload_root(extract_dir)
        apply_update(payload_root, install_dir, backup_dir)
        remove_file_quietly(zip_path)
        logging.info("Update completed successfully")
    finally:
        try:
            shutil.rmtree(workspace, ignore_errors=True)
            logging.info("Removed workspace: %s", workspace)
        except OSError as exc:
            logging.warning("Unable to remove workspace %s: %s", workspace, exc)

    launch_application(install_dir)


def main():
    try:
        zip_path, install_dir, pid = parse_args(os.sys.argv)
    except Exception as exc:
        fallback_dir = Path(tempfile.gettempdir()) / "MyApp"
        configure_logging(fallback_dir)
        logging.exception("Invalid updater arguments: %s", exc)
        return 2

    configure_logging(install_dir)
    logging.info("Archive: %s", zip_path)
    logging.info("Install directory: %s", install_dir)
    logging.info("Application PID: %s", pid)

    try:
        run_update(zip_path, install_dir, pid)
    except Exception as exc:
        logging.exception("Updater failed: %s", exc)
        return 1

    logging.info("Updater finished")
    return 0


if __name__ == "__main__":
    os.sys.exit(main())
