type PromiseTask<T> = () => Promise<T>;

type RunPromisePoolOptions<T> = {
  tasks: PromiseTask<T>[];
  concurrency: number;
};

export async function runPromisePool<T>({
  tasks,
  concurrency,
}: RunPromisePoolOptions<T>): Promise<T[]> {
  if (!Number.isInteger(concurrency) || concurrency <= 0) {
    throw new Error("Concurrency promise pool musi byc dodatnia liczba calkowita.");
  }

  if (tasks.length === 0) {
    return [];
  }

  const results = new Array<T>(tasks.length);
  let nextTaskIndex = 0;
  let firstError: unknown = null;

  async function worker(): Promise<void> {
    while (true) {
      if (firstError !== null) {
        return;
      }

      const currentTaskIndex = nextTaskIndex;
      nextTaskIndex += 1;

      if (currentTaskIndex >= tasks.length) {
        return;
      }

      try {
        results[currentTaskIndex] = await tasks[currentTaskIndex]();
      } catch (error) {
        firstError = error;
        return;
      }
    }
  }

  await Promise.all(
    Array.from({ length: Math.min(concurrency, tasks.length) }, () => worker()),
  );

  if (firstError !== null) {
    throw firstError;
  }

  return results;
}
