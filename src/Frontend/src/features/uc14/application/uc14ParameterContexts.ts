import type { Uc14ActiveParameterContext } from "../domain/uc14ParameterContext";

type Uc14NavigationState = {
  activeView: string;
  datasetsStep?: string;
  examplesWorkflowContext?: Uc14ActiveParameterContext;
};

export function getUc14ActiveParameterContext({
  activeView,
  datasetsStep,
  examplesWorkflowContext,
}: Uc14NavigationState): Uc14ActiveParameterContext {
  if (activeView === "examples") {
    return examplesWorkflowContext ?? null;
  }

  if (activeView === "datasets" && datasetsStep === "uc06") {
    return "trainingRun";
  }

  return null;
}
