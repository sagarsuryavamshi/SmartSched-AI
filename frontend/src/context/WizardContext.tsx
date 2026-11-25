"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { WizardDraftState, AlgorithmChoice, GAParameters, CSPParameters, SoftObjectiveWeights } from "@/types/wizard";
import { useResources } from "@/context/ResourceContext";

const WIZARD_STORAGE_KEY = "smartsched_wizard_draft_v1";

interface WizardContextType {
  state: WizardDraftState;
  currentStep: number;
  setCurrentStep: (step: number) => void;
  setDepartment: (dept: string) => void;
  setTerm: (term: string) => void;
  setAcademicYear: (year: string) => void;
  toggleCourseSelection: (courseId: string) => void;
  selectAllCourses: (select: boolean) => void;
  toggleGroupSelection: (groupId: string) => void;
  selectAllGroups: (select: boolean) => void;
  toggleRoomSelection: (roomId: string) => void;
  selectAllRooms: (select: boolean) => void;
  setAlgorithm: (alg: AlgorithmChoice) => void;
  setGAParams: (params: Partial<GAParameters>) => void;
  setCSPParams: (params: Partial<CSPParameters>) => void;
  setSoftWeights: (weights: Partial<SoftObjectiveWeights>) => void;
  saveDraftLocally: () => void;
  loadSavedDraft: () => boolean;
  hasSavedDraft: boolean;
  resetDraft: () => void;
  validateCurrentStep: (step: number) => { isValid: boolean; error?: string };
}

const WizardContext = createContext<WizardContextType | null>(null);

