import { create } from 'zustand';

type DocumentState = {
  docId?: string;
  document?: any;
  clauses: any[];
  analyses: Record<string, any>;
  selectedClauseId?: string;
  isUploading: boolean;
  setDocId: (id?: string) => void;
  setDocument: (doc?: any) => void;
  setClauses: (clauses: any[]) => void;
  setAnalysis: (clauseId: string, analysis: any) => void;
  clearAnalyses: () => void;
  setSelected: (id?: string) => void;
  setIsUploading: (uploading: boolean) => void;
  reset: () => void;
};

const defaultState = {
  docId: undefined,
  document: undefined,
  clauses: [] as any[],
  analyses: {} as Record<string, any>,
  selectedClauseId: undefined,
  isUploading: false,
};

export const useDocStore = create<DocumentState>((set) => ({
  ...defaultState,
  setDocId: (docId) => set({ docId }),
  setDocument: (document) => set({ document }),
  setClauses: (clauses) => set({ clauses }),
  setAnalysis: (clauseId, analysis) =>
    set((state) => ({ analyses: { ...state.analyses, [clauseId]: analysis } })),
  clearAnalyses: () => set({ analyses: {} }),
  setSelected: (selectedClauseId) => set({ selectedClauseId }),
  setIsUploading: (isUploading) => set({ isUploading }),
  reset: () => set({ ...defaultState }),
}));


