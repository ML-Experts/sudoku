function createAbortError(): Error {
  return new DOMException("Operacja wczytywania obrazu zostala anulowana.", "AbortError");
}

export function loadImageElement(
  sourceUrl: string,
  signal?: AbortSignal,
): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(createAbortError());
      return;
    }

    const image = new Image();

    const cleanup = () => {
      image.onload = null;
      image.onerror = null;
      signal?.removeEventListener("abort", handleAbort);
    };

    const handleAbort = () => {
      cleanup();
      reject(createAbortError());
    };

    image.onload = () => {
      cleanup();
      resolve(image);
    };

    image.onerror = () => {
      cleanup();
      reject(new Error("Nie udalo sie wczytac obrazu do elementu HTMLImageElement."));
    };

    signal?.addEventListener("abort", handleAbort, { once: true });
    image.src = sourceUrl;
  });
}
