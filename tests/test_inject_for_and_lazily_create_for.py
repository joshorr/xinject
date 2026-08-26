import abc
import inspect
import threading

import pytest

from xinject import Dependency, DependencyPerThread, XContext
from xinject.dependency import (
    inject_for_types,
    lazily_create_for_types,
    lazily_create_type_for,
)
from xinject.errors import XInjectError


class LazyBase(Dependency):
    pass


class LazyImpl(LazyBase, lazily_create_for=LazyBase):
    pass


class InjectBase(Dependency):
    pass


class InjectImpl(Dependency, inject_for=InjectBase):
    pass


def test_lazily_create_for_creates_claiming_subclass():
    obj = LazyBase.grab()
    assert type(obj) is LazyImpl


def test_lazily_create_for_maps_one_object_for_both_types():
    obj = LazyBase.grab()
    assert LazyImpl.grab() is obj
    assert XContext.grab().dependency(LazyBase) is obj
    assert XContext.grab().dependency(LazyImpl) is obj


def test_lazily_create_for_from_either_direction_is_same_object():
    # Ask for the claiming subclass first this time; the claimed type must reuse it.
    obj = LazyImpl.grab()
    assert LazyBase.grab() is obj


def test_lazily_create_for_registry_lookup():
    assert lazily_create_type_for(LazyBase) is LazyImpl
    assert lazily_create_type_for(LazyImpl) is None
    assert lazily_create_for_types(LazyImpl) == (LazyBase,)

    # A claimed type is implicitly injected-for as well.
    assert inject_for_types(LazyImpl) == (LazyBase,)


def test_manually_added_claiming_dependency_is_used_for_claimed_type():
    manual = LazyImpl()
    with manual:
        assert LazyBase.grab() is manual
        assert LazyImpl.grab() is manual

    # Outside the `with`, we fall back to lazily creating a different one.
    assert LazyBase.grab() is not manual


def test_inject_for_only_applies_to_instances_in_a_context():
    fake = InjectImpl()
    with fake:
        assert InjectBase.grab() is fake
        assert InjectImpl.grab() is fake

    # `inject_for` does nothing on its own; nothing claimed `InjectBase` for lazy-creation.
    assert type(InjectBase.grab()) is InjectBase


def test_inject_for_applies_on_lazy_creation_too():
    obj = InjectImpl.grab()
    assert InjectBase.grab() is obj


def test_inject_for_applies_via_context_add_and_dependencies_arg():
    fake = InjectImpl()

    ctx = XContext()
    ctx.add(fake)
    assert ctx.dependency(InjectBase, create=False) is fake

    ctx = XContext(dependencies=[fake])
    assert ctx.dependency(InjectBase, create=False) is fake


def test_inject_for_applies_even_when_for_type_is_explicit():
    fake = InjectImpl()
    ctx = XContext()
    ctx.add(fake, for_type=str)

    assert ctx.dependency(str, create=False) is fake
    assert ctx.dependency(InjectBase, create=False) is fake


def test_decorator_activation_injects_for_claimed_types():
    fake = InjectImpl()

    @fake
    def some_method():
        return InjectBase.grab()

    assert some_method() is fake


def test_accepts_a_list_of_types():
    class TargetOne(Dependency):
        pass

    class TargetTwo(Dependency):
        pass

    class MultiInject(Dependency, inject_for=[TargetOne, TargetTwo]):
        pass

    assert inject_for_types(MultiInject) == (TargetOne, TargetTwo)

    obj = MultiInject()
    with obj:
        assert TargetOne.grab() is obj
        assert TargetTwo.grab() is obj


def test_claimed_types_merge_into_inject_for_without_duplicates():
    class TargetOne(Dependency):
        pass

    class TargetTwo(Dependency):
        pass

    class Both(Dependency, inject_for=TargetOne, lazily_create_for=[TargetOne, TargetTwo]):
        pass

    # `TargetOne` is named twice, it should only show up once and keep `inject_for`'s ordering.
    assert inject_for_types(Both) == (TargetOne, TargetTwo)
    assert lazily_create_for_types(Both) == (TargetOne, TargetTwo)


def test_neither_option_is_inherited():
    class Target(Dependency):
        pass

    class Claimer(Dependency, inject_for=Target, lazily_create_for=Target):
        pass

    class Child(Claimer):
        pass

    assert inject_for_types(Child) == ()
    assert lazily_create_for_types(Child) == ()
    assert lazily_create_type_for(Target) is Claimer

    # Child still inherits the normal meta options.
    class PerThreadClaimer(DependencyPerThread, inject_for=Target):
        pass

    class PerThreadChild(PerThreadClaimer):
        pass

    from xinject.dependency import is_dependency_thread_sharable
    assert is_dependency_thread_sharable(PerThreadChild) is False
    assert inject_for_types(PerThreadChild) == ()


