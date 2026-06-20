import type {
  Uc19BoardFoldersSelectionAction,
  Uc19BoardFoldersSelectionState,
} from "./uc19BoardFoldersSelectionTypes";

export function uc19BoardFoldersSelectionReducer(
  state: Uc19BoardFoldersSelectionState,
  action: Uc19BoardFoldersSelectionAction
): Uc19BoardFoldersSelectionState {
  switch (action.type) {
    case "stateReset":
      return {
        status: "idle",
        preparationName: null,
        drafts: [],
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
        drafts: isSamePreparation ? state.drafts : [],
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
        drafts: action.drafts,
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
        drafts: action.clearDrafts ? [] : state.drafts,
        totalCount: action.clearDrafts ? 0 : state.totalCount,
        error: action.error,
        errorType: action.errorType,
        httpStatus: action.httpStatus,
      };
    case "sourceEnabledToggled":
      return {
        ...state,
        drafts: state.drafts.map((draft) =>
          draft.folderName === action.folderName
            ? {
                ...draft,
                enabled: !draft.enabled,
              }
            : draft
        ),
      };
    case "sourceSplitsUpdated":
      return {
        ...state,
        drafts: state.drafts.map((draft) =>
          draft.folderName === action.folderName
            ? {
                ...draft,
                splits: action.splits,
              }
            : draft
        ),
      };
    default:
      return state;
  }
}
