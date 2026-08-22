import os
import glob
import asyncio
import logging
import subprocess
import config
from engine.log_setup import setup_logging
from engine.train_pipeline import train_models
from engine.core import ZeroContextEngine
from engine.database import AsyncThreatDB

setup_logging(config.TEMP_DIR)
log = logging.getLogger("zero_context.main")


def get_kali_keyboard_path():
    """Resolves the dynamic keyboard event path native to Kali Linux udev rules."""
    for path in glob.glob("/dev/input/by-path/*-kbd"):
        return path

    log.warning("Could not auto-detect keyboard in /by-path/. Defaulting to event0.")
    return "/dev/input/event0"


async def main():
    # 1. Auto-compile the C++ daemon if needed (blocking is fine here)
    if not os.path.exists(config.SENSOR_BIN):
        log.info("Compiling multi-threaded C++ daemon...")
        try:
            subprocess.run(
                ["g++", "-pthread", "-O3", config.SENSOR_SRC, "-o", config.SENSOR_BIN],
                check=True,
            )
            log.info("Compilation successful.")
        except subprocess.CalledProcessError:
            log.error("FATAL: Compilation failed.")
            raise SystemExit(1)

    active_kbd_path = get_kali_keyboard_path()

    # 2. Launch the C++ daemon in the background (non-blocking)
    log.info("Launching C++ sensor daemon with root privileges...")
    log.info("Note: you may be prompted for your sudo password.")
    sensor_process = subprocess.Popen(["sudo", config.SENSOR_BIN, active_kbd_path])

    # 3. Start the Python UDS server
    for sock in [config.UDS_MOUSE, config.UDS_KBD]:
        if os.path.exists(sock):
            os.remove(sock)

    db = AsyncThreatDB(
        host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASS, db=config.DB_NAME
    )
    await db.connect()

    engine = ZeroContextEngine(config, db)
    mouse_server = await asyncio.start_unix_server(engine.handle_mouse, path=config.UDS_MOUSE)
    kbd_server = await asyncio.start_unix_server(engine.handle_keyboard, path=config.UDS_KBD)

    log.info(f"ZeroContext backend listening on {config.UDS_MOUSE}")

    try:
        async with mouse_server, kbd_server:
            await asyncio.gather(mouse_server.serve_forever(), kbd_server.serve_forever())
    except asyncio.CancelledError:
        pass
    finally:
        # 4. Clean up the C++ process and DB pool, and remove stale sockets,
        #    no matter how the server loop exits.
        log.info("Shutting down C++ sensor daemon...")
        sensor_process.terminate()
        try:
            sensor_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            sensor_process.kill()

        for sock in [config.UDS_MOUSE, config.UDS_KBD]:
            if os.path.exists(sock):
                os.remove(sock)

        await db.close()


if __name__ == "__main__":
    try:
        os.remove(os.path.join(config.TEMP_DIR, "zero_context_telemetry.jsonl"))
        log.info("Old telemetry ledger cleared.")
    except FileNotFoundError:
        pass
    except OSError as e:
        log.error(f"Failed to delete telemetry file: {e}")

    os.makedirs(config.MODEL_DIR, exist_ok=True)
    os.makedirs(config.TEMP_DIR, exist_ok=True)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("ZeroContext system halted by user.")
    finally:
        # Bug fix: previously train_models() sat after asyncio.run(main()) in
        # the try block, but main() only returns via KeyboardInterrupt, which
        # is caught by the except clause above before train_models() could
        # ever run. Placing it in `finally` guarantees the model gets
        # (re)trained on whatever telemetry was collected this session.
        log.info("Training models on collected telemetry...")
        train_models()
        log.info("ZeroContext lifecycle complete.")
