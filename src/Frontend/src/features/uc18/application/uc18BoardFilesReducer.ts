import type {
  Uc18BoardFilesAction,
  Uc18BoardFilesState,
} from "./uc18BoardFilesTypes";

export function uc18BoardFilesReducer(
  state: Uc18BoardFilesState,
  action: Uc18BoardFilesAction
): Uc18BoardFilesState {
  switch (action.type) {
    case "stateReset":
      return {
        status: "idle",
        preparationName: null,
        sourceName: null,
        items: [],
        page: 1,
        pageSize: state.pageSize,
        totalCount: 0,
        error: null,
        errorType: null,
        httpStatus: null,
      };
    case "loadStarted": {
      const isSameScope =
        state.preparationName === action.preparationName &&
        state.sourceName === action.sourceName;

      return {
        ...state,
        status: "loading",
        preparationName: action.preparationName,
        sourceName: action.sourceName,
        items: isSameScope ? state.items : [],
        page: action.page,
        pageSize: action.pageSize,
        totalCount: isSameScope ? state.totalCount : 0,
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
        sourceName: action.sourceName,
        items: action.items,
        page: action.page,
        pageSize: action.pageSize,
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
        sourceName: action.sourceName,
        items: action.clearItems ? [] : state.items,
        page: action.page,
        pageSize: action.pageSize,
        totalCount: action.clearItems ? 0 : state.totalCount,
        error: action.error,
        errorType: action.errorType,
        httpStatus: action.httpStatus,
      };
    default:
      return state;
  }
}
