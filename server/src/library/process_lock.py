# TODO: update the ProcessLock in python_framework
# TODO: add generator

from threading import Lock
from python_framework.thread_safe_cache import ThreadSafeCache


class ProcessLock:

    _locks: ThreadSafeCache[str, Lock]
    _locks_lock: Lock

    def __init__(self):
        self._locks = ThreadSafeCache()
        self._locks_lock = Lock()

    # NOTE: THIS IS NOT SAFE ACROSS MULTIPLE INSTANCES
    def release_lock(self, lock_id: str) -> None:
        if lock_id not in self._locks:
            return

        self._locks[lock_id].release()
        del self._locks[lock_id]

    # NOTE: THIS IS NOT SAFE ACROSS MULTIPLE INSTANCES
    def acquire_lock(self, lock_id: str, timeout: float = -1) -> bool:
        _acquired_internal_lock = False

        if lock_id in self._locks:
            return self._locks[lock_id].acquire(timeout=timeout)

        try:
            if not self._locks_lock.acquire(timeout=timeout):
                return False

            _acquired_internal_lock = True

            lock = Lock() if lock_id not in self._locks else self._locks[lock_id]
            locked = lock.acquire(timeout=timeout)
            self._locks[lock_id] = lock

            return locked
        finally:
            if _acquired_internal_lock:
                self._locks_lock.release()
