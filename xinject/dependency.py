"""
Easily create singleton-like classes in a sharable/injectable/decoupled way.

Uses `xinject.context.XContext` to find the current dependency for any particular subclass
of Dependency.

You can think of this as making a `Dependency` act like a singleton by default,
as only one instance (at the root-context) would ever 'normally' be created.

It's still possible to get a second instance of the dependency, however:

- If someone created a new dependency themselves manually and adds it to a new Context
    and then activates the context,
    that dependency they created and added themselves could be a second instance.
    (for more details, see [Activating New Dependency](#activating-new-dependency))

    THis is because the Dependency that was manually created was not given an opportunity
    to reuse the parent value.

    However, this is usually desirable as whatever manually created the object probably
    wants to override the dependency with its own configured object.

- If a new `xinject.context.XContext` was created at some point later via `Context(parent=None)`
    and then activated. When a dependency is next asked for, it must create a new one as
    any previous `xinject.context.XContext` would be unreachable until the context was deactivated.
    (for more details, see [Activating New Context](#activating-new-context))


## To Do First

If you have not already, to get a nice high-level overview of library see either:

- project README.md here:
    - https://github.com/xyngular/py-xinject#documentation
- Or go to xinject module documentation at here:
    - [xinject, How To Use](./#how-to-use)

## Dependency Refrence Summary

Allows you to create subclasses that act as sharable dependencies.
Things that should stick around and should be created lazily.

Also allows code to temporarily create, customize and activate a dependency if you don't want
the customization to stick around permanently.
You can do it without your or other code needing to be aware of each other.

This helps promote code decoupling, since it's so easy to make a Resource activate it
as the 'current' version to use.

The only coupling that takes place is to the Resource sub-class it's self.

Each separate piece of code can be completely unaware of each other,
and yet each one can take advantage of the shared dependency.

This means that Resource can also help with simple dependency injection use-case scenarios.

## Dependencies
[dependencies]: #dependencies

### Get Current
There are various ways to get current dependency.
Let's say we have a dependency called `SomeResourceType`:

>>> next_identifier = 0
>>> class SomeResourceType(Dependency):
...     def __init__(self):
...         global next_identifier
...         self.some_value = "hello!"
...         self.ident = next_identifier
...         next_identifier += 1

.. note:: SomeResourceType's `ident` field get's incremented and set on each newly created object.
    So the first SomeResoureType's `ident` will equal `0`,
    the second one created will be `1` and so forth.

If what you want inherits from `Resource`, it has a nice class method that
returns the current dependency.
An easy way to get the current dependency for the type in this case is
to call the class method `Resource.dependency` on its type like so:

>>> SomeResourceType.grab().some_value
'hello!'
>>> SomeResourceType.grab().ident
0

### Activating New Resource

You can easily create a new dependency, configure it however you like and then 'activate' it.
That will make it the current version of that dependency.
This allows you to tempoary 'override' and activate your own custimized version of a dependency.

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


## Active Resource Proxy

You can use `xinject.proxy.CurrentDependencyProxy` to create an object that will act
like the current dependency.
All non-dunder attributes will be grabbed/set on the current object instead of the proxy.

This means you can call all non-special methods and access normal attributes,
as if the object was really the currently active dependency instance.

For more info/details see:

- [Active Resource Proxy - pydoc](./#active-dependency-proxy)
- [Active Resource Proxy - github]
  (https://github.com/xyngular/py-xinject#documentation)


"""
import functools
from typing import TypeVar, Iterable, Type, List, Generic, Callable, Any, Optional, Dict, Set, ClassVar
from copy import copy, deepcopy
from xsentinels import Default
from xinject import XContext, _private
from xinject.errors import XInjectError
import sys

T = TypeVar('T')
R = TypeVar('R')

# Tell pdoc3 to document the normally private method __call__.
__pdoc__ = {
    "Dependency.__call__": True,
    "Dependency.__copy__": True,
    "Dependency.__deepcopy__": True,
    "Dependency.__init_subclass__": True,
}

