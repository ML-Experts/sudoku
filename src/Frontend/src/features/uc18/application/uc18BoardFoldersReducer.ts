import type {
  Uc18BoardFoldersAction,
  Uc18BoardFoldersState,
} from "./uc18BoardFoldersTypes";

export function uc18BoardFoldersReducer(
  state: Uc18BoardFoldersState,
  action: Uc18BoardFoldersAction
): Uc18BoardFoldersState {
  switch (action.type) {
    case "stateReset":
      return {
        status: "idle",
        preparationName: null,
        folders: [],
        totalCount: 0,
        selectedSourceName: null,
        error: null,
        errorType: null,
        httpStatus: null,
      };
    case "loadStarted": {
      const isSamePreparation = state.preparationName === action.preparationName;

      return {
        ...state,
        status: "loading",
        preparationName: action.preparationName,
        folders: isSamePreparation ? state.folders : [],
        totalCount: isSamePreparation ? state.totalCount : 0,
        selectedSourceName: isSamePreparation ? state.selectedSourceName : null,
        error: null,
        errorType: null,
        httpStatus: null,
      };
    }
    case "loadSucceeded":
      return {
        ...state,
        status: "success",
        preparationName: action.preparationName,
        folders: action.folders,
        totalCount: action.totalCount,
        selectedSourceName: action.selectedSourceName,
        error: null,
        errorType: null,
        httpStatus: 200,
      };
    case "loadFailed":
      return {
        ...state,
        status: "error",
        preparationName: action.preparationName,
        selectedSourceName: action.clearSelection ? null : state.selectedSourceName,
        error: action.error,
        errorType: action.errorType,
        httpStatus: action.httpStatus,
      };
    case "selectionChanged":
      return {
        ...state,
        selectedSourceName: action.sourceName,
      };
    default:
      return state;
  }
}
