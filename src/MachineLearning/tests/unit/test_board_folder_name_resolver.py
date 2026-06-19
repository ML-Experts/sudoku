import unittest

from infrastructure.datasets.board_folder_name_resolver import (
    BoardFolderNameResolver,
)


class BoardFolderNameResolverTests(unittest.TestCase):
    def test_resolve_should_use_relative_group_key_without_extension(self) -> None:
        resolver = BoardFolderNameResolver()

        result = resolver.resolve(
            board_name="Image1",
            group_key="nested/Image1.jpg",
            already_used=tuple(),
        )

        self.assertEqual(result, "nested__Image1")

    def test_resolve_should_append_suffix_when_name_collides(self) -> None:
        resolver = BoardFolderNameResolver()

        result = resolver.resolve(
            board_name="Image1",
            group_key="nested/Image1.jpg",
            already_used=("nested__Image1",),
        )

        self.assertEqual(result, "nested__Image1-2")

    def test_resolve_should_be_stable_for_same_input(self) -> None:
        resolver = BoardFolderNameResolver()

        first = resolver.resolve(
            board_name="Image1",
            group_key="a/b/Image1.jpg",
            already_used=tuple(),
        )
        second = resolver.resolve(
            board_name="Image1",
            group_key="a/b/Image1.jpg",
            already_used=tuple(),
        )

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
