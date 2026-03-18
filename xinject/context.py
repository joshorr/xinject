"""
Manage shared dependency and dependency injection.


# To Do First:

If you have not already, to get a nice high-level overview of library see either:

- project README.md here:
    - https://github.com/xyngular/py-xinject#documentation
- Or go to xinject module documentation at here:
    - [xinject, How To Use](./#how-to-use)


# Quick Start

## Please Read First

If your looking for a simple example/use of singltone-like dependencies,
go to `xinject.dependency.Dependency`.

The whole point of the `xinject.context.XContext` is to have a place to get shared dependencies.

Normally, code will use some other convenience methods, as an example:

Most of the time a dependency will inherit from `xinject.dependency.Dependency` and that
class provides a class method `xinject.dependency.Dependency.grab` to easily get a
dependency of the inherited type from the current context as a convenience.

So normally, code would do this to get the current object instance for a Resource:

>>> class SomeResource(Dependency):
>>>    my_attribute = "default-value"
>>>
>>> # Normally code would do this to interact with current Dependency subclass object:
>>> SomeResource.grab().my_attribute = "change-value"

Another convenient way to get the current dependency is via the
`xinject.proxy.CurrentDependencyProxy`. This class lets you create an object
that always acts like the current/active object for some Resource.
So you can define it at the top-level of some module, and code can import it
and use it directly.

I would start with [Fundamentals](#fundamentals) if you know nothing of how
`xinject.context.XContext` works and want to learn more about how it works.

Most of the time, you interact with Context indrectly via
`xinject.dependency.Dependency`.  So getting familiar with Context is more about
utilize more advance use-cases. I get into some of these advanced use-cases below.

.. important:: The below is for advanced use-cases and understanding.
    Look at `xinject.dependency.Dependency` or docs just above ^^^ for the normal use-case and
    examples / quick starts.

# Context Overview

Context is used to keep track of a set of dependencies. The dependencies are keyed off the class
type. IE: One dependency per-context per-dependency-type.

Main Classes:

- `xinject.context.XContext`: Container of dependencies, mapped by type.
- For Resource Subclasses:
    - `xinject.dependency.Dependency`: Nice interface to easily get the current dependency.
        Used to implment a something that should be shared and not generally duplicated,
        like a soft-singleton.

# Fundamentals

`xinject.context.XContext` is like a container, used to store various objects we are calling
dependencies.

Used to store various dependencies of any type  in general [ie: configs, auths, clients, etc].
All of these dependencies together represent a sort of "context" from which various pieces of code
can easily get them; that way they can 'share' the dependency when appropriate. This is a way
to do dependcy injection in a easier and more reliable way since you don't have to worry
about passing these dependencies around everywhere manually.

The values are mapped by their type.  When a dependency of a specific type is asked for,
the Context will return it if it finds it. If not found it will create it, add it to its self
and return it. Future calls will return this new dependency.

`xinject.context.XContext` can optionally have a parent. By default, a newly created/used Context
will use the current context Normally, dependencies are still normally created even if a
parent has a value, as long as the current context does not have one yet.

This behavior can be customized by the dependency, see one of these for details:

- `xinject.dependency.Dependency`
    - Useful for a shared/soft overridable shared object; where you can easily get the current
        version of it.


## Dependencies
[dependencies]: #dependencies

There are various ways to get dependencies from the current context. Let's say we have
a dependency called `SomeResourceType`:

>>> next_identifier = 0
>>> class SomeResourceType(Dependency):
...     def __init__(self):
...         global next_identifier
...         self.some_value = "hello!"
...         self.ident = next_identifier
...         next_identifier += 1

.. note:: SomeResourceType's `ident` field gets incremented and set on each newly created object.
    So the first SomeResoureType's `ident` will equal `0`,
    the second one created will be `1` and so forth.

If what you want inherits from `xinject.dependency.Dependency`, it has a nice class method that
returns the current dependency.
The easiest way to get the current dependency for the type in this case is
to call `xinject.dependency.Dependency.grab` on it's type like so:

>>> SomeResourceType.grab().some_value
'hello!'
>>> SomeResourceType.grab().ident
0

When a Context does not have the dependency, by default it will create it for you, as you
saw in the previous example.

`XContext.current()` will return the current Context if no params are passed in, or if a
type is passed in, it will return the current Context's dependency for the passed in type.

This means another way to grab dependencies is to get the current `XContext.current`,
and then ask it for the dependency like below. This works for any type, including
types that don't inherit from `xinject.dependency.Dependency`:

>>> XContext.grab().grab(SomeResourceType).some_value
'hello!'

If you pass a type into `XContext.current`, it will do the above ^ for you:

>>> XContext.current(SomeResourceType).some_value
'hello!'
>>> XContext.current(SomeResourceType).ident
0

As you can see, it still returns the same object [ie: `ident == 0`]

## Activating New Resource

You can easily create a new dependency, configure it however you like and then 'activate' it,
so it's the current version of that dependency. This allows you to 'override' and activate your
own copy of a dependency.

You can do it via one of the below listed methods/examples below.

For these examples, say I have this dependency defined:

>>> from dataclasses import dataclass
>>> from xinject import Dependency
>>>
>>> @dataclass
>>> class MyResource(Dependency):
>>>     some_value = 'default-value'
>>>
>>> assert MyResource.grab().some_value == 'default-value'

- Use desired `xinject.dependency.Dependency` subclass as a method decorator:

        >>> @MyResource(some_value='new-value')
        >>> def my_method():
        >>>     assert MyResource.grab().some_value == 'new-value'

## Activating New Context

When you create a new context, you can activate it to make it the current context in four ways
(listed below).

1. Via the `with` statement.
2. As a method dectorator, ie: `@`.
3. Using `with` or `@` for a `xinject.dependency.Dependency`,
    that will create and activate a new `UContext` with the newley activated dependency in it.
3. When running a unit-test where xinject is installed as a dependency,
    because the `xinject.ptest_plugin.xinject_test_context` fixture is auto-used in this case.
    This fixture creates a new `UContext with a `None` parent;
    that will isolate dependencies between each run of a unit test method.

### Examples

Here are examples of the four ways to create/activate a new context:

>>> with XContext():
...     SomeResourceType.grab().ident
1

This is stack-able as well; as in this can keep track of a stack of contexts, in a
thread-safe way.

When the context manager or decorated method is exited, it will pop-off the context,
and it won't
be the default one anymore. Whatever the default one was before you entered the `with` will
be the default once more.

>>> @XContext():
>>> def a_decorated_method():
...     return SomeResourceType.grab().ident
>>> a_decorated_method()
2
>>> a_decorated_method()
3
>>> SomeResourceType.grab().ident
0

As you can see, after the method exits the old context takes over, and it already had the
older version of the dependency and so returns that one.

By default, a context will create a dependency when it's asked for it, and it does not have it
already. As you saw above, every time a blank Context was created, it also created a new
SomeResourceType when it was asked for it because the new blank `xinject.context.XContext`
did not already have the dependency.


>>> with XContext():
>>>     SomeResourceType.grab().ident
4

There is a pytest plugin with an auto-use fixture that will create brand-new app + thread root
UContext's; so that each unit test function run will start with no dependecies from other tests.

>>> def test_some_text(context):
...    # This is guaranteed to be a newly created `SomeResourceType`.
...    SomeResourceType.grab()



There are ways to share dependency in a parent Context that a new blank context would beable
to use. But that's more advanced usage. The above should be enough to get you started quickly.
See below for more advanced usage patterns.

# Parents

A Context can have a parent (`XContext.parent`) or event a chain of them (`XContext.ctx_chain`).
The parent is figured out dynamically based on the current thread and a special internal `contextvars.ContextVar`.

Because it's the safest thing to do by default for naive dependencies, Context's normally don't
consult parents for basic dependencies, they will just create them if they don't already have them.

You can customize this behavior. There are some default dependency base classes that will implment
a few common patterns for you. You can see how they work to get ideas, and customize the process
for your own dependency when needed. See [Resource Base Classes][dependency-base-classes] below for
more details on how to do that.

You can make an isolated Context by doing:

>>> XContext(parent=None)

When creating a new context. This will tell the context NOT to use a parent. By default, a
Context will use the current Context as the time the Context was created as it's parent.
See `XContext.parent` for more details.

This is also how the Context test fixture works (see `xinject.ptest_plugin.xinject_test_context`).
It creates a new parent-less context and activates it while the fixture is used.

# Resource Base Classes
[dependency-base-classes]: #dependency-base-classes.

### `xinject.dependency.Dependency`

You can implment the singleton-pattern easily by inherting from the
`xinject.dependency.Dependency` class.
This will try it's best to ensure only one dependency is used amoung a chain/tree of parents.
It does this by returning `self` when `xinject.context.XContext` asks it what it wants to do when
a child-context asks for the dependency of a specific type.

Since `xinject.dependency.Dependency` can be shared amoung many diffrent child Context objects,
and makes the same instance always 'look' like it's the current one;
generally only one is every made or used.

However, you can create a new Context, make it current and put a diffrent instance of the
dependency in it to 'override' this behavior.
See [Activating New Resource](#activating-new-dependency) for more details.

#### Example

I create a new class that uses our previous [SomeResourceType][dependencies] but adds in a
`xinject.dependency.Dependency`.

>>> class MySingleton(SomeResourceType, Dependency):
...     pass
>>> MySingleton.grab().ident
5

Now watch as I do this:

>>> with XContext():
...     MySingleton.grab().ident
5

The same dependency is kept when making a child-context. However, if you make a parent-less
context:

>>> with XContext(parent=None):
...     MySingleton.grab().ident
6

The `xinject.dependency.Dependency` will not see pased the parent-less context,
and so won't see the old dependency.
It will create a new one. The `xinject.dependency.Dependency` will still create it in the
furtherest parent it can... which in this case was the `xinject.context.XContext` activated by the
with statement.

"""
import contextvars
import functools
import threading
from weakref import WeakSet
from functools import cached_property
from typing import TypeVar, Type, Dict, List, Optional, Union, Any, Iterable, Set, Self, Iterator

