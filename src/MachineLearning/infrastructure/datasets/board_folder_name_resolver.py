class BoardFolderNameResolver:
    def resolve(
        self,
        board_name: str,
        group_key: str,
        already_used: tuple[str, ...],
    ) -> str:
        del board_name

        relative_without_extension = group_key.rsplit(".", maxsplit=1)[0]
        candidate = self._sanitize(relative_without_extension)
        if candidate not in already_used:
            return candidate

        suffix = 2
        while True:
            suffixed_candidate = f"{candidate}-{suffix}"
            if suffixed_candidate not in already_used:
                return suffixed_candidate
            suffix += 1

    def _sanitize(self, value: str) -> str:
        sanitized = value.strip()
        sanitized = sanitized.replace("\\", "__").replace("/", "__")
        sanitized = sanitized.replace(":", "_").replace(" ", "_")
        return sanitized or "board"