if sys.version_info >= (3, 11):
    # If we are using Python 3.11, can use this new `Self` type that means current class/subclass
    # that is being used.
    # (it does appear that PyCharm >=2022.3 knows what `Self` is even if you use python < 3.11)
    # This is the only way I know to have a class-property/attribute that type-hints as the
    # subclass.
    from typing import Self
else:
    # This is the best we can do for a `Self` class-property when using python version < 3.11;
    # Newer >=2022.3 will see the above Self typing import and still work even if local project
    # is using an older version of Python!.
    Self = 'Dependency'


def is_dependency_thread_sharable(dependency: 'Dependency') -> bool:
    # noinspection PyProtectedMember
    return dependency._dependency__meta.get('thread_sharable', True)


def attributes_to_skip_while_copying(dependency: 'Dependency') -> Set[str]:
    # noinspection PyProtectedMember
    return dependency._dependency__meta.get('attributes_to_skip_while_copying', set())


class Dependency:
    """
    If you have not already done so, you should also read the xinject project's
    [README.md](https://github.com/xyngular/py-xinject#documentation) for an overview
    of the library before diving into the below text, that's more of like reference material.

    ## Summary

    Allows you to create subclasses that act as sharable dependencies.
    Things that should stick around and should be created lazily.

    Also allows code to temporarily create, customize and activate a dependency if you don't want
    the customization to stick around permanently.
    You can do it without your or other code needing to be aware of each other.

    This helps promote code decoupling, since it's so easy to make a Resource activate it
    as the 'current' version to use.

    The only coupling that takes place is to the Resource sub-class it's self.

    You can also easily have each thread lazily create seperate instance of your Resource,
    by inheriting from `PerThreadResource`.

    Each separate piece of code that uses a particular Resource subclass can be completely
    unaware of each other, and yet each one can take advantage of the shared dependency.

    This means that Resource can help cover dependency-injection use-cases.

    ## Overview

    A `Resource` represents an object in a `xinject.context.XContext`.
    Generally, dependencies that are added/created inside a `XContext` inherit from this abstract
    base `Resource` class, but are not required too. `Resource` just adds some class-level
    conveince methods and configuratino options. Inheriting from Resource also helps
    self-document that it's a Resource.

    See [Resources](#dependencies) at top of this module for a general overview of how dependencies
    and `XContext`'s work. You should also read the xinject project's
    [README.md](https://github.com/xyngular/py-xinject#documentation) for a high-level
    overview.  The text below is more like plain refrence matrial.


    Get the current dependency via `Resource.dependency`, you can call it on sub-class/concreate
    dependency type, like so:

    >>> from xinject import Dependency
    >>> class MyConfig(Dependency):
    ...     some_setting: str = "default-setting-string"
    >>>
    >>> MyConfig.grab().some_setting

    By default, Resource's act like a singletons; in that child contexs will simply get the same
    instance of the dependency that the parent context has.

    If you inherit from this class, when you have `Resource.dependency` called on you,
    we will do our best to ensure that the same object instance is returned every time
    (there are two exceptions, keep reading).

    These dependencies are stored in the current `XContext`'s parent.  What happens is:

    If the current `XContext` and none of their parents have this object and it's asked for
    (like what happens when `Resource.dependency` is called on it),
    it will be created in the deepest/oldest parent XContext.

    This is the first parent `xinject.context.XContext` who's `XContext.parent` is None.
    That way it should be visible to everyone on the current thread since it will normally be
    created in the app-root `xinject.context.XContext`.

    If the Dependency can't be shared between multiple threads, creation would normally happen
    at the thread-root XContext instead of the app-root one.

    If we don't already exist in any parent, then we must be created the first time we are asked
    for. Normally it will simply be a direct call the dependency-type being requested,
    this is the normal way to create objects in python:

    >>> class MyResource(Dependency):
    >>>     pass
    >>>
    >>> MyResource.grab()

    When that last line is executed, and the current or any parent context has a `MyResource`
    dependency; `XContext` will simply create one via calling the dependency type:

    >>> MyResource()

    You can allocate the dependency yourself with custom options and add it to the XContext your
    self.

    Here are the various ways to do that, via:


    - `XContext.add`
        Adds dependency to a specific XContext that already exists
        (or replaces if one has already been directly added in the past to that specific Context).
        When/While XContext is active, these added dependencies will be the `current` ones.

    - Decorator, ie: `@MyResource()`

            >>> from xny_config import Config, config
            >>>
            >>> @DependencySubclass(service="override-service-name")
            >>> def my_method():
            >>>    assert config.service == "override-service-name"

    - via a with statement.

            >>> def my_method():
            >>>    with @DependencySubclass(service="override-service-name")
            >>>         assert config.service == "override-service-name"

    - multiple in single statement by making your own XContext directly:

            >>> def my_method():
            >>>     with @XContext([
            >>>         DependencySubclass(service="override-service-name"),
            >>>         SomeOtherDep(name='new-name')
            >>>     ]):
            >>>         assert config.service == "override-service-name"

    ## Background on Unit Testing

    By default, unit tests always create a new blank `XContext` with `parent=None`.
    THis is done by an autouse fixture (`xinject.pytest_plugin.xinject_test_context`)
    THis forces every unit test run to create new dependencies when they are asked for (lazily).

    This fixture is used automatically for each unit test, it clears the app-root XContext,
    removes all current thread-root XContext's and their children from being `active`.
    just beofre each run of a unit test.

    That way it will recreate any shared dependency each time and a unit test can't leak
    dependencies it added or changed into the next run.

    One example of why this is good is for `moto` when mocking dynamodb in boto3 client.
    Can use dependency to ensure that we get a new dynamodb shared dependency for `boto` each time
    a unit test executes
    (which helps with `moto`, it needs to be active when a dependency is allocated/used).

    This is exactly what we want for each unit test run, to have a blank-slate for all the
    vairous dependencies.

    If a particulre set of unit-tests need to have specific dependcies, you can use fixtures to
    modify/add various dependcies as needed for each indivirual unit-test function run.

    When the application runs for real though, we do generally want to use the dependencies in a
    shared fashion.  So normally we only allocate a new blank-root `@XContext(parent=None)`
    either at the start of a normal application run, or during a unit-test.
    """

    def __init_subclass__(
            cls,
            thread_sharable=Default,
            attributes_to_skip_while_copying: Optional[Iterable[str]] = Default,
            **kwargs
    ):
        """

        Args:
            thread_sharable: If `False`: While a dependency is lazily auto-created, we will
                ensure we do it per-thread, and not make it visible to other threads.
                This is accomplished by only auto-creating the dependency in the thread-root
                `xinject.context.XContext`.

                If `True` (default): Lazily auto-creating the `Dependency` subclass will happen
                in app-root `xinject.context.XContext`, and will therefore be visible and shared
                among all threads.

                If True, we can be put in the app-root context, and can be potentially used in
                multiple threads.  If False, we will only be lazily allocated in the
                pre-thread, thread-root XContext and always be used in a single-thread.

                If another thread needs us and this is False, a new Dependency instance will be
                lazily created for that thread.

                ## Details on Mechanism

                It accomplishes this by the lazy-creation mechanism.
                When something asks for a Dependency that does not currently exist,
                the parent-XContext is asked for the dependency, and then the parent's parent
                will be asked and so on.

                Eventually the app-root context will be asked for the Dependency.

                If the app-root already has the Dependency, it will return it.

                When app-root does not have the dependency, it potentially needs to lazily create
                the dependency depending on if Dependency is thread-safe.

                So at this point, if you call `is_dependency_thread_sharable` on type/cls,
                and if returned value is:

                - `False`: The app-root context will return `None` instead of lazily creating the
                    Dependency. It's expected a thread-root XContext is the thing that asked the
                    app-root context and the thread-root context when getting back a None should
                    just go and lazily create it.
                    This results in a new Dependency being lazily allocated for each thread that
                    needs it.
                - `True`: If it does not have one it will lazily create a new Dependency store it
                    in self and return it. Other thread-roots that ask for this Dependency in the
                    future will get the one from the app-root, and therefore the Dependency will
                    be shared between threads and needs to be thread-safe.

                Each context then stores this value in its self as it goes up the chain.
                Finally, the code that originally asked for the Dependency will have it returned
                to it, and they can then use it.

                We store it in each XContext that Dependency passes though so in the future it can
                just directly answer the question and return the Dependency quickly.

            attributes_to_skip_while_copying: If subclass sets this to a list/set of attribute
                names, we will skip copying them for you
                (via `Dependency.__copy__` and `Dependency.__deepcopy__`).

                See `Dependency.__copy__` for details.

                We ourselves need to skip copying a specific internal property,
                and there are other dependencies that need to do the same thing.

                This is an easy way to accomplish that goal.

                As a side note, we will always skip copying `_context_manager_stack` in addition to
                what's set on `Dependency.__init_subclass__` attributes_to_skip_while_copying
                class argument.

                This can be dynamic if needed, by default it's consulted on the object each time
                it's copied.

                To see where it's used, look at:
                - `Dependency.__copy__`
                - `Dependency.__deepcopy__`
            **kwargs:

        Returns:

        """
        super().__init_subclass__(**kwargs)
        parent_meta_dict = cls._dependency__meta

        if parent_meta_dict is None:
            meta_dict = {'attributes_to_skip_while_copying': set()}
        else:
            meta_dict = deepcopy(parent_meta_dict)

        cls._dependency__meta = meta_dict

        if thread_sharable is not Default:
            meta_dict['thread_sharable'] = thread_sharable

        if attributes_to_skip_while_copying is not Default:
            attr_set: set = meta_dict['attributes_to_skip_while_copying']
            attr_set.update(attributes_to_skip_while_copying)

    _dependency__meta = None

    obj: ClassVar[Self]
    """
    class property/attribute that will return the current dependency for the subclass
    it's asked on by calling `Dependency.grab`, passing no extra arguments and returning the
    result.

    >>> class MyDependency(Dependency):
    >>>     my_attribute: str = "default-value"
    >>>
    >>> # `.obj` calls `.grab()` and returns it's result, so they are equivalent;
    >>> # but type-hinting for `.obj` will only work property on the newest IDE's
    >>> # (it's a new feature in Python 3.11):
    >>>
    >>> assert MyDependency.obj.my_attribute == "default-value"
    >>> assert MyDependency.grab().my_attribute == "default-value"

    Background Details (only if interested in implementation details):

    This is implemented via a `setattr` later on in the module that sets a
    `_private.classproperty.classproperty` on it. This is a private class and should not be
    used outside. I use a `setattr` to try and hide from IDE that a classproperty is being used,
    which can add confusing details to the resulting type-hint the IDE comes up with for `.obj`.

    This way, we hide that detail and the type-hint is cleaner, while at the same time not having
    to implement a `__getattribute__` (which would slow down attribute access to the class).
    """

    @classmethod
    def grab(cls: Type[T]) -> T:
        """
        Gets a potentially shared dependency from the current `udpend.context.XContext`.

        Dependency subclass may add override to have additional args/kwargs when overriding this
        method if needed [rare] to customize things or return alternate dependency based on
        some passed-in value(s).

        (example: like passing in a hash-key of some sort).

        As an alterative to overriding `grab` with addtional arguments,
        you could use a type of Manager for this sort of thing, example:

        >>> class SomeDependencyManager(Dependency):
        ...     def get_resource_via(self, some_key_or_value: str) -> SomeResourceType:
        ...         # Lookup and return some sort of related dependency.
        ...         pass
        >>> SomeResourceManager.obj.get_resource_via("some-key-or-value")
        """
        return XContext.grab().dependency(for_type=cls)

    @classmethod
    def proxy(cls: Type[R], ) -> R:
        """
        Returns a proxy-object, that when and attribute is asked for, it will
        proxy it to the current object of `cls`.

        ie: the equivalent of this code will run:
        >>> # `requested_attribute` is the original attribute being requested
        >>> # on returned proxy object.
        >>> return getattr(cls.grab(), requested_attribute)
        """
        from .proxy import CurrentDependencyProxy
        return CurrentDependencyProxy.wrap(cls)

    @classmethod
    def proxy_attribute(cls, attribute_name: str) -> Any:
        """
        Returns a proxy-object, that when and attribute is asked for, it will
        proxy it to the current attribute value on the current object of `cls`.

        ie: the equivalent of this code will run:
        >>> # `requested_attribute` is the original attribute being requested
        >>> # on returned proxy object.
        >>> return getattr(getattr(cls.grab(), attribute_name), requested_attribute)
        """
        from .proxy import CurrentDependencyProxy
        return CurrentDependencyProxy(
            dependency_type=cls,
            grabber=lambda x: getattr(x, attribute_name),
            repr_info=f'attr:{attribute_name}'
        )

    def __copy__(self):
        """
        Basic shallow copy protection
        (I am wondering if I should just remove this default copy code).

        `Dependency` overrides the default copy operation to shallow copy everything,
        except it will make a shallow copy for any normal dict/list types.
        (so old a new dependencies don't share the same list/dict instance).

        It will also look skip copying any attributes that are named in the
        `attributes_to_skip_while_copying` class parameter (if anything),
        if a super-class of the `Dependency` has specified any `attributes_to_skip_while_copying`
        subclasses will inherit any items in that parents list of attributes to skip while copying.

        If you want different behavior, then override `Dependency.__copy__`.

        A dependency could also use `deepcopy` instead when making a copy, if desirable.

        Copying a dependency may be useful if you want to activate a new dependency but have its
        configuration similar to a current dependency (with some tweaks/modifications).
        """
        clone = type(self)()
        dict_copy = self.__dict__.copy()

        # Pop out of the dict-copy any attributes we should skip.
        attrs_to_skip = attributes_to_skip_while_copying(self) or []
        for attr_to_skip in ['_context_manager_stack', *attrs_to_skip]:
            dict_copy.pop(attr_to_skip, None)

        for k, v in dict_copy.items():
            if isinstance(v, (list, dict)):
                dict_copy[k] = copy(v)
        clone.__dict__.update(dict_copy)
        return clone

    def __deepcopy__(self, memo=None):
        # Collect a list of things to skip....
        # We always need to have `_context_manager_stack`, subclasses can set
        # `attributes_to_skip_while_copying` if they have additional ones they want to skip.
        skip_attributes = {
            x for x in ['_context_manager_stack', *(attributes_to_skip_while_copying(self) or [])]
        }

        # If we get called without a memo, allocate a blank dict.
        if memo is None:
            memo = {}

        # Check to see if we are already in the memo, if we are then use that instead of
        # making a copy of self again.
        already_copied = memo.get(id(self))
        if already_copied:
            return already_copied

        # Make new object, put it in memo so if we encounter `self` in the future we will reuse it.
        copy = type(self)()
        memo[id(self)] = copy

        # Deepcopy everything except the ones user wants to ignore.
        for k, v in self.__dict__.items():
            try:
                if k in skip_attributes:
                    continue
                copy.__dict__[k] = deepcopy(v, memo)
            except TypeError:
                continue  # Ignore type errors

        return copy

    _context_manager_stack: List[XContext] = None
    """ Keeps track of context's we created when self (ie: `Dependency`) is used in a `with`
        statement.  This MUST be reset when doing a copy of the dependency.
    """

    def __enter__(self: R) -> R:
        if self._context_manager_stack is None:
            self._context_manager_stack = []

        # We make a new XContext object, and delegate context-management duties to it.
        context = XContext(dependencies=self)
        self._context_manager_stack.append(context)
        context.__enter__()
        return self

    def __exit__(self, *args, **kwargs):
        stack = self._context_manager_stack
        if not stack:
            raise XInjectError(
                f"While using ({self}) as a context manager via a `with` statement,"
                f"somehow we did not have an internal context from the initial entering "
                f"(see `xinject.dependency.Dependency.__enter__`). "
                f"Indicates a very strange bug."
            )

        context = stack.pop()
        context.__exit__(*args, **kwargs)

    def __call__(self, func):
        """
        This makes Resource subclasses have an ability to be used as function decorators
        by default unless this method is overriden to provide some other funcionality.

        If subclasses do need to override this, I would recemend checking the first positional
        argument for a callable (and no other arguments are passed in) to maintain their ability
        to be function decorators.
        Something like this:

        >>> class MyResource(Dependency):
        ...     some_param = None
        ...     def __init__(self, some_param = None):
        ...         self.some_param = some_param
        ...
        ...     def __call__(self, *args, **kwargs):
        ...         if len(args) == 1 and not kwargs and callable(args[0]):
        ...             return super().__call__(args[0])

        This method will check for a callable being passed in as first argument.
        I will raise an error with a descriptive error message if we don't get a callable.

        We should get a callable if Resource subclass is used like in the example below.
        (Config being a dependency subclass).

        In this example, a new Config dependency is being created and we tell it to only use
        the `EnvironmentalProvider` and we use it as a function decorator.
        This means while the `some_method` function is executing,
        that Config object is made the current one.

        `some_method` and any other method called from within `some_method` will
        only be using the `EnvironmentalProvider` for looking up configuration by default.

        >>> my_resource = MyResource.proxy()
        >>> assert my_resource.some_param is None
        >>>
        >>> @MyResource(some_param="alternate-value")
        >>> def some_method():
        ...     # Only searches: overrides, environ-vars, defaults
        ...     assert my_resource.some_param == 'alternate-value'

        Args:
            func (Callable): decorated function passed in via python decorator syntax.

                >>> @MyResource()
                >>> def some_method():
                ...     pass

        Returns: We execute decorated method and return whatever it returns.
        """
        if not callable(func):
            raise XInjectError(
                f"Attempt to calling a Dependency of type ({self}) as a callable function. "
                f"By default (unless dependency subclass does/says otherwise) you need to use "
                f"it as a decorator when calling it. "
                f"When using a Dependency subclass as a decorator, Python will call the "
                f"Dependency and pass in a callable function. The dependency will then make self "
                f"the current dependency via `with self` and call the passed in function inside "
                f"that with statement, returning the result of calling the passed in function."
            )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper


# Keeps type-hinting in pycharm (and hopefully other IDE's) cleaner.
# This is just an implementation detail, IDE should be using the explicit type-hints on class
# to know what type the `obj` property/attribute will be.
#
# Details: We set a classproperty on `obj` that simply calls the `grab()` method on the
#   Dependency subclass the user is asking for `obj` on and returns the result.
setattr(Dependency, 'obj', _private.classproperty(fget=lambda cls: cls.grab()))


class DependencyPerThread(Dependency, thread_sharable=False):
    """
    Same as `Dependency`, except we set the `thread_sharable` flag to False (via class argument),
    this means when an instance of us is created by the system lazily,
    it will not be shared between threads.

    Basically, when some other thread asks for this dependency,
    the system will lazily create another one just for that thread to use.
    This happens when a particular thread asks for the dependency for the first time.

    When the same thread asks for the dependency a second time, it will not create a new one but
    return the dependency instance that was originally created just for that thread.

    ## Details

    Normally, when a new `Dependency` subclass needs to be created on-demand for the first time
    the new Dependency will be placed in the app's root `xinject.context.XContext`,
    which each thread's root-context has set as its parent.
    This makes the object available to be seen/used by other threads.

    When a dependency makes a subclass from `DependencyPerThread` or otherwise set's
    the `Dependency.__init_subclass__`'s `thread_sharable` to `False` via the Dependency
    class arguments (so that `is_dependency_thread_sharable` will return `False` when its passed
    the new Dependency subclass/type).
    When a thread asks for that dependency for first time it will be lazily created like expected,
    but the resulting object is placed in the root-context instead (and NOT the app-root-context).

    That way, only the specific thread the Dependency was lazily created on will see the object;
    no other thread will.

    Therefore, when other threads also ask for the dependency, they will each create their own
    the first time they ask for it, and place it in their thread-root
    `xinject.context.XContext`.
    """
    pass