from xsentinels.default import Default, DefaultType
from xsentinels.singleton import Singleton
from xinject.errors import XInjectError
from logging import getLogger
from . import _private

log = getLogger(__name__)

T = TypeVar('T')
C = TypeVar('C')
ResourceTypeVar = TypeVar('ResourceTypeVar')
"""
Some sort of Dependency, I am usually emphasizing with this that you need to pass in the
`Type` or `Class` of the Dependency you want.
"""


# Tell pdoc3 to document the normally private method __call__.
__pdoc__ = {
    "XContext.__call__": True,
    "XContext.__copy__": True,
    "XContext.__deepcopy__": True,
    "XContext.__enter__": True,
    "XContext.__exit__": True,

}


class _TreatAsRootParentType(Singleton):
    """
    Use `TreatAsRootParent`. This class is an implementation detail,
    to ensure that there is ever only one `TreatAsRootParent` value.
    I based this off how None works in Python [ie: a None + NoneType]
    """
    pass


_TreatAsRootParent = _TreatAsRootParentType()
""" Can be used for the parent of a new `XContext`, it will make the context a root-like
    context. What this means is the parent is treated as if you set it to `None` while at the
    same time altering the copying/activating behavior.

    When you make a copy of a root-like `XContext` and activate the copy.
    When this happens the new context will use the currently activated context as it's parent.

    Normally when you pass in `None` as the parent of a new context, ie:

    >>> XContext(parent=None)

    New copies of that context object will have their parent set as None.

    For a root-like context created like this:

    >>> XContext(parent=_TreatAsRootParent)

    When activating this context, it will make a copy and have it's parent set as None.
    But if you then make another copy of this root-like context, the new context will
    have it's parent set to the Default/Current context instead of staying as None.

    The idea here is, if you pass in an explicit None, then we should always use None including
    in copied.  But root-like objects are a bit special, they have no parent because they are
    supposed to be the 'first' one, and we don't necessarily want any copies of this
    root-like context to keep using `None`.
"""


