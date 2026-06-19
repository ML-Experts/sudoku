import type {
  Uc18DeleteBoardFileAction,
  Uc18DeleteBoardFileState,
} from "./uc18DeleteBoardFileTypes";

export function uc18DeleteBoardFileReducer(
  state: Uc18DeleteBoardFileState,
  action: Uc18DeleteBoardFileAction
): Uc18DeleteBoardFileState {
  switch (action.type) {
    case "stateReset":
      return {
        status: "idle",
        boardFileKey: null,
        boardFolderName: null,
        remainingItemsCount: null,
        error: null,
        errorType: null,
        httpStatus: null,
      };
    case "deleteStarted":
      return {
        ...state,
        status: "deleting",
        boardFileKey: action.boardFileKey,
        boardFolderName: action.boardFolderName,
        remainingItemsCount: null,
        error: null,
        errorType: null,
        httpStatus: null,
      };
    case "deleteSucceeded":
      return {
        ...state,
        status: "success",
        boardFileKey: action.boardFileKey,
        boardFolderName: action.boardFolderName,
        remainingItemsCount: action.remainingItemsCount,
        error: null,
        errorType: null,
        httpStatus: 200,
      };
    case "deleteFailed":
      return {
        ...state,
        status: "error",
        boardFileKey: action.boardFileKey,
        boardFolderName: action.boardFolderName,
        remainingItemsCount: null,
        error: action.error,
        errorType: action.errorType,
        httpStatus: action.httpStatus,
      };
    default:
      return state;
  }
}
