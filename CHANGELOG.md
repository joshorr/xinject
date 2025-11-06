# Changelog

## [1.4.1](https://github.com/xyngular/py-xinject/compare/v1.4.0...v1.4.1) (2023-04-15)


### Bug Fixes

* license ([709f49e](https://github.com/xyngular/py-xinject/commit/709f49e7a107b51f6223f4a7b781c62f254c807c))

## [1.4.0](https://github.com/xyngular/py-xinject/compare/v1.3.0...v1.4.0) (2023-02-19)


### Features

* have proxy also forward set/get item dunder methods. ([e471b71](https://github.com/xyngular/py-xinject/commit/e471b7115c2e580e5065280ac11991384ce3bf3b))

## [1.3.0](https://github.com/xyngular/py-xinject/compare/v1.2.0...v1.3.0) (2023-02-03)


### Features

* added ability to easily proxy an attribute on dependency. ([0ff42a0](https://github.com/xyngular/py-xinject/commit/0ff42a09c78d16ceaa3981aff25d5c281934944d))


### Bug Fixes

* style, add doc comment. ([3ad3817](https://github.com/xyngular/py-xinject/commit/3ad38173d30c3f03184630b7af78f2b89f04d237))

## [1.2.0](https://github.com/xyngular/py-xinject/compare/v1.1.0...v1.2.0) (2023-01-02)


### Features

* renamed resource-refs to dependency-refs terminology; ie: `resource_chain() -&gt; dependency_chain()` ([f1f7b08](https://github.com/xyngular/py-xinject/commit/f1f7b08401cf21b1fdbd78c55c3e868205e9c85e))

## [1.1.0](https://github.com/xyngular/py-xinject/compare/v1.0.2...v1.1.0) (2022-12-13)


### Features

* update deps. ([0c49054](https://github.com/xyngular/py-xinject/commit/0c49054de4f00e825234531c0b14ea9587d209da))


### Bug Fixes

* fixes a bug where if you activate a dependency before the thread-root context is created. ([0bb778c](https://github.com/xyngular/py-xinject/commit/0bb778c79a2a39b81041b7e848fb1a7a35f3fd08))

## [1.0.2](https://github.com/xyngular/py-xinject/compare/v1.0.1...v1.0.2) (2022-11-20)


### Documentation

* fix readme pypi pointer. ([e775c81](https://github.com/xyngular/py-xinject/commit/e775c8126e5f7419796102271797ea3479b1c1f3))

## [1.0.1](https://github.com/xyngular/py-xinject/compare/v1.0.0...v1.0.1) (2022-11-20)


### Bug Fixes

* add missing metadata to package. ([ced4cea](https://github.com/xyngular/py-xinject/commit/ced4cea1a53287d4d2e7206d0e2b7a4ea71b2e3c))

## [1.0.0](https://github.com/xyngular/py-xinject/compare/v0.4.0...v1.0.0) (2022-11-20)


### Features

* release as version 1.0.0 ([a971752](https://github.com/xyngular/py-xinject/commit/a971752c0a4c6d189d048969ec79a7ff06a537bb))

## [0.4.0](https://github.com/xyngular/py-xinject/compare/v0.3.0...v0.4.0) (2022-11-20)


### Features

* added `obj` class property on Dependency to more easily get current dependency object. ([e7de56e](https://github.com/xyngular/py-xinject/commit/e7de56e84c657a98ea47fedf3d3021b51f218eec))
* precent context from copying unless needed. ([3e0940c](https://github.com/xyngular/py-xinject/commit/3e0940c0ce215397127078b68e2d3acf2cf2d4c3))
* Proxy str/repr functions. ([0991475](https://github.com/xyngular/py-xinject/commit/0991475a25f71fd8c4891baa9d5fe6cbb5a794a0))
* rearranged docs to make them more clear. ([2d55d38](https://github.com/xyngular/py-xinject/commit/2d55d388b1bcd61675befc9f55c2976d87961eaf))
* rename ActiveResourceProxy to CurrentDependencyProxy ([5474533](https://github.com/xyngular/py-xinject/commit/5474533fc34fe11c55146ffd228254879a1e0edb))
* rename file to new name. ([e5bf973](https://github.com/xyngular/py-xinject/commit/e5bf97399975dbd312aa828a196d63e8cb7bcfb4))
* rename library to final name `xinject`. ([be567e4](https://github.com/xyngular/py-xinject/commit/be567e4b84a6d7c47eef7df2685abf6187cc6ffb))
* renamed `resource()` into `grab()`, a simpler and more obvious name for what it does. ([aafcec8](https://github.com/xyngular/py-xinject/commit/aafcec82d53d19c94e18523755de8e8ed269a9c6))
* renamed glazy into udepend in general. ([f302abe](https://github.com/xyngular/py-xinject/commit/f302abefba6b87fa109068a50d2fd49c6c7866f9))
* renamed guards to xsentinels. ([750d987](https://github.com/xyngular/py-xinject/commit/750d98771ea41a35c52d258d4ba7c6433e15d544))
* return self if calling dependency without args (supports future Dependency.grab() syntax). ([c2ebe5b](https://github.com/xyngular/py-xinject/commit/c2ebe5b2f801c59592afd15c229eac5f85c1b70d))
* simplified `grab` method; updated doc-comment; renamed to DependecyPerThread. ([40a2052](https://github.com/xyngular/py-xinject/commit/40a2052f07e14258bcacb2fce52dba0895f50814))


### Bug Fixes

* doc links ([4d0fdb0](https://github.com/xyngular/py-xinject/commit/4d0fdb03a525de5d892d8b560075b774de33aa84))
* doc-comments + thread-sharable feature. ([2da6a76](https://github.com/xyngular/py-xinject/commit/2da6a764d57077ba5a1315a54b1ec099b84f50cf))
* forgot to rename UDependError to XInjectError. ([7c4bf11](https://github.com/xyngular/py-xinject/commit/7c4bf1184b3d3864fe2d27bf73a8253d5df8e0dd))
* more emphasis on doc-link. ([325a191](https://github.com/xyngular/py-xinject/commit/325a191dd92a4c2b21cb7b0eec80f9c77e183b4c))
* use NotImplementedError instead of just NotImplemented. ([24dbaa0](https://github.com/xyngular/py-xinject/commit/24dbaa0a4fd32c52b65c60271771e64fafc2d4ee))


### Documentation

* capitalized API Reference ([a82f9ed](https://github.com/xyngular/py-xinject/commit/a82f9edf89ef3594620ecfbbc616829db56e902c))
* fix readme. ([f2990d5](https://github.com/xyngular/py-xinject/commit/f2990d554552a0eaa8b5e58c2bc2b98269a1d638))
* fix references to `Context` to fully qualified `UContext`. ([6558f12](https://github.com/xyngular/py-xinject/commit/6558f124b96a0957c1fa46bd5bfe4bee0748aac8))
* grammer fix ([c40f472](https://github.com/xyngular/py-xinject/commit/c40f472eaddeeaa4e2360d999b76f91a1260a858))
* Majorly improve documentation. ([5b0af23](https://github.com/xyngular/py-xinject/commit/5b0af2332d10c5b2fd041d81da437d4875f935ab))
* splitting up docs into multiple files. ([71fee52](https://github.com/xyngular/py-xinject/commit/71fee52dcea1e50b154d1f6b3e2b27ae5335bd8b))

## [0.3.0](https://github.com/xyngular/py-xinject/compare/v0.2.0...v0.3.0) (2022-10-08)


### Features

* add api docs ref, change-log... ([f3ffaed](https://github.com/xyngular/py-xinject/commit/f3ffaede7cdb3cae04c8144aa163c357a97cb864))
* add docs. ([bec0deb](https://github.com/xyngular/py-xinject/commit/bec0deb753f12a990f8fa79f75d44e529ad398d4))


### Bug Fixes

* accidentally added .html files... ([4fb10b4](https://github.com/xyngular/py-xinject/commit/4fb10b4a7358cd12b9bbb6c5c18cf30c55dabb0b))
* remove unneeded input to reusable workflow call. ([040e4fd](https://github.com/xyngular/py-xinject/commit/040e4fda9b4a5c69108d7bc9ec492621a7e10e64))
* test-release-process. ([b9c6d8c](https://github.com/xyngular/py-xinject/commit/b9c6d8cd7d4e0febef70296cf49728def5a6e19f))

## [0.2.0](https://github.com/xyngular/py-xinject/compare/v0.1.0...v0.2.0) (2022-10-08)


### Features

* initial code import; experimental; DO NOT USE!!! ([ace5177](https://github.com/xyngular/py-xinject/commit/ace517730bc4ff933386e01300b4050f6072ecfb))


### Bug Fixes

* correct package to include name. ([2d481b4](https://github.com/xyngular/py-xinject/commit/2d481b40f3000becfbbda6379ae52c74b89d8164))

## 0.1.0 (2022-10-08)


### Features

* initial code import; experimental; DO NOT USE!!! ([ace5177](https://github.com/xyngular/py-xinject/commit/ace517730bc4ff933386e01300b4050f6072ecfb))


### Bug Fixes

* correct package to include name. ([2d481b4](https://github.com/xyngular/py-xinject/commit/2d481b40f3000becfbbda6379ae52c74b89d8164))