class XContext:
    """
    See [Quick Start](#quick-start) in the `xinject.context` module if your new to the XContext
    class.
    """

    @classmethod
    def grab(cls) -> 'XContext':
        """
        Gets the current `XContext` that should be used by default. It does this by calling
        `XContext.current`.
        """
        ctx = _XContextOrderedStore.current()

        # If there is nothing in the stack, return thread-root.
        if ctx is None:
            return _thread_storage.root_ctx

        if ctx._thread_unique_id != _thread_storage.thread_unique_id:
            return _thread_storage.root_ctx

        return ctx

    @classmethod
    def thread_root(cls) -> Self:
        return _thread_storage.root_ctx

    @classmethod
    def current(cls, for_type: Type[C]) -> C:
        """ Gets the current context that should be used by default, via the Python 3.7 ContextVar
            feature. Please see XContext class doc [just above] for more details on how this works.
        """
        context = cls.grab()

        if for_type is XContext:
            return context

        return context.dependency(for_type=for_type)

    @classmethod
    def _current_without_creating_thread_root(cls):
        return _current_context_contextvar.get()

    @property
    def parent(self) -> Self | None:
        """ Returns the next parent relative to us and the current thead.
            See `XContext.chain` for details on algorithm.
        """
        # Use `chain` to help us find our next parent.
        return next(self.ctx_chain(yield_self=False), None)

    @property
    def name(self) -> str:
        """ Name of context (for debugging purposes only).
            Right now this defaults to a unique number, that gets incremented each time a
            `XContext` is created (in it's init method).

            May allow customization in the future.
        """
        return self._name

    def __init__(
            self, __func=None, *,
            dependencies: Union[Dict[Type, Any], List[Any], Any] = None,
            parent: Union[DefaultType, _TreatAsRootParentType, None] = Default,
            name: str = None,
            _thread_unique_id: int | None = None,
    ):
        """
        You can give an initial list of dependencies
        (if desired, most of the time you just start with a blank context).

        for `parent`, it can be set to `xsentinels.default.Default` (default value); or to `None.

        If you don't pass anything to parent, then the default value of `Default` will cause us
        to look up the current context and use that for the parent automatically when the
        XContext is activated.
        For more information on activating a context see
        [Activating A XContext](#activating-a-context).

        If you pass in None for parent, no parent will be used/consulted. Normally you'll only
        want to do this for a root context. Also, useful for unit testing to isolate testing
        method dependencies from other unit tests. Right now, the unit-test Dependency isolation
        happens automatically via an auto-use fixture
        (`xinject.ptest_plugin.xinject_test_context`).

        A non-activated context will return `xsentinels.default.Default` as it's `XContext.parent`
        if it was created with the default value;
        otherwise we return `None` (if it was created that way).

        Args:
            dependencies (Union[Dict[Type, Any], List[Any], Any]): If you wish to have the
                `XContext` your creating have an initial list of dependencies you can pass them
                in here.

                It can be a single Dependency, or a list of dependencies, or a mapping of
                dependencies.

                Mainly useful for unit-testing, but could be useful elsewhere too.

                They will be added to use via `XContext.add` for you.

                If you use a dict/mapping, we will use the following for `XContext.add`:

                - Dict-key as the `for_type' method parameter.
                - Dict-value as the `Dependency` method parameter.

                This allows you to map some standard Dependency type into a completely different
                type (useful for unit-testing).

                By default, no dependencies are initially added to a new XContext.

            parent (Union[xsentinels.default.Default, _TreatAsRootParent, None]): Unused/Ignored,
                only here for backwards compatibility only.

            name (str): Optional name.
                If left as None, by default, this will simply assign a unique sequential
                number to the name.

                If name is passed in, it will be appended to the unique sequential number.

                When XContext is printed in a string, it will include
                this as it's name to make debugging easier.

        """
        if _thread_unique_id is not None:
            self._thread_unique_id = _thread_unique_id
        else:
            self._thread_unique_id = _thread_storage.thread_unique_id

        self._thread_name = threading.current_thread().name
        self._reset_dependencies()

        if not name:
            name = 'Stack'

        # Unique sequential number.
        self._name = f'{name}[{threading.current_thread().name}]({_ctx_counter.new_value()})'

        # This means we were used directly as a function decorator, ie:
        # >>> @XContext
        # >>> def some_method():
        # ...     pass
        #
        # Store the decorated function for later use
        # (for when decorated method get's called).
        if __func and not callable(__func):
            raise XInjectError(
                "First position argument was NOT a callable function; "
                "The first positional argument `__func` is reserved for a decorated function "
                "when you do use XContext directly as a decorator, "
                "ie: `@XContext` (notice no parens at end)."
            )
        self._func = __func
        if __func:
            # Make our class appear to be '__func', ie: we are wrapping __func
            # due to using XContext like this:
            #
            # >>> @XContext  # <-- notice not parens at end "()"
            # >>> def some_method():
            # ...     pass
            functools.update_wrapper(self, __func)

        # Add any requested initial dependencies.
        if isinstance(dependencies, dict):
            # We have a mapping, use that....
            for for_type, resource in dependencies.items():
                self.add(resource, for_type=for_type)
        elif isinstance(dependencies, list):
            # We have one or more Dependency values, add each one.
            for resource in dependencies:
                self.add(resource)
        elif dependencies is not None:
            # Otherwise, we have a single Dependency value.
            self.add(dependencies)

    # todo: Make it so if there is a parent context, and the current config has no property
    # todo: it can ask the XContext for the parent config to see if it has what is needed.
    def add(
            self, dependency: Any, *, for_type: Type = None
    ) -> "XContext":
        """
        Lets you add a dependency to this context, you can only have one-dependency per-type.

        Returns self so that you can keep calling more methods on it easily.... this allws you
        to also add a dependency and then use it directly as decorator (only works on python 3.9),
        ie:

        >>> # Only works on python 3.9+, it relaxes grammar restrictions
        >>> #    (https://www.python.org/dev/peps/pep-0614/)
        >>>
        >>> @XContext().add(2)
        >>> def some_method()
        ...     print(f"my int dependency: {XContext.dependency(int)}")
        Output: "my int dependency: 2"

        As as side-note, you can easily add resources to a new `xinject.context.XContext` via:

        >>> @XContext(dependencies=[2])
        >>> def some_method()
        ...     print(f"my int dependency: {XContext.dependency(int)}")
        Output: "my int dependency: 2"

        With the `XContext.add` method, you can subsitute dependency for other
        dependency types, ie:

        >>> def some_method()
        ...     context = XContext()
        ...     context.add(3, for_type=str)
        ...     print(f"my str dependency: {XContext.dependency(str)}")
        Output: "my str dependency: 3"

        If you need to override a dependency, you can create a new context and set me as it's
        parent. At that point you can add whatever resources you want before anyone else
        uses the new `xinject.context.XContext`.

        .. warning:: If you attempt to add a second dependency of the same type...
            ...a `xinject.errors.XInjectError` will be
            raised. This is because other objects have already gotten this dependency and are
            relying on it now.  You need to configure any special resources you want to add
            to this context early enough before anything else will need it.

        .. todo:: Consider relaxing this ^ and not producing an error [or at least an option
            to 'replace' an existing dependency in an existing Context. I was cautious on this
            at first because it was the safest thing to do and I could always relax it later
            if I found that desirable. Careful consideration would have to be made.

        Args:
            dependency (Any): Object to add as a dependency, it's type will be mapped to it.

            skip_if_present (bool): If False [default], we raise an exception if dependency
                of that type is already in context/self.

                If True, we don't do anything if dependency of that type is already in
                context/self.

            for_type: You can force a particular mapping by using this option.
                By default, the `for_type` is set to the type of the passed in dependency
                [via `type(dependency)`].

                You can override this behavior by passing a type in the `for_type` param.
                We will then map the dependency for `for_type` to the `dependency` object when
                a dependency is requested for `for_type` in the future. Will still raise the
                error if a dependency for `for_type` already exists in Context.
        Returns:
            Return `self`, so that you can keep calling more methods easily if needed
            (ie: .add(), etc)
        """
        if for_type is None:
            for_type = type(dependency)

        self._dependencies[for_type] = dependency
        if self._sibling:
            self._sibling.add(dependency, for_type=for_type)
        return self

    def dependency(
            self, for_type: Type[ResourceTypeVar], *, create: bool = True
    ) -> ResourceTypeVar:
        """

        ## Summary

        The whole point of the `xinject.context.XContext` is to have a place to get shared
        dependencies. This method is the primary way to get a shared resource from a XContext
        directly.

        Normally, code will use some other convenience methods, as an example:

        Normally a resource will inherit from `xinject.dependency.Dependency` and that
        class provides a class method `xinject.dependency.Dependency.grab` to easily get a
        resource of the inherited type from the current context as a convenience.

        So normally, code would do this to get a Resource:

        >>> class SomeResource(Dependency):
        >>>    pass
        >>> # Normally code would do this to get current Dependency object:
        >>> SomeResource.grab()

        Another convenient way to get the current resource is via the
        `xinject.proxy.CurrentDependencyProxy`. This class lets you create an object
        that always acts like the current/active object for some Resource.
        So you can define it at the top-level of some module, and code can import it
        and use it directly.

        I would start with [Quick Start](#quick-start) if you know nothing of how
        `xinject.context.XContext` works and want to learn more about how it works.

        Most of the time, you interact with Context indrectly via
        `xinject.dependency.Dependency`.  So getting familure with Context is more about
        utilize more advance use-cases. I get into some of these advanced use-cases below.

        ## Advanced Usage for Unit Tests

        You can allocate a new Context to inject or customize dependencies. When the context is
        thrown away or otherwise is not the current context anymore, the idea is whatever
        resource you made temporarily active is forgotten.

        You can inject/replace dependencies as needed for unit-testing purposes as well by simply
        adding the resource to a new/blank `xinject.context.XContext` as a diffrent type,
        see example below.

        In this example, we add a value of int(20) for the `str` resource type.
        I used built-int types to simplify this, but you can image using your own
        custom-resource-class and placing it in the Context for the normal-resource-type
        the normal code asks for.

        >>> XContext().add(20, for_type=str)
        >>> XContext().dependency(str)
        Output: 20

        ## Specific Details

        Given a type of `xinject.dependency.Dependency`, or any other type;
        we will return an instance of it.

        If we currently don't have one, we will create a new one of type passe in and return that.
        We will continue to return the one created in the future for the type passed in.

        You can customize this process a bit by having your custom resource inherit from
        `xinject.dependency.Dependency`.

        Otherwise, no other parameters will be sent to init method.

        If you have an `for_type` class of any sort
        that needs extra parameters, and you want to use it as a Resource, you can create it
        yourself and add it to the Context via `add_resource`.  I would recommend in this case a
        class-method on the `for_type` class that would accept these extra parameters and then
        check the current Context and allocate or return the existing context resource as needed.

        Args:
            for_type (Type[ResourceTypeVar]): The type of resource you need, and instance of
                this type will be returned.

            create (bool): Whether to create resource if needed or not.
                If `True` [default]: creates the resource if it does not exist in self.
                If `False`: only returns an object if we have it already, otherwise None.
        """

        # TODO: Decide if/when to bring back the cached dependencies.
        #   I have thoughts on the cache-key being the StorageObject or some such and then
        #   keeping track of all XContext instances weakly, etc;
        #   but for now to keep things simple and don't do caching.
        #
        # # We next check our cached parent deps...
        # obj = self._cached_parent_dependencies.get(for_type, None)
        # if obj is not None:
        #     return obj

        # We must now query the parent-chain to find the dependency.
        #
        # If we are the root context for the entire app (ie: app-root between all threads)
        # then we check to see if dependency is thread-sharable.
        #
        # If it is then we continue as normal.
        # If NOT, then we always return None.
        #
        # This will indicate to the thread-specific XContext that is calling us to allocate
        # the object in its self.
        #
        # If something else is asking us, we still return None because this Dependency does not
        # belong in us, and so we should not accidentally auto-create it in us.
        # ie: Whoever is calling it should handle the None case.
        #
        # In Reality, the only thing that should be calling the app-root context
        # is a thread-root context.  Thread root-contexts should never return None when asked
        # for a dependency.
        #
        # So, code using a Dependency in general should never have to worry about this None case.

        from xinject.dependency import is_dependency_thread_sharable
        is_thread_sharable = is_dependency_thread_sharable(for_type)

        if self._is_app_root and not is_thread_sharable:
            # We can't allocate a non-thread-sharable dependency in the app-root context,
            # and there are no more parents; so we always return `None` in this case.
            return None

        last_ctx = None
        for ctx in self.ctx_chain(yield_from_other_threads=is_thread_sharable):
            last_ctx = ctx
            obj = ctx._dependencies.get(for_type, None)
            if obj is not None:
                # TODO: I have another TODO in this file about caching these, check that for details.
                # # Store in self (and all other ctx's up to this point) for future reuse?
                # self._cached_parent_dependencies[for_type] = parent_value
                return obj

        # If we can't create the dependency, we simply return `None`; nothing more to do.
        if not create:
            return None

        # We next create dependency if we don't have an existing one.
        # Allocate a blank object if we have no parent-value to use.
        # We add it to the ctx farthest down the stack, so it can be more visible to others
        # (this reduces the number of redundant Dependency instances to the minimum).
        # If `is_thread_sharable` is `False`, the last one is guaranteed to be the thread-root.
        obj = for_type()
        last_ctx._dependencies[for_type] = obj

        # TODO: I have another TODO in this file about caching these, check that for details.
        # # Store in self and all other ctx's on the stack for future reuse?
        # self._cached_parent_dependencies[for_type] = parent_value

        return obj

    def resource_chain(
            self, for_type: Type[ResourceTypeVar], create: bool = False
    ) -> Iterable[ResourceTypeVar]:
        """ This is deprecated, renamed to `XContext.dependency_chain`; use `dependency_chain` instead.
        """
        return self.dependency_chain(for_type=for_type, create=create)

    def dependency_chain(
            self, for_type: Type[ResourceTypeVar], create: bool = False
    ) -> Iterable[ResourceTypeVar]:
        """
        Returns a python generator yielding dependencies in self and in each parent;
        returns them in order.

        This won't create a dependency if none exist unless you pass True into `create`, so it's
        possible for no results to be yielded if it's never been created and `create` == False.

        .. warning:: This is mostly used by `xinject.dependency.Dependency` subclasses
            (internally).

            Not normally used elsewhere. It can help the `xinject.dependency.Dependency`
            subclasses to find their list of parent dependencies to consult for its
            own purposes (ie: to inherit settings/configuration from parent objects).

        Args:
            for_type (Type[ResourceTypeVar]): The dependency type to look for.
            create (bool): If we should create dependency at each context if it does not already
                exist.
        Yields:
            Generator[ResourceTypeVar, None, None]: Resources that were found in the self/parent
                hierarchy.
        """
        objs_already_seen = set()
        from xinject.dependency import is_dependency_thread_sharable
        is_thread_sharable = is_dependency_thread_sharable(for_type)

        for context in self.ctx_chain(yield_from_other_threads=is_thread_sharable):
            obj = context.dependency(for_type=for_type, create=create)
            if not obj:
                continue

            obj_id = id(obj)
            if obj_id in objs_already_seen:
                continue

            objs_already_seen.add(obj_id)
            yield obj

    def __copy__(self):
        """ Makes a shallow copy of self.

            We copy `XContext` implicitly and make that copy the 'active' context when it's made
            current/activated via a:

            - decorator `@`,
            - `with` statement,
            - Activating a `xinject.dependency.Dependency` via `@` or `with`.

            Using one of the above with a XContext also makes it 'active'
            (see XContext.is_active for more internal details, if your interested ).

            When a context is made current, it's sort of used as a 'template'.
            That way it can be used over and over again without accumulating
            resourced between runs. It will be 'fresh' each time with whatever
            you added in the original 'template'.
        """
        return self.copy()

    def __deepcopy__(self, memo):
        """
        For right now, I am disabling making deep-copies of UContext.

        This method currently raises a `NotImplementedError` error.

        Will enable this in a future version of the library.

        Args:
            memo: Memo from `copy.deepcopy`, used to hook up already deep-copied objects
                that have multiple ways/paths to get to in a graph.

        Returns:
            Raises a `NotImplementedError` error.
        """
        raise NotImplementedError(
            "Deepcopy is currently disabled for xinject.context.XContext. "
            "Will enable at some point in the future, disabled for now."
        )

        # # Copy current dependencies from self into new XContext;
        # # This uses `self` as a template for the new XContext.
        # new_resources = {}
        # for k, v in self._dependencies.items():
        #     v = copy(v)
        #     new_resources[k] = v

        # return self.__copy__(deepcopy_resources=True, deepcopy_memo=memo)

    def copy(self, name: str | None = None):
        """ Convenience method to easily shallow-copy a XContext, calls `return copy.copy(self)`.
            Used when you activate a XContext via a decorator or `with` statement.

            When a XContext is activated, it is copied and then the copy is set to active.
        """
        # Blank context with the same parent configuration
        if not name:
            name = "Copy"
        new_context = XContext(name=f"{name}Of<{self._name}>")
        new_context._dependencies = self._dependencies.copy()
        return new_context

    def __enter__(self):
        """
        Used to make a Context usable as a ContextManager via `with` statement.

        Otherwise, will activate self, and return self.
        You MUST ensure that a context that is directly activated and with no
        copy made is not currently active right now.

            We will copy self and then activate the copy, returning the copy as the
            output of the with statement.

            >>> # Some pre-existing XContext object.
            >>> some_context: XContext
            >>>
            >>> # Use it in `with` statement:
            >>> with some_context as copied_and_activated_context:
            ...     assert XContext.grab() is copied_and_activated_context
            ...     assert XContext.grab() is not some_context
        """
        if self.is_active:
            # We are already 'activated', make shallow copy + sibling.
            # This is due to the need to put ourselves into the storage/parent-chain a second time.
            # To accomplish this, we make a copy of ourselves and set the copies sibling to ourselves.
            # WHen a context has a sibling, dependencies added to them is also added to the sibling.
            # This allows the 'appearance' from the users perspective that the context is still the same,
            # even though we are technically using a second context object.
            new_ctx = self.copy(name="Sibling")
            new_ctx._sibling = self
            _XContextOrderedStore.push(new_ctx, self)
            return new_ctx

        _XContextOrderedStore.push(self)
        return self

    def __exit__(self, *args, **kwargs):
        result = _XContextOrderedStore.pop(self)
        if not result:
            log.error(f"A XContext ({self}) was exited, but it was not in stack.")

    def __call__(self, *args, **kwargs):
        """
        This allows us to support using `xinject.context.XContext` as a function decorator in a
        few ways:

        >>> @XContext
        >>> def some_method():
        ...     pass

        OR

        >>> my_context = XContext()
        >>> my_context.add(Dependency())
        >>>
        >>> @my_context
        >>> def some_method():
        ...     pass

        In either case, we will create and activate NEW context each time `some_method` is called.
        It will be thrown away after the method is finished executing.

        This allows you to make whatever changes you wish to the Context while method is
        is running and it will start fresh again next time it runs.

        In the case of a pre-allocated context, such as `my_context` in the above example;
        we will use that as the template/starting-point each time `some_method` is called;

        What this means is that when `some_method` is called, and we create this new
        `xinject.context.XContext` to use.
        The next `xinject.context.XContext` will get the same dependencies that are/were assigned
        to it; whatever it is at the time `some_method` is called.

        This allows for more fine-control of what is in the `template` context, without
        worrying about taking other changes into it that come later.
        """
        _func = self._func

        def wrapper(*args, **kwargs):
            # If we already have `self._func`,
            # it means we were used directly as a function decorator, ie:
            #
            # >>> @XContext
            # >>> def some_method():
            # ...     pass
            #
            # FYI: This will make a shallow copy IF `self` has already activated and then make the
            #      two contexts siblings, when a younger sibling has resources added to it, it
            #      will also add them to the older sibling.
            #      (ie: we are activating same `XContext` object twice).
            #      Example: Could happen if function we are decorating is called recursively.
            with self:
                # Use the out-scope `_func` var; which should have the original/decorated method
                # that is being called.
                return _func(*args, **kwargs)

        if _func:
            # If we have a `self._func`, that means we were used as a decorator without
            # using parens, like so:
            #
            # @XContext
            # def some_method():
            #    pass
            #
            # In this case, we just use the stored method we already have.
            # Currently, the decorated method is being called so we execute the call immediately.
            return wrapper(*args, **kwargs)

        # If we don't already have an assigned self._func;
        # we have this situation:
        #
        # @XContext()
        # def some_func():
        #     pass
        #
        # OR
        #
        # some_context = XContext()
        # @some_context
        # def some_func():
        #     pass
        #
        #
        # In the above cases Python will call us to give us the originally decorated func
        # which in the above cases would be `some_func`.
        #
        # Our objective is to wrap a decorated function; such that when decorated method is called
        # we will activate a new context, keeping whatever objects are in `some_context`.
        # After function is done, we will throwaway the new context because it may have
        # objects while `some_func` was running. We don't want to bring any dependencies
        # created while function was running into future runs of the function.
        # We want to start fresh each time.

        fail_reason = ""
        if len(args) != 1:
            fail_reason = "zero arguments"
        elif not callable(args[0]):
            fail_reason = "one non-callable argument"

        if fail_reason:
            raise XInjectError(
                f"Used directly as decorator `@XContext` (without ending parens) which is"
                f"normally fine. This normally makes "
                f"Python pass decorated function into `__init__` method and I don;t "
                f"one of those. "
                f"In this case Python should call us with exactly one callable argument; "
                f"But instead we got called with {fail_reason}. "
                f"This should not be possible; something very strange is afoot!"
            )

        # Store the function for later use by the wrapper closure method we are returning.
        # This should be the originally decorated method;
        # ie: It should be `some_method` in the below small example:
        #
        # @XContext()
        # def some_method():
        #    pass

        _func = args[0]
        # This makes our `wrapper` method look like `_func` to the outside world.
        functools.update_wrapper(wrapper, _func)
        return wrapper

    def ctx_chain(self, yield_self: bool = True, yield_from_other_threads: bool = True) -> Iterator[Self]:
        """ Returns a generator that will yield self, and then every parent relative to us, along
            with the thread-root and app-root at the appropriate times.

            The goal is to generally return self first, and then the next parent in the stack, etc.;
            but along the way yielding the special thread-root and app-root at the correct points.

            General Algorthm:
            - Always yield self first, unless `include_self` is `False`.

            - If self is not active, we return the top of the stack; unless top of stack is from a different thread,
              we then return thread-root context in that case.

            - Otherwise, we keep returning the next context after us in the stack, until we find context in a different
              thread and current context is in current thread.  In that case, we return thread-root context.

            - If self is a thread-root context, we scan stack and return the next context that is not in our
              current thread; and if not found we return app-root context.

            - Once we get to bottom of stack, we check if bottom-stack context is in our current thread.
              If it is we return thread-root context; otherwise we return app-root context.
            Args:
                yield_self: If `True` (default): Include `self` as the first yielded item.
                    Unless `self` is from a different thread and `yield_from_other_threads` is `False`.

                yield_from_other_threads: If `True` (default): Include XContext's that were created in threads
                    different from the current thread.  This overrides `yield_self` if `self` was created
                    in a different thread.
        """
        thread_unique_id = _thread_storage.thread_unique_id
        thread_root_was_yielded = False
        yielded_self = False
        is_self_thread_root = self._is_thread_root

        if yield_self:
            if self._is_app_root and yield_from_other_threads:
                yield self
                return
            elif self._thread_unique_id == thread_unique_id:
                yielded_self = True
                yield self
            elif yield_from_other_threads:
                yielded_self = True
                yield self

            if yielded_self and is_self_thread_root:
                if not yield_from_other_threads:
                    # If we are the thread-root and we already got yielded, nothing more to do.
                    # The thread-root is always last if `yield_from_other_threads` is `False`.
                    return
                thread_root_was_yielded = True

        if self._is_app_root:
            return

        if not yield_from_other_threads and is_self_thread_root:
            return

        storage = _XContextOrderedStore.storage()

        # If we  are thread-root, we need to find the next parent after the thread-root,
        # and then yield that and everything else, up until the app-root
        if is_self_thread_root:
            if thread_unique_id != self._thread_unique_id:
                log.error(f'Somehow asking for parent of a thread-root ({self}) '
                          f'from a different thread ({threading.current_thread().name}/{thread_unique_id}); '
                          f'skipping self.')

            stack_iter = iter(storage.values_reversed)
            for v in stack_iter:
                if v._thread_unique_id == thread_unique_id:
                    continue

                # Found first ctx in storage stack (ie: reversed values) that is in a different thread:
                if yield_from_other_threads and self is not v:
                    yield v
                break
            else:
                # Everything in storage is in our own thread,
                # that means next one after thread-root is the app-root.
                if yield_from_other_threads and self is not _app_root_context:
                    yield _app_root_context
                return

            # Faster to simply continue the iter and finally yield the app root here, since we know exactly
            # what we need to do and no other logic needs to be checked at this point.
            for v in stack_iter:
                if yield_from_other_threads or v._thread_unique_id == thread_unique_id:
                    if self is not v:
                        yield v

            if yield_from_other_threads and self is not _app_root_context:
                yield _app_root_context
            return

        # We want to use a local-copy of the stack, in case things change in our storage/contextvar while iterating
        # (I don't really expect it to, but you never know).
        stack = storage.values
        start_index = storage.index_for_ctx(self)

        # We are not 'active' in storage, so we check the top of the stack;
        # since the next parent needs to be in stack or thread-root.
        if start_index is None:
            if not stack:
                # If nothing is in stack, yield thread-root and then app-root; we are done.
                yield _thread_storage.root_ctx
                if yield_from_other_threads:
                    yield _app_root_context
                # Finished!
                return

            # If we are not yielding from other threads, always do thread-root last, no mater what.
            # If stack top is not in our thread, we yield the thread-root and then go though the rest of the stack.
            if yield_from_other_threads and stack[-1]._thread_unique_id != thread_unique_id:
                v = _thread_storage.root_ctx
                if self is not v:
                    thread_root_was_yielded = True
                    yield _thread_storage.root_ctx

            # Start next index (ie: index-1) to get the top of the stack.
            start_index = len(stack)
        elif start_index <= 0:
            # We are at bottom of the stack.
            # Return thread-root IF the bottom of the stack is in the same thread as us.
            # (if it's in a different thread, thread-root should have already
            #  been yielded earlier at some point in the past).
            if self._thread_unique_id == thread_unique_id:
                yield _thread_storage.root_ctx

            # #hen app-root; and then we are finished.
            if yield_from_other_threads:
                yield _app_root_context
            # Finished!
            return

        # Otherwise, we get the next parent after us in the stack, and so on and so forth...
        for i in range(start_index - 1, -1, -1):
            ctx = stack[i]

            if ctx._thread_unique_id == thread_unique_id and self is not ctx:
                # Thread is the same as us, so always safe to yield it.
                yield ctx
                continue

            # We are from the same thread as the current thread, but next parent is not and self was created in thread;
            # return thread-root if we `yield_from_other_threads`, otherwise wait until the end.
            # We always yield thread-root last if `yield_from_other_threads` is `False`.
            if yield_from_other_threads and not thread_root_was_yielded and self._thread_unique_id == thread_unique_id:
                v = _thread_storage.root_ctx
                if self is not v:
                    thread_root_was_yielded = True
                    yield _thread_storage.root_ctx

            # Yield current position in stack, then go to next one (via for loop).
            # We already detected if ctx was in our thread or not at top of loop,
            # so only yield this if `yield_from_other_threads` is `True`.
            if yield_from_other_threads and self is not ctx:
                yield ctx

        # If we are not yielding from other threads, the thread-root is always the last one; we skip app-root.
        if not yield_from_other_threads:
            yield _thread_storage.root_ctx
            return

        # Make sure we yield thread-root if it has not already been.
        if not thread_root_was_yielded:
            yield _thread_storage.root_ctx

        # And finally, yield the app-root as the last context.
        if yield_from_other_threads:
            yield _app_root_context

    # todo: rename this to just 'chain' ?? or context_chain? [it includes 'self' is why].
    def parent_chain(self, _include_self=True) -> List["XContext"]:
        """ A list of self + all parents in priority order.

            See `XContext._is_active` internal/private var for a bit more detail on what is
            'active' but suffice to say that active means XContext is currently being used via a
            decorator '@' or via `with` or activating a `xinject.dependency.Dependency` via `@`
            or `with`; has not been exited yet, we are active.

            The chain will start with `self` as the first item, and then proceed with the others
            that are currently active (see `XContext.is_active`).
        """
        return [v for v in self.ctx_chain() if v]

    @property
    def is_active(self) -> bool:
        """ This means at some point in the past we were 'activated' via one of these methods:

            `with` or `@` or activating a `xinject.dependency.Dependency` via `@` or `with`.

            And we are still 'active' (or even the 'XContext.current');

            When we are active we can be consulted generically.
            This means the `self` is part of the parent-chain.
            See `XContext.ctx_chain`.
        """
        if self._is_app_root or self._is_thread_root:
            return True
        return _XContextOrderedStore.storage().contains(self)

    def __repr__(self, include_parent=False):
        types_list = list(self._dependencies.keys())
        if types_list and len(types_list) < 3:
            types_list = [t.__name__ for t in types_list]
            types = ';'.join(types_list)
            types = f'dep_type={types}'
        else:
            types = f'dep_count={len(types_list)}'

        my_str = f"XContext(name='{self.name}', {types}')"
        if not include_parent:
            return my_str

        str_list = [my_str]
        for v in self.ctx_chain(yield_self=False):
            str_list.append(v.__repr__(include_parent=False))
        return f"[{', '.join(str_list)}]"

    def _reset_dependencies(self):
        self._dependencies = {}

    _cached_context_chain = None

    # _cached_parent_dependencies: dict = None

    _dependencies: Dict[Type[Any], Any] = None

    _is_app_root = False
    """ If `True`: Context is the root-context for entire app; and lives outside of
            the `_current_context_contextvar` contextvars, in a special static, module/global.
    """

    _is_thread_root: bool = False
    """ If True, this XContext is the root-context for a thread
        (or if only one thread, the only root context).
        This is mostly here for debugging purposes.
    """

    _sibling: Optional['XContext'] = None
    """
    If a `XContext` is activated a second time (perhaps when a function is called recursively, etc)
    then it makes a shallow copy of self, and sets its self as the the XContext copy's sibling
    by setting this var on the copied XContext.

    If a XContext has a sibling, when a `xinject.dependency.Dependency` is directly added to
    XContext via `XContext.add` it will also add that same dependency to the sibling XContext.

    In this way, when you do something like this:

    >>> @XContext()
    >>> def some_method()
    >>>   XContext.grab().add(SomeDependency())

    The `SomeDependency` instance will be added to all of the functions decorated XContext
    objects like you would expect
    (ie: it's treated as if one instance of XContext was created, even if `some_method` is
         called recursively).

    The shallow-copy must be made if method is called recursively so that the parent-chain
    can be kept track of correctly along with any cached resources from the parent-chain.
    """

    _func = None
    """ Used if XContext is used as a function decorator directly, ie:

        >>> @XContext
        >>> def some_method():
        ...     pass
    """

    _thread_unique_id: int
    """ Thread that we were originally created on.
    """

    _thread_name: str
    """ Name of thread we were orginally created on.
    """


