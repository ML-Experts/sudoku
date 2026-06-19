import type {
  Uc18BoardImageAction,
  Uc18BoardImageState,
} from "./uc18BoardImageTypes";

export function uc18BoardImageReducer(
  state: Uc18BoardImageState,
  action: Uc18BoardImageAction
): Uc18BoardImageState {
  switch (action.type) {
    case "stateReset":
      return {
        status: "idle",
        requestKey: null,
        imageDataUrl: null,
        error: null,
        errorType: null,
        httpStatus: null,
      };
    case "loadStarted":
      return {
        status: "loading",
        requestKey: action.requestKey,
        imageDataUrl: null,
        error: null,
        errorType: null,
        httpStatus: null,
      };
    case "loadSucceeded":
      if (state.requestKey !== action.requestKey) {
        return state;
      }

      return {
        status: "success",
        requestKey: action.requestKey,
        imageDataUrl: action.imageDataUrl,
        error: null,
        errorType: null,
        httpStatus: 200,
      };
    case "loadFailed":
      if (state.requestKey !== action.requestKey) {
        return state;
      }

      return {
        status: "error",
        requestKey: action.requestKey,
        imageDataUrl: null,
        error: action.error,
        errorType: action.errorType,
        httpStatus: action.httpStatus,
      };
    default:
      return state;
  }
}
