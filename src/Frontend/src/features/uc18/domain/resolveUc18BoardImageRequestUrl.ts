export function resolveUc18BoardImageRequestUrl(
  apiBaseUrl: string,
  imageEndpoint: string
): string {
  const trimmedEndpoint = imageEndpoint.trim();

  if (!trimmedEndpoint) {
    return "";
  }

  if (
    trimmedEndpoint.startsWith("http://") ||
    trimmedEndpoint.startsWith("https://")
  ) {
    return trimmedEndpoint;
  }

  if (trimmedEndpoint.startsWith("/")) {
    return trimmedEndpoint;
  }

  const normalizedBaseUrl = apiBaseUrl.replace(/\/+$/, "");
  const normalizedEndpoint = trimmedEndpoint.replace(/^\/+/, "");

  return `${normalizedBaseUrl}/${normalizedEndpoint}`;
}
