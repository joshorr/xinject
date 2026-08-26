import threading
import time

from xinject import Dependency, DependencyPerThread


THREAD_COUNT = 8


def _run_in_threads(target, count=THREAD_COUNT, timeout=10):
    """ Runs `target` on `count` threads, fails if any of them are still alive after `timeout`. """
    threads = [threading.Thread(target=target, daemon=True) for _ in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=timeout)

    alive = [t for t in threads if t.is_alive()]
    assert not alive, f"{len(alive)} thread(s) never finished; likely a deadlock"


def test_shared_dependency_is_only_created_once_across_threads():
    created = []
    created_lock = threading.Lock()
    at_the_gate = threading.Barrier(THREAD_COUNT, timeout=10)

    class SlowShared(Dependency):
        def __init__(self):
            # Widen the window between "nobody has one" and "it's in the context",
            # which is exactly the window the lock has to close.
            time.sleep(0.02)
            with created_lock:
                created.append(self)

    grabbed = []
    grabbed_lock = threading.Lock()

    def worker():
        # Get every thread into `grab()` at the same moment.
        at_the_gate.wait()
        obj = SlowShared.grab()
        with grabbed_lock:
            grabbed.append(obj)

    _run_in_threads(worker)

    assert len(created) == 1, f"lazily created {len(created)} instances, expected exactly 1"
    assert len(grabbed) == THREAD_COUNT
    assert all(obj is created[0] for obj in grabbed), "threads got different instances"


def test_per_thread_dependency_still_gets_one_per_thread():
    created = []
    created_lock = threading.Lock()
    at_the_gate = threading.Barrier(THREAD_COUNT, timeout=10)

    class SlowPerThread(DependencyPerThread):
        def __init__(self):
            time.sleep(0.02)
            with created_lock:
                created.append(self)

    def worker():
        at_the_gate.wait()
        first = SlowPerThread.grab()
        # Same thread asking twice must reuse, the lock must not change that.
        assert SlowPerThread.grab() is first

    _run_in_threads(worker)

    # The lock serializes creation but must not collapse per-thread dependencies into one.
    assert len(created) == THREAD_COUNT
    assert len({id(obj) for obj in created}) == THREAD_COUNT


def test_dependency_init_grabbing_another_does_not_deadlock():
    class Inner(Dependency):
        value = 'inner-value'

    class Outer(Dependency):
        def __init__(self):
            # Re-enters `XContext.dependency` while the lazy-create lock is already held by this
            # same thread; a non-reentrant lock would deadlock right here.
            self.from_inner = Inner.grab().value

    results = []
    results_lock = threading.Lock()

    def worker():
        with results_lock:
            results.append(Outer.grab().from_inner)

    _run_in_threads(worker)

    assert results == ['inner-value'] * THREAD_COUNT


def test_nested_lazy_creation_races_resolve_to_one_instance_each():
    at_the_gate = threading.Barrier(THREAD_COUNT, timeout=10)
    inner_created = []
    outer_created = []
    counter_lock = threading.Lock()

    class Inner(Dependency):
        def __init__(self):
            time.sleep(0.01)
            with counter_lock:
                inner_created.append(self)

    class Outer(Dependency):
        def __init__(self):
            time.sleep(0.01)
            self.inner = Inner.grab()
            with counter_lock:
                outer_created.append(self)

    grabbed = []
    grabbed_lock = threading.Lock()

    def worker():
        at_the_gate.wait()
        obj = Outer.grab()
        with grabbed_lock:
            grabbed.append(obj)

    _run_in_threads(worker)

    assert len(outer_created) == 1
    assert len(inner_created) == 1
    assert all(obj is outer_created[0] for obj in grabbed)
    assert Inner.grab() is inner_created[0]
