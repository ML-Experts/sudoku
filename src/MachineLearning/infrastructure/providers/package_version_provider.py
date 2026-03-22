from importlib.metadata import version as package_version


class ImportlibPackageVersionProvider:
    def get_version(self, package_name: str) -> str:
        return package_version(package_name)
