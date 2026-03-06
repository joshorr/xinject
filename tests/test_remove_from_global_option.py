from xinject import Dependency


class GlobalDep1(Dependency, remove_between_unittests=True):
    value: str = 'default1'


class GlobalDep2(Dependency):
    value: str = 'default2'


GlobalDep1.grab().value = 'changed1'
GlobalDep2.grab().value = 'changed2'


def test_remove_from_global():
    # Before unit test ran, it should have removed `GlobalDep`,
    # and therefore it will now lazily allocate and have its default value.
    assert GlobalDep1.grab().value == 'default1'
    assert GlobalDep2.grab().value == 'changed2'
