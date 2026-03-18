from xinject import XContext, Dependency
import dataclasses
import pytest
from copy import deepcopy, copy
from xinject.errors import XInjectError


@XContext
def test_decorator_on_direct_context_class(xinject_test_context):
    """ Test using XContext class directly as a decorator (not a XContext instance). """
    # This should be the XContext that was created via `@XContext`.
    assert XContext.grab() is not xinject_test_context

    # Since the `@XContext` would have been created AFTER the standard unit-test `context`
    # fixture, the parent of my `@XContext` would be the standard unit-test context fixture.
    assert XContext.grab().parent is xinject_test_context


@dataclasses.dataclass
class SomeDependency(Dependency):
    my_name: str = 'hello!'


module_level_context = XContext.grab()


def test_ensure_pytest_plugin_context_autouse_fixture_working():
    # Ensure by default every unit test that has xinject as a dependency will use
    # the context auto-use fixture; which makes a blank root-like context.
    assert XContext.grab() is not module_level_context

    # Ensure we have no items in the XContext, that it is indeed blank.
    assert len(XContext.grab()._dependencies) == 0


# noinspection PyTypeChecker
# NOTE: This is not how you would normally do this, normally you would do:
#       >>> @SomeDependency(my_name='first-name')
#       Doing it this way to test out giving initial dependencies to a new XContext directly
#       instead of indirectly.
@XContext(dependencies=[SomeDependency(my_name='first-name')])
def test_decorator_on_context_object():
    first_resource = SomeDependency.grab()
    assert first_resource.my_name == 'first-name'
    decorated_context = XContext.grab()

    new_resource = SomeDependency(my_name='new-name')
    with XContext(dependencies=[new_resource]) as with_context:
        assert with_context is not decorated_context, "Should be new context"
        # I created new XContext and manually added new instance of SomeDependency;
        # check to see if it's the current dependency and looks intact.
        inside_resource = SomeDependency.grab()
        assert inside_resource is not first_resource
        assert inside_resource is new_resource
        assert inside_resource.my_name == 'new-name'
        assert first_resource.my_name == 'first-name'

    with XContext():
        assert with_context is not decorated_context, "Should be new context"
        # Check to see if when adding new XContext, we still get the same SomeDependency
        # instance, and that they still look intact with the correct values.
        assert SomeDependency.grab() is first_resource
        assert first_resource.my_name == 'first-name'
        assert new_resource.my_name == 'new-name'


def test_context_and_with():
    root_context = XContext.grab()

    context_1 = XContext(dependencies=[2])

    def verify_current_context_is_copy():
        copied_context: XContext = XContext.grab()

        # ensure they are not the same object (ie: it got copied), and the parent is correct.
        assert context_1 is not copied_context
        assert copied_context.parent is context_1
        assert copied_context._sibling is context_1

        # See if the non-active Context can dynamically look up it's parent as the
        # currently active XContext.
        assert XContext().parent is copied_context

        # Ensure dependencies at copied.
        assert copied_context._dependencies == {int: 2}

    with context_1 as current_context:
        assert XContext.grab() is current_context

        with context_1 as current_context_2:
            assert XContext.grab() is current_context_2
            assert XContext.grab() is not current_context
            verify_current_context_is_copy()

    # check to make sure same behavior happens when using context as a decorator.
    @context_1
    def my_method():
        assert XContext.grab() is context_1
        # verify_current_context_is_copy()

    my_method()


module_level_context = XContext(
    dependencies=[
        20,
        "hello-str",
        SomeDependency(my_name="start-name")
    ]
)


# I want to test it out here, because pytest looks at the argument list of the function
# in order to know what (if any) fixtures to inject.
# If our decorator is not setup correctly, pytest won't call our test-method correctly.
# So having pycharm call our test method correctly is a excellent edge-case test in of its self!
@module_level_context.copy()
def test_module_level_context(xinject_test_context):
    # `context` is the base-context
    XContext.grab().add(1.2)
    assert XContext.current(float) == 1.2

    # Ensure that when we used the module-level-context, ensure it still uses the current
    # context as it's first parent. the `create=False` will ensure it won't add this looked
    # up dependency to its self.
    assert module_level_context.dependency(for_type=float, create=False) == 1.2

    # Should be the same object since we have not been called recursively.
    assert module_level_context is not XContext.grab()

    # Ensure that we don't have a float dependency in the outer-module version
    # (since create=False).
    assert float not in module_level_context._dependencies

    # See if the copied-context has the same dependencies still
    assert SomeDependency.grab().my_name == "start-name"
    assert XContext.current(int) == 20
    assert XContext.current(str) == "hello-str"