def test_later_claim_wins_and_warns():
    class Target(Dependency):
        pass

    class First(Dependency, lazily_create_for=Target):
        pass

    assert lazily_create_type_for(Target) is First

    with pytest.warns(UserWarning, match='taking over'):
        class Second(Dependency, lazily_create_for=Target):
            pass

    assert lazily_create_type_for(Target) is Second
    assert type(Target.grab()) is Second


def test_re_declaring_same_claim_on_same_class_does_not_warn():
    class Target(Dependency):
        pass

    class Only(Dependency, lazily_create_for=Target):
        pass

    # Subclassing does not re-register, so no warning even though the parent holds the claim.
    class Child(Only):
        pass

    assert lazily_create_type_for(Target) is Only


def test_non_type_value_raises():
    with pytest.raises(XInjectError, match='not a class'):
        class BadInject(Dependency, inject_for='some-string'):
            pass

    with pytest.raises(XInjectError, match='not a class'):
        class BadLazy(Dependency, lazily_create_for=[object, 3]):
            pass


def test_listing_self_raises():
    class Target(Dependency):
        pass

    # A class can't name its self in its own class-arguments (the name doesn't exist yet), so this
    # guard is only reachable through the normalizer; check it there.
    from xinject.dependency import _dependency_types_from
    with pytest.raises(XInjectError, match='lists itself'):
        _dependency_types_from(Target, cls=Target, param_name='inject_for')


def test_lazily_create_for_uses_creating_class_thread_sharability():
    class SharableTarget(Dependency):
        pass

    class PerThreadImpl(DependencyPerThread, lazily_create_for=SharableTarget):
        pass

    main_obj = SharableTarget.grab()
    assert type(main_obj) is PerThreadImpl

    other = {}

    def in_thread():
        other['obj'] = SharableTarget.grab()

    thread = threading.Thread(target=in_thread)
    thread.start()
    thread.join()

    # `SharableTarget` is thread-sharable, but the class we actually create is not,
    # so each thread must get its own.
    assert type(other['obj']) is PerThreadImpl
    assert other['obj'] is not main_obj


def test_unclaimed_dependency_behaves_as_before():
    class Plain(Dependency):
        pass

    obj = Plain.grab()
    assert type(obj) is Plain
    assert Plain.grab() is obj
    assert inject_for_types(Plain) == ()
    assert lazily_create_for_types(Plain) == ()


class AbstractStore(Dependency, abc.ABC):
    @abc.abstractmethod
    def read(self):
        ...


class S3Store(AbstractStore, lazily_create_for_abstract_parents=True):
    def read(self):
        return 'from-s3'


def test_abstract_parent_is_claimed():
    assert lazily_create_for_types(S3Store) == (AbstractStore,)
    assert lazily_create_type_for(AbstractStore) is S3Store

    obj = AbstractStore.grab()
    assert type(obj) is S3Store
    assert obj.read() == 'from-s3'
    assert S3Store.grab() is obj


def test_abstract_parent_claim_also_injects_for():
    assert inject_for_types(S3Store) == (AbstractStore,)

    manual = S3Store()
    with manual:
        assert AbstractStore.grab() is manual


def test_all_abstract_ancestors_claimed_nearest_first():
    class Root(Dependency, abc.ABC):
        @abc.abstractmethod
        def a(self):
            ...

    class Middle(Root):
        # Still abstract, `a` is not implemented yet.
        @abc.abstractmethod
        def b(self):
            ...

    class Concrete(Middle, lazily_create_for_abstract_parents=True):
        def a(self):
            return 'a'

        def b(self):
            return 'b'

    assert lazily_create_for_types(Concrete) == (Middle, Root)
    assert type(Root.grab()) is Concrete
    assert Root.grab() is Middle.grab()


def test_abc_base_with_no_abstract_methods_is_claimed():
    class Marker(Dependency, abc.ABC):
        pass

    # `inspect.isabstract` is False here, it's caught by the self-declared-ABC check.
    assert inspect.isabstract(Marker) is False

    class Impl(Marker, lazily_create_for_abstract_parents=True):
        pass

    assert lazily_create_for_types(Impl) == (Marker,)
    assert type(Marker.grab()) is Impl


def test_metaclass_abcmeta_base_is_claimed():
    class ViaMetaclass(Dependency, metaclass=abc.ABCMeta):
        pass

    class Impl(ViaMetaclass, lazily_create_for_abstract_parents=True):
        pass

    assert lazily_create_for_types(Impl) == (ViaMetaclass,)


def test_concrete_ancestors_are_not_claimed():
    class AbstractBase(Dependency, abc.ABC):
        @abc.abstractmethod
        def go(self):
            ...

    class ConcreteMiddle(AbstractBase):
        def go(self):
            return 'middle'

    class Leaf(ConcreteMiddle, lazily_create_for_abstract_parents=True):
        def go(self):
            return 'leaf'

    # `ConcreteMiddle` inherits ABCMeta but implements everything, so it is not claimed.
    assert lazily_create_for_types(Leaf) == (AbstractBase,)
    assert type(ConcreteMiddle.grab()) is ConcreteMiddle


