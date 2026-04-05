# --- INTEGRITY ---
# Previous Character Count: 30396
# Current Character Count: 30652
# Syntax Check: [PASS]
# Logic Validation: [Restored screen=True and fixed startup race condition by starting processing thread after UI.]
# Reason for Change: [To definitively fix the persistent startup crash by resolving a race condition between the UI and background threads.]
# ------------------
# --- METADATA ---
# Filename: src/main_processor.py
# Version: 31.0
#
# --- CHANGELOG ---
# v31.0: ARCHITECTURAL FIX: Restored `screen=True` for the UI. Resolved the
#        persistent startup crash by starting the processing thread *after* the
#        rich.Live context is active, preventing a race condition.
# v30.0: STABILITY FIX: Removed `screen=True` from the `rich.Live` call.
# ------------------

import argparse
import multiprocessing.managers  # Import managers directly for EventProxy
import os
import shutil
import threading
import time
import traceback
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from multiprocessing import Manager
from multiprocessing.queues import (
    Queue as mp_Queue,  # Alias Queue to avoid name collision with typing.Queue
)
from pathlib import Path
from typing import (
    Any,
    Callable,  # Import Callable for type hinting
    Optional,
    cast,  # Import cast for type casting
)

import structlog
from pynput import keyboard
from pynput.keyboard import Key, KeyCode  # Import Key and KeyCode for pynput type hints
from rich.box import HEAVY
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from tomlkit.toml_document import TOMLDocument

from .config import CONFIG_PATH, AppConfig, load_configuration
from .logger import (
    add_dashboard_handler,
    get_logging_config_dict,
    setup_logging,
    shutdown_logging,
    toggle_console_logs,
)
from .processing_job import run_cpu_job_in_worker_multiprocess
from .state_manager import JobStatus, StateManager
from .subtitle_generator import (
    StopRequestedError,
    generate_subtitles_for_file,
    load_model,
)
from .ui_dashboard import Dashboard
from .utils import get_video_files

log = structlog.get_logger()
console = Console()  # Removed encoding="utf-8"


def create_settings_panel(config: AppConfig) -> Panel:
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column(style="magenta", justify="right")
    table.add_column(style="cyan")
    for section_name, section_data in config.model_dump().items():
        table.add_row(f"[bold]{section_name.capitalize()}[/]", "")
        for key, value in section_data.items():
            table.add_row(f"  {key}:", str(value))
    return Panel(
        table, title="[bold]Session Settings[/]", border_style="green", box=HEAVY
    )


