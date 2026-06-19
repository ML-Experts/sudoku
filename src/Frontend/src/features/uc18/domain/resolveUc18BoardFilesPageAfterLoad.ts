export type Uc18BoardFilesPageResolution = {
  requestedPage: number;
  responsePage: number;
  responsePageSize: number;
  lastPage: number;
  shouldReloadLastPage: boolean;
};

export function resolveUc18BoardFilesPageAfterLoad(
  requestedPage: number,
  responsePage: number,
  responsePageSize: number,
  totalCount: number,
  itemsCount: number
): Uc18BoardFilesPageResolution {
  const safePageSize = responsePageSize > 0 ? responsePageSize : 1;
  const lastPage = Math.max(1, Math.ceil(totalCount / safePageSize));
  const requestedPageExceedsLastPage = totalCount > 0 && requestedPage > lastPage;
  const backendDidNotClampToLastPage = responsePage !== lastPage;
  const receivedEmptyOutOfRangePage =
    itemsCount === 0 && totalCount > 0 && responsePage > lastPage;

  return {
    requestedPage,
    responsePage,
    responsePageSize: safePageSize,
    lastPage,
    shouldReloadLastPage:
      requestedPageExceedsLastPage &&
      (backendDidNotClampToLastPage || receivedEmptyOutOfRangePage),
  };
}