def test_dependency_base_classes_are_never_claimed():
    class AbstractPerThread(DependencyPerThread, abc.ABC):
        @abc.abstractmethod
        def go(self):
            ...

    class Impl(AbstractPerThread, lazily_create_for_abstract_parents=True):
        def go(self):
            return 'go'

    assert lazily_create_for_types(Impl) == (AbstractPerThread,)
    assert Dependency not in lazily_create_for_types(Impl)
    assert DependencyPerThread not in lazily_create_for_types(Impl)


def test_warns_when_no_abstract_parents_found():
    class PlainBase(Dependency):
        pass

    with pytest.warns(UserWarning, match='none of its parents are abstract'):
        class Impl(PlainBase, lazily_create_for_abstract_parents=True):
            pass

    assert lazily_create_for_types(Impl) == ()
    assert inject_for_types(Impl) == ()
    # Warned, but carried on; `PlainBase` is unclaimed and lazily creates its self.
    assert type(PlainBase.grab()) is PlainBase


def test_false_and_unset_claim_nothing():
    class AbstractBase(Dependency, abc.ABC):
        @abc.abstractmethod
        def go(self):
            ...

    class ExplicitFalse(AbstractBase, lazily_create_for_abstract_parents=False):
        def go(self):
            return 'x'

    class Unset(AbstractBase):
        def go(self):
            return 'y'

    assert lazily_create_for_types(ExplicitFalse) == ()
    assert lazily_create_for_types(Unset) == ()
    assert lazily_create_type_for(AbstractBase) is None


def test_merges_with_explicit_lazily_create_for():
    class AbstractBase(Dependency, abc.ABC):
        @abc.abstractmethod
        def go(self):
            ...

    class SideTarget(Dependency):
        pass

    class Impl(
        AbstractBase,
        lazily_create_for=SideTarget,
        lazily_create_for_abstract_parents=True,
    ):
        def go(self):
            return 'go'

    assert lazily_create_for_types(Impl) == (SideTarget, AbstractBase)
    assert inject_for_types(Impl) == (SideTarget, AbstractBase)
    assert type(SideTarget.grab()) is Impl
    assert SideTarget.grab() is AbstractBase.grab()


def test_flag_is_not_inherited():
    class AbstractBase(Dependency, abc.ABC):
        @abc.abstractmethod
        def go(self):
            ...

    class Impl(AbstractBase, lazily_create_for_abstract_parents=True):
        def go(self):
            return 'go'

    # `Child` does not re-run the claim, so no collision warning and `Impl` keeps it.
    class Child(Impl):
        pass

    assert lazily_create_for_types(Child) == ()
    assert lazily_create_type_for(AbstractBase) is Impl


def test_two_implementations_collide_with_warning():
    class AbstractBase(Dependency, abc.ABC):
        @abc.abstractmethod
        def go(self):
            ...

    class FirstImpl(AbstractBase, lazily_create_for_abstract_parents=True):
        def go(self):
            return 'first'

    with pytest.warns(UserWarning, match='taking over'):
        class SecondImpl(AbstractBase, lazily_create_for_abstract_parents=True):
            def go(self):
                return 'second'

    assert type(AbstractBase.grab()) is SecondImpl


def test_abstract_parents_that_are_not_dependencies_are_skipped():
    class ReadableMixin(abc.ABC):
        @abc.abstractmethod
        def read(self):
            ...

    class MarkerMixin(abc.ABC):
        pass

    class BaseStore(Dependency, abc.ABC):
        @abc.abstractmethod
        def size(self):
            ...

    class Impl(
        BaseStore, ReadableMixin, MarkerMixin, lazily_create_for_abstract_parents=True
    ):
        def read(self):
            return 'r'

        def size(self):
            return 1

    # All three mixins are abstract and in the MRO, but only the `Dependency` one is claimed.
    assert ReadableMixin in Impl.__mro__
    assert MarkerMixin in Impl.__mro__
    assert abc.ABC in Impl.__mro__
    assert lazily_create_for_types(Impl) == (BaseStore,)
    assert inject_for_types(Impl) == (BaseStore,)


def test_warns_when_only_abstract_parents_are_non_dependencies():
    class LonelyMixin(abc.ABC):
        @abc.abstractmethod
        def go(self):
            ...

    class PlainBase(Dependency):
        pass

    # `LonelyMixin` is abstract but isn't a Dependency, so there is nothing to claim.
    with pytest.warns(UserWarning, match='none of its parents are abstract'):
        class Impl(PlainBase, LonelyMixin, lazily_create_for_abstract_parents=True):
            def go(self):
                return 'go'

    assert lazily_create_for_types(Impl) == ()
