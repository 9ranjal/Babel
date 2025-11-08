import { create } from 'zustand'

type State = {
  docId?: string
  selectedClauseId?: string
  setDocId: (id?: string) => void
  setSelected: (id?: string) => void
  document?: any
  setDocument: (doc?: any) => void
  clauses: any[]
  setClauses: (clauses: any[]) => void
  analyses: Record<string, any>
  setAnalysis: (clauseId: string, a: any) => void
}

export const useDocStore = create<State>((set) => ({
  docId: undefined,
  selectedClauseId: undefined,
  setDocId: (id) => set({ docId: id }),
  setSelected: (id) => set({ selectedClauseId: id }),
  document: undefined,
  setDocument: (doc) => set({ document: doc }),
  clauses: [],
  setClauses: (clauses) => set({ clauses }),
  analyses: {},
  setAnalysis: (clauseId, a) => set((s) => ({ analyses: { ...s.analyses, [clauseId]: a } })),
}))