def test_initial_context_resources_with_dict():
    my_context = XContext(
        dependencies={int: 'string-as-int-dependency', float: False, SomeDependency: 'str-instead'}
    )

    with my_context:
        # SomeDependency was replaced by a direct-string 'str-instead', testing replacing
        # dependencies with a completely different type
        # (if you want to mock/test something specific).
        assert SomeDependency.grab() == 'str-instead'
        assert XContext.current(int) == 'string-as-int-dependency'
        assert XContext.current(float) is False


def test_deepcopy_context():
    c1 = XContext()
    with pytest.raises(NotImplementedError):
        deepcopy(c1)


@dataclasses.dataclass
class ATestDependency(Dependency):
    my_name: str = 'hello!'


module_level_test_resource = ATestDependency.grab()
print(module_level_test_resource)
module_level_test_resource.my_name = "module-level-change"


# We run unit-test twice, ensure that each run of a unit test runs in it's own blank root context.
@pytest.mark.parametrize("test_run", [1, 2])
def test_module_level_resource_in_unit_test(test_run):
    # Make sure we have the same TestDependency instance, as global dependencies are kept between unit-test runs.
    assert module_level_test_resource is ATestDependency.grab()

    # Check values, see if they are still at the module-level value
    assert ATestDependency.grab().my_name == "module-level-change"

    # Do a unit-test change, ensure we don't see it in another unit test.
    with ATestDependency() as obj:
        obj.my_name = "unit-test-change"
        assert ATestDependency.grab().my_name == "unit-test-change"

    assert ATestDependency.grab().my_name == "module-level-change"


def test_each_unit_test_starts_with_a_single_parentless_root_like_context():
    # Ensure we have no parent.
    unit_test_root_context = XContext.grab()

    # We should only have a thread-root context that is pointing to a single parent app-root.
    assert unit_test_root_context.parent.parent is None

    # Ensure we have no items in the XContext, that it is indeed blank.
    assert len(unit_test_root_context._dependencies) == 0

    # Ensure that when we use the root-like blank unit test context inside a `with` statement,
    # we have a new context with its parent set at our root-like blank unit test context.
    with unit_test_root_context as new_context:
        assert unit_test_root_context is not new_context
        assert new_context.parent is unit_test_root_context


class TestSkipAttrOnCopyDependency(Dependency, attributes_to_skip_while_copying=['my_attribute']):
    my_attribute = "hello-1"  # Defined at class-level, not object-level
    my_other_attr = "hello-2"  # Defined at class-level, not object-level


def test_skip_attrs_on_resource_copy():
    r1 = TestSkipAttrOnCopyDependency()
    assert r1.my_attribute == "hello-1"
    assert r1.my_other_attr == "hello-2"

    r1.my_attribute = 'changed_value-1'
    assert r1.my_attribute == "changed_value-1"

    r1.my_other_attr = 'changed_value-2'
    assert r1.my_other_attr == "changed_value-2"

    r2 = copy(r1)
    assert r2 is not r1

    assert r1.my_attribute == "changed_value-1"
    assert r1.my_other_attr == "changed_value-2"

    assert r2.my_attribute == "hello-1"
    assert r2.my_other_attr == "changed_value-2"

    r2.my_attribute = "changed_value-1.2"
    r2.my_other_attr = "changed_value-2.2"

    r3 = deepcopy(r2)
    assert r2.my_attribute == "changed_value-1.2"
    assert r2.my_other_attr == "changed_value-2.2"

    assert r3.my_attribute == "hello-1"
    assert r3.my_other_attr == "changed_value-2.2"
