export function buildHubUrl(
  progressChannelUrl: string,
  apiBaseUrl: string,
): string {
  if (
    progressChannelUrl.startsWith("http://") ||
    progressChannelUrl.startsWith("https://")
  ) {
    return progressChannelUrl;
  }

  if (apiBaseUrl.startsWith("http://") || apiBaseUrl.startsWith("https://")) {
    return new URL(progressChannelUrl, apiBaseUrl).toString();
  }

  return progressChannelUrl.startsWith("/")
    ? progressChannelUrl
    : `/${progressChannelUrl}`;
}
