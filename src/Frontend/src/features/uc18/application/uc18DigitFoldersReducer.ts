import type {
  Uc18DigitFoldersAction,
  Uc18DigitFoldersState,
} from "./uc18DigitFoldersTypes";

export function uc18DigitFoldersReducer(
  state: Uc18DigitFoldersState,
  action: Uc18DigitFoldersAction
): Uc18DigitFoldersState {
  switch (action.type) {
    case "stateReset":
      return {
        status: "idle",
        preparationName: null,
        folders: [],
        totalCount: 0,
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
        error: null,
        errorType: null,
        httpStatus: 200,
      };
    case "loadFailed":
      return {
        ...state,
        status: "error",
        preparationName: action.preparationName,
        error: action.error,
        errorType: action.errorType,
        httpStatus: action.httpStatus,
      };
    default:
      return state;
  }
}
