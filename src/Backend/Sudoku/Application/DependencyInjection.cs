using FluentValidation;
using MediatR;
using Microsoft.Extensions.DependencyInjection;
using Sudoku.Application.Abstractions;
using Sudoku.Application.Behaviors;
using Sudoku.Application.ModelsActive;
using Sudoku.Application.SudokuSolve;
using Sudoku.Application.Trainings;

namespace Sudoku.Application;

public static class DependencyInjection
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        services.AddMediatR(configuration =>
        {
            configuration.RegisterServicesFromAssembly(typeof(DependencyInjection).Assembly);
            configuration.AddOpenBehavior(typeof(ValidationBehavior<,>));
        });
        services.AddValidatorsFromAssembly(typeof(DependencyInjection).Assembly);
        services.AddTransient<IActiveModelResolver, ActiveModelResolver>();
        services.AddTransient<ISudokuBacktrackingSolver, SudokuBacktrackingSolver>();
        services.AddTransient<ISudokuSolveSessionRunner, SudokuSolveSessionRunner>();
        services.AddTransient<ITrainingRunCancellationRecovery, TrainingRunCancellationRecovery>();
        services.AddSingleton<ITrainingRunNameGenerator, TrainingRunNameGenerator>();
        services.AddSingleton<ITrainingRunEventLockProvider, InMemoryTrainingRunEventLockProvider>();
        services.AddSingleton<ITrainingRunEventPublisher, NoOpTrainingRunEventPublisher>();
        services.AddSingleton<ISolveSessionIdGenerator, SolveSessionIdGenerator>();
        services.AddSingleton<ISolveSessionLockProvider, InMemorySolveSessionLockProvider>();
        services.AddSingleton<ISudokuSolveEventPublisher, NoOpSudokuSolveEventPublisher>();

        return services;
    }
}
