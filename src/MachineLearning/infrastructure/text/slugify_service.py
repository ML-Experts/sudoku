from slugify import slugify


class PythonSlugifyService:
    def slugify(self, value: str) -> str:
        return slugify(value)
