export type AlgorithmChoice = "GA" | "CSP";

export interface GAParameters {
  populationSize: number;
  maxGenerations: number;
  crossoverProb: number;
  mutationRate: number;
}

export interface CSPParameters {
  useMRV: boolean;
  useDegree: boolean;
  useLCV: boolean;
  useForwardChecking: boolean;
  useAC3Preprocess: boolean;
  useIncrementalAC3: boolean;
}

export interface SoftObjectiveWeights {
  s1FacultyPreferences: number; // default 1.0
  s2MinimizeGaps: number;        // default 2.0
  s3AvoidConsecutive: number;    // default 1.5
  s4BalancedWorkload: number;    // default 1.0
}

export interface WizardDraftState {
  step: number;
  department: string;
  term: string;
  academicYear: string;
  selectedCourseIds: string[];
  selectedGroupIds: string[];
  selectedRoomIds: string[];
  algorithm: AlgorithmChoice;
  gaParams: GAParameters;
  cspParams: CSPParameters;
  softWeights: SoftObjectiveWeights;
  lastSavedAt?: string;
}
