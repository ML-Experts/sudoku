using Microsoft.AspNetCore.Mvc;

namespace Sudoku.Contracts;

public sealed class UploadExampleApiEntry
{
    [FromForm(Name = "file")]
    public IFormFile? File { get; init; }
}
