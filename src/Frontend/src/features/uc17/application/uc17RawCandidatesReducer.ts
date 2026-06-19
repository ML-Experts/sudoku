import type {
  Uc17RawCandidatesAction,
  Uc17RawCandidatesState,
} from "./uc17RawCandidatesTypes";

export function uc17RawCandidatesReducer(
  state: Uc17RawCandidatesState,
  action: Uc17RawCandidatesAction
): Uc17RawCandidatesState {
  switch (action.type) {
    case "loadStarted":
      return {
        ...state,
        status: "loading",
        error: null,
        errorType: null,
        httpStatus: null,
      };
    case "loadSucceeded":
      return {
        ...state,
        status: "success",
        candidates: action.candidates,
        selectedKeys: action.selectedKeys,
        error: null,
        errorType: null,
        httpStatus: 200,
        unknownTypeCount: action.unknownTypeCount,
      };
    case "loadFailed":
      return {
        ...state,
        status: "error",
        error: action.error,
        errorType: action.errorType,
        httpStatus: action.httpStatus,
      };
    case "selectionToggled":
      return {
        ...state,
        selectedKeys: state.selectedKeys.includes(action.candidateKey)
          ? state.selectedKeys.filter((key) => key !== action.candidateKey)
          : [...state.selectedKeys, action.candidateKey],
      };
    default:
      return state;
  }
}
