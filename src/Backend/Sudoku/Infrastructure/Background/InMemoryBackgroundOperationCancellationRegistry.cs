using System.Collections.Concurrent;
using Sudoku.Application.Abstractions;

namespace Sudoku.Infrastructure.Background;

public sealed class InMemoryBackgroundOperationCancellationRegistry : IBackgroundOperationCancellationRegistry
{
    private readonly ConcurrentDictionary<string, CancellationTokenSource> _registrations = new(StringComparer.Ordinal);

    public CancellationToken Register(string operationId)
    {
        if (string.IsNullOrWhiteSpace(operationId))
        {
            throw new ArgumentException("Operation id is required.", nameof(operationId));
        }

        var cancellationTokenSource = new CancellationTokenSource();
        if (!_registrations.TryAdd(operationId, cancellationTokenSource))
        {
            cancellationTokenSource.Dispose();
            throw new InvalidOperationException(
                $"Background operation '{operationId}' is already registered for cancellation.");
        }

        return cancellationTokenSource.Token;
    }

    public bool TryGetCancellationToken(string operationId, out CancellationToken cancellationToken)
    {
        if (_registrations.TryGetValue(operationId, out var cancellationTokenSource))
        {
            cancellationToken = cancellationTokenSource.Token;
            return true;
        }

        cancellationToken = CancellationToken.None;
        return false;
    }

    public bool TryCancel(string operationId)
    {
        if (!_registrations.TryGetValue(operationId, out var cancellationTokenSource))
        {
            return false;
        }

        cancellationTokenSource.Cancel();
        return true;
    }

    public void Complete(string operationId)
    {
        if (_registrations.TryRemove(operationId, out var cancellationTokenSource))
        {
            cancellationTokenSource.Dispose();
        }
    }
}
