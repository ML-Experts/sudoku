using FluentValidation;
using MediatR;
using Sudoku.Application.Behaviors;
using Microsoft.Extensions.DependencyInjection;
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
        services.AddSingleton<ITrainingRunNameGenerator, TrainingRunNameGenerator>();
        services.AddSingleton<ITrainingRunEventLockProvider, InMemoryTrainingRunEventLockProvider>();
        services.AddSingleton<Sudoku.Application.Abstractions.ITrainingRunEventPublisher, NoOpTrainingRunEventPublisher>();

        return services;
    }
}
