import os
import signal
import sys

sys.dont_write_bytecode = True

from engine import Engine


def expired(signum, frame):
    os._exit(124)


if __name__ == "__main__":
    engine = Engine(sys.argv[1])
    mode, batch_id = sys.argv[2:4]
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(40)
    try:
        engine.collect(mode, batch_id)
    except Exception as error:
        with engine.locked(mode) as directory:
            state = engine.load(directory)
            if state.get("batch_id") == batch_id and state["phase"] == "RUNNING":
                state.update(phase="FAILED", error="后台抓取失败：" + str(error)[:300])
                engine.save(directory, state)
    finally:
        signal.alarm(0)