export function WizardProvider({ children }: { children: React.ReactNode }) {
  const { courses, studentGroups, classrooms } = useResources();

  const getDefaultState = (): WizardDraftState => ({
    step: 1,
    department: "Department of Computer Science & Engineering",
    term: "Fall Semester (Odd Sem 2026-2027)",
    academicYear: "2026-2027",
    selectedCourseIds: courses.map((c) => c.course_id),
    selectedGroupIds: studentGroups.map((g) => g.group_id),
    selectedRoomIds: classrooms.map((r) => r.room_id),
    algorithm: "GA",
    gaParams: {
      populationSize: 60,
      maxGenerations: 40,
      crossoverProb: 0.85,
      mutationRate: 0.08,
    },
    cspParams: {
      useMRV: true,
      useDegree: true,
      useLCV: true,
      useForwardChecking: true,
      useAC3Preprocess: true,
      useIncrementalAC3: false,
    },
    softWeights: {
      s1FacultyPreferences: 1.0,
      s2MinimizeGaps: 2.0,
      s3AvoidConsecutive: 1.5,
      s4BalancedWorkload: 1.0,
    },
  });

  const [state, setState] = useState<WizardDraftState>(getDefaultState);
  const [hasSavedDraft, setHasSavedDraft] = useState(false);

  // Sync default selection if resources change initially
  useEffect(() => {
    setState((prev) => {
      // If none selected, default to all available
      return {
        ...prev,
        selectedCourseIds: prev.selectedCourseIds.length > 0 ? prev.selectedCourseIds : courses.map((c) => c.course_id),
        selectedGroupIds: prev.selectedGroupIds.length > 0 ? prev.selectedGroupIds : studentGroups.map((g) => g.group_id),
        selectedRoomIds: prev.selectedRoomIds.length > 0 ? prev.selectedRoomIds : classrooms.map((r) => r.room_id),
      };
    });
  }, [courses, studentGroups, classrooms]);

  // Check saved draft in localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(WIZARD_STORAGE_KEY);
      if (saved) {
        setHasSavedDraft(true);
      }
    } catch {
      // localStorage may fail in SSR
    }
  }, []);

  const setCurrentStep = (step: number) => {
    setState((prev) => ({ ...prev, step }));
  };

  const setDepartment = (department: string) => {
    setState((prev) => ({ ...prev, department }));
  };

  const setTerm = (term: string) => {
    setState((prev) => ({ ...prev, term }));
  };

  const setAcademicYear = (academicYear: string) => {
    setState((prev) => ({ ...prev, academicYear }));
  };

  const toggleCourseSelection = (courseId: string) => {
    setState((prev) => {
      const exists = prev.selectedCourseIds.includes(courseId);
      const next = exists
        ? prev.selectedCourseIds.filter((id) => id !== courseId)
        : [...prev.selectedCourseIds, courseId];
      return { ...prev, selectedCourseIds: next };
    });
  };

  const selectAllCourses = (select: boolean) => {
    setState((prev) => ({
      ...prev,
      selectedCourseIds: select ? courses.map((c) => c.course_id) : [],
    }));
  };

  const toggleGroupSelection = (groupId: string) => {
    setState((prev) => {
      const exists = prev.selectedGroupIds.includes(groupId);
      const next = exists
        ? prev.selectedGroupIds.filter((id) => id !== groupId)
        : [...prev.selectedGroupIds, groupId];
      return { ...prev, selectedGroupIds: next };
    });
  };

  const selectAllGroups = (select: boolean) => {
    setState((prev) => ({
      ...prev,
      selectedGroupIds: select ? studentGroups.map((g) => g.group_id) : [],
    }));
  };

  const toggleRoomSelection = (roomId: string) => {
    setState((prev) => {
      const exists = prev.selectedRoomIds.includes(roomId);
      const next = exists
        ? prev.selectedRoomIds.filter((id) => id !== roomId)
        : [...prev.selectedRoomIds, roomId];
      return { ...prev, selectedRoomIds: next };
    });
  };

  const selectAllRooms = (select: boolean) => {
    setState((prev) => ({
      ...prev,
      selectedRoomIds: select ? classrooms.map((r) => r.room_id) : [],
    }));
  };

  const setAlgorithm = (algorithm: AlgorithmChoice) => {
    setState((prev) => ({ ...prev, algorithm }));
  };

  const setGAParams = (params: Partial<GAParameters>) => {
    setState((prev) => ({ ...prev, gaParams: { ...prev.gaParams, ...params } }));
  };

  const setCSPParams = (params: Partial<CSPParameters>) => {
    setState((prev) => ({ ...prev, cspParams: { ...prev.cspParams, ...params } }));
  };

  const setSoftWeights = (weights: Partial<SoftObjectiveWeights>) => {
    setState((prev) => ({ ...prev, softWeights: { ...prev.softWeights, ...weights } }));
  };

  const saveDraftLocally = () => {
    try {
      const payload: WizardDraftState = {
        ...state,
        lastSavedAt: new Date().toLocaleTimeString(),
      };
      localStorage.setItem(WIZARD_STORAGE_KEY, JSON.stringify(payload));
      setHasSavedDraft(true);
      setState(payload);
    } catch {
      // LocalStorage error handling
    }
  };

  const loadSavedDraft = (): boolean => {
    try {
      const raw = localStorage.getItem(WIZARD_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        setState(parsed);
        return true;
      }
    } catch {
      // LocalStorage error handling
    }
    return false;
  };

  const resetDraft = () => {
    localStorage.removeItem(WIZARD_STORAGE_KEY);
    setHasSavedDraft(false);
    setState(getDefaultState());
  };

  const validateCurrentStep = (step: number): { isValid: boolean; error?: string } => {
    if (step === 1) {
      if (!state.department.trim()) return { isValid: false, error: "Academic department is required." };
      if (!state.term.trim()) return { isValid: false, error: "Academic semester term is required." };
    }
    if (step === 2) {
      if (state.selectedCourseIds.length === 0) {
        return { isValid: false, error: "At least one academic course must be selected for scheduling." };
      }
      if (state.selectedGroupIds.length === 0) {
        return { isValid: false, error: "At least one student cohort group must be selected." };
      }
      if (state.selectedRoomIds.length === 0) {
        return { isValid: false, error: "At least one classroom/laboratory facility must be selected." };
      }
    }
    if (step === 5) {
      if (state.algorithm === "GA") {
        if (state.gaParams.populationSize < 10) return { isValid: false, error: "Population size must be at least 10." };
        if (state.gaParams.maxGenerations < 5) return { isValid: false, error: "Maximum generations must be at least 5." };
      }
    }
    return { isValid: true };
  };

  return (
    <WizardContext.Provider
      value={{
        state,
        currentStep: state.step,
        setCurrentStep,
        setDepartment,
        setTerm,
        setAcademicYear,
        toggleCourseSelection,
        selectAllCourses,
        toggleGroupSelection,
        selectAllGroups,
        toggleRoomSelection,
        selectAllRooms,
        setAlgorithm,
        setGAParams,
        setCSPParams,
        setSoftWeights,
        saveDraftLocally,
        loadSavedDraft,
        hasSavedDraft,
        resetDraft,
        validateCurrentStep,
      }}
    >
      {children}
    </WizardContext.Provider>
  );
}

export function useWizard() {
  const ctx = useContext(WizardContext);
  if (!ctx) {
    throw new Error("useWizard must be used within a WizardProvider");
  }
  return ctx;
}
