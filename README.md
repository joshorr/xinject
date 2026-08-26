![PythonSupport](https://img.shields.io/static/v1?label=python&message=%203.8|%203.9|%203.10&color=blue?style=flat-square&logo=python)
![PyPI version](https://badge.fury.io/py/xinject.svg?)

- [Introduction](#introduction)
- [Documentation](#documentation)
- [Install](#install)
- [Quick Start](#quick-start)
- [Substituting One Dependency For Another](#substituting-one-dependency-for-another)
- [Licensing](#licensing)

# Introduction

Main focus is an easy way to create lazy universally injectable dependencies;
in less magical way. It also leans more on the side of making it easier to get
the dependency you need anywhere in the codebase.

py-xinject allows you to easily inject lazily created universal dependencies into whatever code that needs them,
in an easy to understand and self-documenting way.

# Documentation

**[📄 Detailed Documentation](https://xyngular.github.io/py-xinject/latest/)** | **[🐍 PyPi](https://pypi.org/project/xinject/)**

# Install

```bash
# via pip
pip install xinject

# via poetry
poetry add xinject
```

# Note On Backward Breaking Changes

Version 1.11.0: By default, all global dependencies are removed between each unit test run.
Previously, we removed everything except global, thread-sharable dependencies.

To revert this behavior for a specific dependency, use `remove_between_unittests=False` in its class argument list.

Decided to not make a major breaking change version, as this can only effect unit testing.
Nothing outside unit testing has a breaking change.

# Quick Start

```python
# This is the "my_resources.py" file/module.

import boto3
from xinject import DependencyPerThread


class S3(DependencyPerThread):
    def __init__(self, **kwargs):
        # Keeping this simple; a more complex version
        # may store the `kwargs` and lazily create the s3 resource
        # only when it's asked for (via a `@property or some such).

        self.resource = boto3.resource('s3', **kwargs)
```

To use this resource in codebase, you can do this:

```python
# This is the "my_functions.py" file/module

from .my_resources import S3

def download_file(file_name, dest_path):
    # Get dependency
    s3_resource = S3.grab().resource
    s3_resource.Bucket('my-bucket').download_file(file_name, dest_path)
```

Inject a different version of the resource:

```python
from .my_resources import S3
from .my_functions import download_file

us_west_s3_resource = S3(region_name='us-west-2')

def get_s3_file_from_us_west(file, dest_path):
    # Can use Dependencies as a context-manager,
    # inject `use_west_s3_resource` inside `with`:
    with us_west_s3_resource:
        download_file(file, dest_path)

# Can also use Dependencies as a function decorator,
# inject `use_west_s3_resource` whenever this method is called.
@us_west_s3_resource
def get_s3_file_from_us_west(file, dest_path):
    download_file(file, dest_path)
```

# Substituting One Dependency For Another

Two class arguments let a `Dependency` subclass stand in for other types, so code can keep asking
for the type it knows about while getting the implementation you actually want.

## `lazily_create_for`

Claims one or more types. When a claimed type is asked for and no instance exists yet, your
subclass is created instead, and that single object is mapped for both types:

```python
from xinject import Dependency

# Defined by a library; app code only ever imports this one.
class BaseConfig(Dependency):
    default_region = 'us-east-1'

# Defined by your app.
class AppConfig(BaseConfig, lazily_create_for=BaseConfig):
    default_region = 'us-west-2'

assert type(BaseConfig.grab()) is AppConfig
assert BaseConfig.grab() is AppConfig.grab()
```

The claimed types don't have to be superclasses; they just have to be types someone asks for.

A few things worth knowing:

- The claim is **global** and registered when your class is defined, ie: when its module is first
  imported. If the claimed type was already lazily created before then, the existing object stays.
  Import the claiming subclass before the type it claims is first used.
- If a second, unrelated class later claims the same type, the later definition wins and a
  `UserWarning` is emitted naming both classes.
- `thread_sharable` is read off the class actually being created, so a `DependencyPerThread`
  subclass is still created per-thread even when the claimed type is thread-sharable.
- It's not inherited; a subclass of `AppConfig` does not claim `BaseConfig`.

## `lazily_create_for_abs`

A bool shorthand: claim every abstract `Dependency` ancestor, so you don't list them by hand.

```python
import abc
from xinject import Dependency

class BaseStore(Dependency, abc.ABC):
    @abc.abstractmethod
    def read(self): ...

class S3Store(BaseStore, lazily_create_for_abs=True):
    def read(self):
        return 'from-s3'

assert type(BaseStore.grab()) is S3Store
```

Without it, `BaseStore.grab()` tries to construct `BaseStore` and dies with
`TypeError: Can't instantiate abstract class`. The point of an abstract Dependency is that code
depends on the base while something else supplies the implementation; this wires that up in one
flag.

An ancestor is only considered if it inherits from `Dependency`. Abstract mixins and plain
`abc.ABC` bases that aren't dependencies are skipped, since nothing would ever ask an `XContext`
for them.

Of those, an ancestor counts as abstract if either:

- It has unimplemented abstract methods, ie: `inspect.isabstract` is `True`.
- It declared its self an ABC (`abc.ABC` in its own bases, or `metaclass=abc.ABCMeta`), even with
  no abstract methods on it. We check what the class its self declared, since `abc.ABCMeta` is
  inherited by every descendant, concrete ones included.

All abstract ancestors are claimed, nearest-first, and merged with anything you list in
`lazily_create_for`. `Dependency` and `DependencyPerThread` are never claimed; neither is abstract.

If the flag is `True` but no abstract ancestor is found, you get a `UserWarning` and nothing is
claimed — that usually means the base stopped being abstract. Two concrete subclasses of the same
abstract base that both set this will collide, later definition winning, with a warning.

## `inject_for`

Maps your dependency for extra types whenever an instance of it lands in a context. Unlike
`lazily_create_for` it does nothing on its own — it only applies to instances that actually get
added, which makes it a good fit for tests and temporary overrides:

```python
from xinject import Dependency

class Auth(Dependency):
    def token(self):
        return real_token()

class FakeAuth(Dependency, inject_for=Auth):
    def token(self):
        return 'fake-token'

def test_something():
    with FakeAuth():
        assert Auth.grab().token() == 'fake-token'

    # Outside the `with`, `Auth` is a plain `Auth` again.
```

This applies however the instance is added: a `with` statement, a function decorator,
`XContext.add`, or the `dependencies` argument of `XContext`. Like `lazily_create_for`,
it's not inherited.

Anything listed in `lazily_create_for` is implicitly added to `inject_for` as well, so an instance
you create and add yourself is found under the claimed types too.

# Licensing

This library is licensed under the MIT-0 License. See the LICENSE file.
