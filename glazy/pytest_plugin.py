"""
Auto-loaded common fixtures for helping with unit-testing.

.. important:: Very Important!  Don't import this module!
    pytest should automatically import this via it's plugin mechanism.
    If you import any of the fixtures below manually, you may get something like this:

    `ValueError: duplicate 'glazy_test_context'`

    You should be able to use any of these fixtures without importing them.
    This is accomplished via the setup.py file in glazy, it tells pytest about the
    `glazy.fixtures` module so it can load them automatically.


    For `glazy_test_context` fixture it's self... it's an auto-use fixture,
    so it's automatically used anyway.

    I would probably just get the current context like you normally would
    (via `glazy.context.Context.current`), rather than use this fixture directly
    in your unit-test.
"""
import pytest


@pytest.fixture(autouse=True)
@pytest.mark.order(-1300)
def glazy_test_context():
    """
    Will blank-out the app and root contexts by allocating new containers
    for the root contexts.

    This means that, the first time a thread asks/needs a Context, one will be created lazily
    after the unit test starts since we removed all of them from the global state.

    This fixture is also using the `autouse=True` feature of pytest, to ensure this always runs.
    You don't need to use it directly,
    simply call `glazy.context.Context.current` like you normally would if you need the
    current context during your unit-test.

    After the unit test is finished, this auto-use fixture will clean up the state again.

    It's important that this is the first fixture that runs,
    so we marked it with a -1300 fixture order, helping to ensure that it runs first.

    There is nothing special about the number per-se,
    it's just sufficiently low, at least compared to all of our own fixtures in our own codebase.
    """

    # Want to keep global-module slate clean, import stuff we need privately.
    from .context import (
        Context, _setup_blank_app_and_thread_root_contexts_globals
    )

    # Ensure we have a blank slate for the unit-test.
    # This will allocate brand new, blank global app+thread root-contexts.
    _setup_blank_app_and_thread_root_contexts_globals()

    # Yield the current thread-root context as the fixture-value.
    yield Context.current()

    # Ensure app+thread root-contexts do not have leftover resource objects from unit test.
    _setup_blank_app_and_thread_root_contexts_globals()

