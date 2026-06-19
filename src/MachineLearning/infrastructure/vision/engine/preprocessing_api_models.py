from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ImageApiEntry:
    mime_type: str
    base64: str

    def __post_init__(self) -> None:
        if not self.mime_type.strip():
            raise ValueError("mime_type cannot be empty.")
        if not self.base64.strip():
            raise ValueError("base64 cannot be empty.")

    def model_dump(self, by_alias: bool = False) -> dict[str, str]:
        if by_alias:
            return {
                "mimeType": self.mime_type,
                "base64": self.base64,
            }
        return {
            "mime_type": self.mime_type,
            "base64": self.base64,
        }


@dataclass(frozen=True, slots=True)
class ImageApiResponse:
    mime_type: str
    base64: str

    def __post_init__(self) -> None:
        if not self.mime_type.strip():
            raise ValueError("mime_type cannot be empty.")
        if not self.base64.strip():
            raise ValueError("base64 cannot be empty.")

    def model_dump(self, by_alias: bool = False) -> dict[str, str]:
        if by_alias:
            return {
                "mimeType": self.mime_type,
                "base64": self.base64,
            }
        return {
            "mime_type": self.mime_type,
            "base64": self.base64,
        }


@dataclass(frozen=True, slots=True)
class CellsGridApiResponse:
    cells: list[list[ImageApiResponse]]

    def __post_init__(self) -> None:
        if not self.cells:
            raise ValueError("cells cannot be empty.")
        if any(not row for row in self.cells):
            raise ValueError("cells rows cannot be empty.")

    def model_dump(
        self,
        by_alias: bool = False,
    ) -> dict[str, list[list[dict[str, str]]]]:
        return {
            "cells": [
                [cell.model_dump(by_alias=by_alias) for cell in row]
                for row in self.cells
            ]
        }


@dataclass(frozen=True, slots=True)
class ErrorApiResponse:
    error_type: str
    message: str

    def __post_init__(self) -> None:
        if not self.error_type.strip():
            raise ValueError("error_type cannot be empty.")
        if not self.message.strip():
            raise ValueError("message cannot be empty.")

    def model_dump(self, by_alias: bool = False) -> dict[str, str]:
        if by_alias:
            return {
                "errorType": self.error_type,
                "message": self.message,
            }
        return {
            "error_type": self.error_type,
            "message": self.message,
        }


__all__ = [
    "CellsGridApiResponse",
    "ErrorApiResponse",
    "ImageApiEntry",
    "ImageApiResponse",
]
