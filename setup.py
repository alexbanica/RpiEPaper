from setuptools import setup

try:
    from wheel.bdist_wheel import bdist_wheel
except ModuleNotFoundError:  # pragma: no cover - depends on environment toolchain
    try:
        from setuptools.command.bdist_wheel import bdist_wheel
    except ModuleNotFoundError:  # pragma: no cover - depends on environment toolchain
        bdist_wheel = None


if bdist_wheel is not None:

    class NonPureBDistWheel(bdist_wheel):
        def finalize_options(self):
            super().finalize_options()
            self.root_is_pure = False
            self.abi_tag = "none"
            self.py_limited_api = False

        def get_tag(self):
            _, __, plat_name = super().get_tag()
            return "py3", "none", plat_name

    setup(cmdclass={"bdist_wheel": NonPureBDistWheel})
else:
    setup()