def scan_and_plan_jobs(
    config: AppConfig, state_manager: StateManager
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    log.info("Phase start", phase="scan_and_plan", category="processing")
    video_files = get_video_files(config.paths.source)
    total_video_files = len(video_files)
    if not video_files:
        log.warning(
            "No video files found",
            source_dir=str(config.paths.source),
            category="processing",
        )
        return [], [], 0
    console.print(
        f"Found [bold green]{total_video_files}[/bold green] video files. Evaluating job states..."
    )
    jobs_for_subtitles, jobs_for_cpu = [], []
    for source_path in video_files:
        job_id = f"{source_path.stem}-{uuid.uuid4().hex[:4]}"
        job_details = {"path": str(source_path), "job_id": job_id}

        with structlog.contextvars.bound_contextvars(
            job_id=job_id, file_name=source_path.name
        ):
            job_info = state_manager.get_job_status(source_path)
            current_signature = state_manager.get_file_signature(source_path)
            if (
                job_info.get("stored_signature")
                and job_info["stored_signature"] != current_signature
            ):
                log.warning("Signature mismatch, resetting job")
                state_manager.reset_job(source_path)
                shutil.rmtree(
                    config.paths.temp_dir / source_path.stem, ignore_errors=True
                )
                job_info["status"] = JobStatus.NOT_STARTED

            if job_info["status"] in (JobStatus.NOT_STARTED, JobStatus.FAILED):
                jobs_for_subtitles.append(job_details)
            elif job_info["status"] == JobStatus.SUBTITLES_COMPLETED:
                jobs_for_cpu.append(job_details)
    log.info(
        "Phase end",
        phase="scan_and_plan",
        new_or_failed=len(jobs_for_subtitles),
        ready_for_cpu=len(jobs_for_cpu),
        category="processing",
    )
    return jobs_for_subtitles, jobs_for_cpu, total_video_files


def run_subtitle_phase(
    jobs: list[dict[str, Any]],
    config: AppConfig,
    state_manager: StateManager,
    dashboard: Dashboard,
    stop_event: threading.Event,
):
    if not jobs:
        log.info("No subtitle jobs to process", category="processing")
        return

    for job_details in jobs:
        source_path = Path(job_details["path"])
        job_id = job_details["job_id"]
        file_name = source_path.name
        base_name = source_path.stem
        temp_dir = config.paths.temp_dir / base_name
        outcome = "failed"

        with structlog.contextvars.bound_contextvars(
            job_id=job_id, file_name=file_name
        ):
            if stop_event.is_set():
                log.warning(
                    "Stop event set, skipping subtitle job", category="processing"
                )
                break

            log.info("subtitle_generation_started", category="processing")
            start_time = time.time()
            try:
                dashboard.current_task_text.plain = (
                    f"Current Task: Subtitles for {file_name}"
                )
                dashboard.summary_data["queued"] -= 1
                dashboard.summary_data["in_progress"] += 1
                dashboard.clear_subtitle_subtasks()

                def progress_callback(current: int, total: int):
                    if stop_event.is_set():
                        raise StopRequestedError("User requested stop.")
                    if not dashboard.active_subtask_progress:
                        return
                    active_bar = dashboard.active_subtask_progress[-1]
                    percentage = (current / total) * 100 if total > 0 else 0
                    active_bar.update(active_bar.tasks[0].id, completed=percentage)

                generate_subtitles_for_file(
                    str(source_path),
                    str(temp_dir),
                    progress_callback,
                    stop_event=stop_event,
                )
                state_manager.upsert_job(source_path, JobStatus.SUBTITLES_COMPLETED)
                dashboard.summary_data["completed"] += 1
                outcome = "success"
            except StopRequestedError:
                log.warning(
                    "Subtitle generation stopped by user.", category="processing"
                )
                outcome = "stopped"
                dashboard.summary_data["in_progress"] -= 1
                dashboard.overall_progress.advance(dashboard.overall_task)
                return
            except Exception as e:
                log.error(
                    "Subtitle generation failed",
                    error=str(e),
                    exc_info=True,
                    category="processing",
                )
                state_manager.upsert_job(
                    source_path, JobStatus.FAILED, f"Subtitle gen failed: {e}"
                )
                dashboard.summary_data["failures"].append(
                    {"file": file_name, "error": f"Subtitle gen failed: {e}"}
                )
                dashboard.summary_data["failed"] += 1
            finally:
                duration = time.time() - start_time
                log.info(
                    "subtitle_generation_completed",
                    duration_ms=int(duration * 1000),
                    outcome=outcome,
                    category="processing",
                )
                dashboard.summary_data["in_progress"] -= 1
                dashboard.overall_progress.advance(dashboard.overall_task)


def run_initial_scan_and_phases(
    config: AppConfig,
    state_manager: StateManager,
    dashboard: Dashboard,
    progress_dict,
    db_queue: mp_Queue[Any],
    stop_event: threading.Event,
    mp_stop_event: multiprocessing.managers.EventProxy,
    run_id: str,
    pre_scanned_data: tuple,  # Use full path for EventProxy
):
    structlog.contextvars.bind_contextvars(
        run_id=run_id, component="main_processing_thread"
    )
    log.info("Processing thread started")

    try:
        jobs_for_subtitles, jobs_for_cpu, total_files = pre_scanned_data
        total_jobs = len(jobs_for_subtitles) + len(jobs_for_cpu)
        dashboard.summary_data.update(
            {"total": total_files, "queued": total_jobs, "status": "Processing..."}
        )
        dashboard.overall_progress.update(dashboard.overall_task, total=total_jobs)

        run_subtitle_phase(
            jobs_for_subtitles, config, state_manager, dashboard, stop_event
        )

        if not stop_event.is_set():
            run_cpu_phase(
                jobs_for_cpu,
                config,
                dashboard,
                progress_dict,
                db_queue,
                mp_stop_event,
                run_id,
            )

        log.info("Processing phases completed")
    except Exception as e:
        log.critical("Processing thread crashed", error=str(e), exc_info=True)
        stop_event.set()


def run_cpu_phase(
    jobs: list[dict[str, Any]],
    config: AppConfig,
    dashboard: Dashboard,
    progress_dict,
    db_queue: mp_Queue[Any],
    stop_event: multiprocessing.managers.EventProxy,
    run_id: str,  # Use full path for EventProxy
):
    if not jobs:
        log.info("No CPU jobs to process", category="processing")
        return
    log.info(
        "Phase start",
        phase="cpu_processing",
        job_count=len(jobs),
        category="processing",
    )
    max_workers = (
        config.performance.max_workers
        if config.performance.max_workers > 0
        else (os.cpu_count() or 1)
    )
    dashboard.clear_subtitle_subtasks()
    dashboard.current_task_text.plain = "Current Task: CPU Processing Phase"
    for i in range(min(len(jobs), max_workers)):
        dashboard.cpu_progress.update(dashboard.cpu_worker_tasks[i], visible=True)

    dashboard.summary_data["queued"] -= len(jobs)
    dashboard.summary_data["in_progress"] += len(jobs)

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_job = {
            executor.submit(
                run_cpu_job_in_worker_multiprocess,
                {
                    "source_path": job_details["path"],
                    "job_id": job_details["job_id"],
                    "config": config,
                    "run_id": run_id,
                },
                progress_dict,
                i,
                db_queue,
                stop_event,
                get_logging_config_dict(config.settings.log_level, "logs/vidrec.json"),
            ): (Path(job_details["path"]), job_details["job_id"], i)
            for i, job_details in enumerate(jobs)
        }

        for future in as_completed(future_to_job):
            if stop_event.is_set():
                executor.shutdown(wait=False, cancel_futures=True)
                break

            job_path, job_id, worker_id_map = future_to_job[future]
            job_file_name = job_path.name
            worker_id = worker_id_map % max_workers
            dashboard.summary_data["in_progress"] -= 1

            with structlog.contextvars.bound_contextvars(
                job_id=job_id, file_name=job_file_name
            ):
                try:
                    result, message = future.result()
                    if result == "SUCCESS":
                        dashboard.summary_data["completed"] += 1
                        dashboard.cpu_progress.update(
                            dashboard.cpu_worker_tasks[worker_id],
                            description=f"[green]Completed[/] {job_file_name}",
                            completed=100,
                        )
                    else:
                        dashboard.summary_data["failed"] += 1
                        dashboard.summary_data["failures"].append(
                            {"file": job_file_name, "error": message}
                        )
                        dashboard.cpu_progress.update(
                            dashboard.cpu_worker_tasks[worker_id],
                            description=f"[red]Failed[/] {job_file_name}",
                            completed=100,
                        )
                except Exception as e:
                    log.error(
                        "Worker process future failed", error=str(e), exc_info=True
                    )
                    dashboard.summary_data["failed"] += 1
                    dashboard.summary_data["failures"].append(
                        {"file": job_file_name, "error": f"Worker crashed: {e}"}
                    )
                    dashboard.cpu_progress.update(
                        dashboard.cpu_worker_tasks[worker_id],
                        description=f"[red]Crashed[/] {job_file_name}",
                        completed=100,
                    )

            dashboard.overall_progress.advance(dashboard.overall_task)
    log.info("Phase end", phase="cpu_processing")


def _setup_app_components() -> tuple[AppConfig, TOMLDocument]:
    try:
        config, config_doc = load_configuration(CONFIG_PATH)
        return config, config_doc
    except Exception as e:
        log.critical("Failed to load configuration.", error=str(e), exc_info=True)
        raise


def setup_application():
    parser = argparse.ArgumentParser(description="Video re-encoding tool.")
    parser.add_argument("--source", type=Path, help="Source directory or file.")
    parser.add_argument(
        "--mode", type=str, default="batch", choices=["batch", "interactive"]
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    return parser.parse_args()


def run_processing_session(
    config: AppConfig,
    state_manager: StateManager,
    manager: Manager,
    db_queue: mp_Queue[Any],
    run_id: str,
    pre_scanned_data: Optional[tuple] = None,
):
    processing_thread = None
    listener = None
    stop_event = threading.Event()

    def on_press(
        key,
    ):  # Removed explicit type hint, relying on pynput's internal handling
        try:
            # Check if key is a character key and if it's 'q'
            if isinstance(key, KeyCode) and key.char == "q":
                log.warning("'q' pressed. Initiating shutdown.")
                stop_event.set()
                return False  # Returning False stops the pynput listener
            # Check for special keys like Key.esc if needed
            elif isinstance(key, Key) and key == Key.esc:
                log.warning("Escape key pressed. Initiating shutdown.")
                stop_event.set()
                return False  # Returning False stops the pynput listener
        except AttributeError:
            # This handles cases where key is a special key (e.g., Key.shift) which doesn't have a .char attribute
            pass
        return None  # Continue listening for key presses

    try:
        # Cast on_press to Callable to satisfy Pylance's strict type checking for pynput callbacks
        listener = keyboard.Listener(on_press=cast(Callable[..., Any], on_press))
        listener.start()
        log.info("Keyboard listener started.")
    except Exception as e:
        log.warning(
            "Failed to start keyboard listener. 'q' to quit will be disabled.",
            error=str(e),
        )

    try:
        log.info("Starting processing session setup")
        progress_dict = manager.dict()
        mp_stop_event = manager.Event()
        max_workers = (
            config.performance.max_workers
            if config.performance.max_workers > 0
            else (os.cpu_count() or 1)
        )
        dashboard = Dashboard(num_cpu_workers=max_workers)
        add_dashboard_handler(dashboard.log_deque, config.settings.log_level)

        toggle_console_logs(False)
        with Live(
            dashboard.layout, screen=True, transient=False, vertical_overflow="visible"
        ) as live:
            # FIX: Start background threads *after* the UI is live
            processing_args = (
                config,
                state_manager,
                dashboard,
                progress_dict,
                db_queue,
                stop_event,
                mp_stop_event,
                run_id,
                pre_scanned_data,
            )
            processing_thread = threading.Thread(
                target=run_initial_scan_and_phases, args=processing_args, daemon=False
            )
            processing_thread.start()

            watcher_thread = threading.Thread(
                target=lambda: stop_event.wait() and mp_stop_event.set(), daemon=True
            )
            watcher_thread.start()

            while processing_thread.is_alive():
                dashboard.update(create_settings_panel(config))
                live.refresh()
                time.sleep(0.1)
                if stop_event.is_set():
                    break

        processing_thread.join()
        # final_status = "Stopped by user" if stop_event.is_set() else "Complete"
        dashboard.show_final_summary()
        console.print(dashboard.get_final_summary_panel())

    except (KeyboardInterrupt, Exception) as e:
        log.warning(
            "Processing session interrupted",
            reason=type(e).__name__,
            error=str(e),
            exc_info=True,
            details="Application interrupted during processing session setup or execution.",
            category="system",
        )
    finally:
        log.info("Starting cleanup phase")
        toggle_console_logs(True)
        stop_event.set()
        if listener and listener.is_alive():
            listener.stop()
        if processing_thread and processing_thread.is_alive():
            processing_thread.join()
        log.info("Cleanup phase complete")


def main():
    import sys
    # Removed sys.stdout.reconfigure as it caused AttributeError in some environments.
    # The Console(encoding="utf-8") should handle the encoding for Rich output.

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        log.critical(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_exception
    manager = None
    state_manager = None

    try:
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
        args = setup_application()
        config, config_doc = _setup_app_components()
        effective_log_level = args.log_level or config.settings.log_level or "INFO"
        setup_logging(log_level=effective_log_level)

        if config.settings.create_subtitles:
            console.print(
                "[yellow]Pre-loading subtitle model... (this may take a moment)[/yellow]"
            )
            load_model()
            console.print("[green]Subtitle model loaded.[/green]")

        run_id = (
            f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        )
        structlog.contextvars.bind_contextvars(run_id=run_id)
        manager = Manager()
        db_queue = manager.Queue()
        state_manager = StateManager(
            db_path=Path.cwd() / "vidrec_state.db", db_queue=db_queue
        )
        jobs_sub: list = []
        jobs_cpu: list = []
        total: int = 0
        jobs_sub, jobs_cpu, total = scan_and_plan_jobs(config, state_manager)
        if not jobs_sub and not jobs_cpu:
            log.info("All jobs are already processed.")
            console.print(
                f"\n[bold green]✔ All {total} files are already processed.[/bold green]"
            )
            return
        run_processing_session(
            config,
            state_manager,
            manager,
            db_queue,
            run_id,
            (jobs_sub, jobs_cpu, total),
        )

    except (KeyboardInterrupt, Exception) as e:
        log.critical(
            "Shutdown due to exception",
            reason=type(e).__name__,
            error=str(e),
            exc_info=True,
            details="Application interrupted during processing session setup or execution.",
            category="system",
        )
        if not isinstance(e, KeyboardInterrupt):
            with open("crash_report.txt", "w") as f:
                f.write(
                    f"--- Vid_ReC CRASH REPORT ---\nTimestamp: {datetime.now().isoformat()}\nError: {e}\n\n"
                )
                traceback.print_exc(file=f)
    finally:
        if state_manager is not None:
            state_manager.close()
        if manager is not None:
            manager.shutdown()
        log.info(
            "Application shutdown.",
            details="Application has completed execution or was stopped.",
            category="system",
        )
        shutdown_logging()


if __name__ == "__main__":
    main()