class _XContextOrderedStore:
    _storage: dict[XContext, list[XContext] | None]

    def __init__(self, from_pool: Self | None = None):
        if from_pool is not None:
            self._storage = from_pool._storage.copy()
        else:
            self._storage = {}

    @classmethod
    def storage(cls) -> Self | None:
        value = _current_context_contextvar.get()
        if value is None:
            value = _XContextOrderedStore()
            value.set_as_current_storage()
        return value

    @classmethod
    def current(cls) -> XContext | None:
        return _XContextOrderedStore.storage().last

    @classmethod
    def push(cls, ctx: XContext, from_sibling_ctx: XContext | None = None):
        current = _XContextOrderedStore.storage()
        if ctx in current._storage:
            log.error(f'Somehow ({ctx}) was already in internal storage stack when a request to push it came in, '
                      f'stack ({list(current._storage.keys())})')
            return

        new = current.copy()
        storage = new._storage
        storage[ctx] = None
        if from_sibling_ctx and from_sibling_ctx in storage:
            # Copy-on-write immutable list logic:
            to_siblings = storage[from_sibling_ctx]
            if to_siblings is None:
                to_siblings = []
            else:
                to_siblings = to_siblings.copy()

            to_siblings.append(ctx)
            storage[ctx] = to_siblings

        new.set_as_current_storage()

    @classmethod
    def pop(cls, ctx: XContext) -> XContext | None:
        current = _XContextOrderedStore.storage()
        if ctx not in current._storage:
            log.error(f'Somehow ({ctx}) was not in internal storage stack when a request to pop it came in, '
                      f'stack ({list(current._storage.keys())})')
            return None

        top_ctx = current.last
        new = current.copy()
        storage = new._storage
        siblings = storage[ctx]
        result = None

        if ctx is not top_ctx and siblings:
            siblings_indexes_to_cleanup = []
            index_to_use = len(siblings) - 1
            if siblings[index_to_use] is not top_ctx:
                try:
                    index_to_use = siblings.index(top_ctx)
                except ValueError:
                    for i, v in reversed(list(enumerate(siblings))):
                        if v in storage:
                            index_to_use = i
                            break
                    else:
                        index_to_use = None

            if index_to_use is not None:
                siblings = siblings.copy()
                sibling_to_pop = siblings.pop(index_to_use)
                storage[ctx] = siblings if siblings else None
                storage.pop(sibling_to_pop)
                result = sibling_to_pop

        if result is None:
            result = storage.pop(ctx, Default)
            result = ctx if result is not Default else None

        new.set_as_current_storage()
        return result

    def set_as_current_storage(self):
        _current_context_contextvar.set(self)

    def copy(self) -> Self:
        return _XContextOrderedStore(self)

    @cached_property
    def values(self) -> list[XContext]:
        return list(self._storage.keys())

    @cached_property
    def values_reversed(self) -> list[XContext]:
        return list(reversed(self.values))

    @cached_property
    def stack(self):
        return self.values_reversed

    @cached_property
    def ctx_to_index(self) -> dict[XContext, int]:
        return {v: i for i, v in enumerate(self._storage.keys())}

    @cached_property
    def last(self) -> XContext | None:
        values = self.values
        return values[-1] if values else None

    @cached_property
    def top(self):
        return self.last

    @cached_property
    def first(self) -> XContext | None:
        values = self.values
        return values[0] if values else None

    def contains(self, ctx) -> bool:
        return ctx in self._storage

    def index_for_ctx(self, ctx) -> int | None:
        return self.ctx_to_index.get(ctx, None)

    def __getitem__(self, index) -> XContext:
        return self.values[index]

    def __len__(self) -> int:
        return len(self._storage)

    def __contains__(self, item) -> bool:
        return self.contains(item)


