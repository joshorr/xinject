import asyncio
import random

from xinject import DependencyPerThread, Dependency


def test__yielding_within_dependency_ctx_manager():
    class Dep(Dependency):
        hello = "1"

    def my_generator():
        first_obj = Dep.grab()
        value = first_obj.hello
        yield value
        with Dep() as e:
            e.hello = "c"
            yield Dep.grab().hello
            assert e.hello == 'c'
        yield Dep.grab().hello
        assert value == Dep.grab().hello
        assert first_obj is Dep.grab()

    assert [*my_generator()] == ['1', 'c', '1']

    for v in my_generator():
        assert Dep.grab().hello == v
        with Dep() as obj:
            obj.hello = 'd'
            assert Dep.grab().hello == 'd'


def test__async_task():
    loop = asyncio.new_event_loop()
    counter = 10

    class Dep(Dependency):
        hello = "1"

    Dep.grab().hello = '2'

    async def current_hello():
        await asyncio.sleep(random.uniform(.01, .06))
        return Dep.grab().hello

    async def my_fn(i):
        nonlocal counter
        with Dep() as e:
            await asyncio.sleep(random.uniform(.01, .06))
            counter += 1
            value = f"c-{i}"
            e.hello = value
            assert await current_hello() == value
            await asyncio.sleep(random.uniform(.01, .06))
            assert e.hello == value
            return await current_hello()

    async def my_other_fn(i):
        assert await current_hello() == '2'
        assert await current_hello() == '2'
        assert await current_hello() == '2'
        assert await current_hello() == '2'
        return await current_hello()

    async def my_fn2(i):
        nonlocal counter
        with Dep() as e1:
            counter += 1
            value1 = f"d-{i}"
            e1.hello = value1
            with Dep() as e2:
                counter += 1
                value2 = f"e-{i+1}"
                e2.hello = value2
                await asyncio.sleep(random.uniform(.01, .06))
                assert await current_hello() == value2
                await asyncio.sleep(random.uniform(.01, .06))
                assert e2.hello == value2
            assert await current_hello() == value1
            return await current_hello()

    async def my_fn3(i):
        nonlocal counter
        with Dep() as e:
            await asyncio.sleep(random.uniform(.01, .06))
            counter += 1
            value = f"e-{i}"
            e.hello = value
            assert await current_hello() == value
            await asyncio.sleep(random.uniform(.01, .06))
            assert e.hello == value
            value_out = e.hello
        return await current_hello(), value_out

    tasks = []

    with Dep() as e:
        e.hello = 'b'
        tasks.append(loop.create_task(my_fn3(10)))

    tasks.extend([
        loop.create_task(my_fn(20)),
        loop.create_task(my_fn(30)),
        loop.create_task(my_other_fn(40)),
        loop.create_task(my_fn(50)),
        loop.create_task(my_fn2(60)),
        loop.create_task(my_fn(70)),
        loop.create_task(my_other_fn(80))
    ])
    gather_result = asyncio.gather(*tasks)
    loop.run_until_complete(gather_result)
    assert gather_result.result() == [('b', 'e-10'), 'c-20', 'c-30', '2', 'c-50', 'd-60', 'c-70', '2']
    assert Dep.grab().hello == '2'

