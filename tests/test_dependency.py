import dataclasses

import pytest as pytest

from xinject import CurrentDependencyProxy, XContext, Dependency
from xinject.context import _setup_blank_app_and_thread_root_contexts_globals
from xinject.dependency import DependencyPerThread


class MyClass(Dependency):
    def __init__(self):
        self._my_value = "b"

    def my_method(self):
        return self._my_value

    @property
    def my_prop(self):
        return self._my_value

    @my_prop.setter
    def my_prop(self, value):
        self._my_value = value


my_class = CurrentDependencyProxy.wrap(MyClass)
my_class_via_proxy_method = MyClass.proxy()


def test_proxy_wrapper():
    for current_class in [my_class, my_class_via_proxy_method]:
        with XContext(dependencies=[MyClass()]):
            assert_myclass("b")

            current_class.my_prop = "c"
            assert_myclass("c")

            current_class.other = 3
            assert current_class.other == 3

        assert_myclass("b")
        with pytest.raises(AttributeError):
            assert current_class.other == 3


def assert_myclass(param):
    assert my_class.my_prop == param
    assert my_class.my_method() == param
    assert my_class_via_proxy_method.my_prop == param
    assert my_class_via_proxy_method.my_method() == param
    assert MyClass.grab().my_prop == param
    assert MyClass.grab().my_method() == param


def test_shared_threaded_resource():
    # Test to ensure that the app-root and thread-root work correctly with
    # thread safe/unsafe dependencies.

    class ThreadSharableDependency(Dependency):
        hello = "1"

    class NonThreadSharableDependency(DependencyPerThread):
        hello2 = "a"

    ThreadSharableDependency.grab().hello = "3"
    NonThreadSharableDependency.grab().hello2 = "b"

    assert ThreadSharableDependency.grab().hello == "3"
    assert NonThreadSharableDependency.grab().hello2 == "b"

    thread_out_sharable = None
    thread_out_nonsharable = None

    # This is the root-func for a separate thread.
    def thread_func():
        # Want to write-to these in outer scope.
        nonlocal thread_out_sharable
        nonlocal thread_out_nonsharable

        # This should produce an '3', since dependency can be shared between threads.
        thread_out_sharable = ThreadSharableDependency.grab().hello

        # This should produce an 'a', since the dependency is NOT shared between threads;
        # the setting of it to 'b' above is in another thread and is NOT shared.
        thread_out_nonsharable = NonThreadSharableDependency.grab().hello2

    import threading

    # Create thread
    other_thread = threading.Thread(
        name='TestThread',
        target=thread_func,
        args=[]
    )

    # Startup Thread
    other_thread.start()

    # Wait for thread to finish
    other_thread.join()

    # Check to see if the thread safe/unsafe dependencies worked correctly.
    assert thread_out_sharable == "3"
    assert thread_out_nonsharable == "a"


def test_dep_as_decorator():
    @dataclasses.dataclass
    class MyDep(Dependency):
        some_value: str = 'my-value'

    # This ensures we don't have any thread-root context's,
    # which is important for testing to make sure a specific bug is fixed.
    # (the pytest-plugin already creates a blank thread-root-context for us,
    #  so we clear it again here)
    _setup_blank_app_and_thread_root_contexts_globals(keep_global_context=True)

    @MyDep(some_value='new-value')
    def my_func():
        return MyDep.grab().some_value

    assert my_func() == 'new-value'


def test_proxy_attribute():
    @dataclasses.dataclass
    class MyData:
        some_data: str = 'hello'

    class MyDep(Dependency):
        def __init__(self, my_data: MyData = None):
            if not my_data:
                my_data = MyData(some_data='data-value')
            self.my_data = my_data

    proxy__my_data: MyData = MyDep.proxy_attribute('my_data')

    assert proxy__my_data.some_data == 'data-value'
    with MyDep(my_data=MyData(some_data='new-value')):
        # Proxy should find the newly injected MyData object with its new value.
        assert proxy__my_data.some_data == 'new-value'

    # Original MyData object is restored
    assert proxy__my_data.some_data == 'data-value'