def _setup_blank_app_and_thread_root_contexts_globals(keep_global_context: bool = False):
    """
    Used to create initial global state of app/thread-root contexts containers,
    which keep track of the visible `Contexts` on each thread, and for the app-root `XContext`.

    Is also used by `xinject.pytest_plugin.xinject_test_context` auto-use fixture to blank/clear
    out all root/globally visible contexts by allocating the global-structures again and letting
    the old global structures deallocate.

    This allows for clean slate for each individual unit test run,
    in a way that does not really alter how XContext works.

    It should work exactly the same as the normal, non-uniting app.
    We simply clear and allocate new root/global contexts at the start/end of each
    unit test run via the auto-use fixture.

    Args:
        keep_global_context: If `False` (default): Will clear global context and all the pre-thread/async-io ones.
            If `True`: Still clears the per-thread/async-io dependencies but will keep the global ones intact.
                This is used by the pytest plugin to keep global dependencies but to clear out all the others still
                automatically between unit-tests.
    """
    global _app_root_context
    global _current_context_contextvar

    if not keep_global_context:
        _app_root_context = XContext(parent=_TreatAsRootParent, name='AppRoot')
        _app_root_context._is_app_root = True
    else:
        from xinject.dependency import is_dependency_removed_between_unittests, Dependency
        # Remove any dependencies from/in global context that configure themselves as wanting that.
        for k in list(_app_root_context._dependencies):
            k: Type[Dependency]
            if is_dependency_removed_between_unittests(k):
                _app_root_context._dependencies.pop(k, None)

    # Keeping this private for now, everything outside of this module should use the XContext class
    # as a ContextManager/ContextDecorator to get/set current context.
    #
    # This is used to keep track of the current context when using a XContext as a ContextManager.

    _current_context_contextvar = contextvars.ContextVar(
        'py-xinject-current_context',
        default=None
    )

    with _all_thread_storage_ctxs__lock:
        for ctx in _all_thread_storage_ctxs:
            ctx._reset_dependencies()


class _ThreadStorage(threading.local):
    thread_unique_id: int
    root_ctx: XContext

    def __init__(self, first: bool = False):
        super().__init__()
        thread_unique_id = _thread_counter.new_value()
        self.thread_unique_id = thread_unique_id
        ctx = XContext(name=f'ThreadRoot', _thread_unique_id=thread_unique_id)
        ctx._is_thread_root = True
        self.root_ctx = ctx
        with _all_thread_storage_ctxs__lock:
            _all_thread_storage_ctxs.add(ctx)


_all_thread_storage_ctxs__lock = threading.Lock()
_all_thread_storage_ctxs: WeakSet[XContext] = WeakSet()
_ctx_counter = _private.AtomicCounter()
_thread_counter = _private.AtomicCounter()

# These are globals that should be here at this point:
_app_root_context: XContext
_thread_storage = _ThreadStorage(first=True)
_current_context_contextvar: contextvars.ContextVar[_XContextOrderedStore | None]

# Setup initial global XContext objects/state/containers:
_setup_blank_app_and_thread_root_contexts_globals(False)


def copy_full_stack_state() -> Any:
    return _XContextOrderedStore.storage()


def restore_with_full_stack_state(stack_state: Any):
    stack_state.set_as_current_storage()
