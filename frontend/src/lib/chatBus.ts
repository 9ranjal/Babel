import { create } from 'zustand'

export type ChatRole = 'user' | 'assistant' | 'system'
export type ChatInjection = { role: ChatRole; content: string }

type ChatBusState = {
  listeners: Set<(msg: ChatInjection) => void>
  subscribe: (fn: (msg: ChatInjection) => void) => () => void
  emit: (msg: ChatInjection) => void
}

export const useChatBus = create<ChatBusState>((set, get) => ({
  listeners: new Set(),
  subscribe: (fn) => {
    const { listeners } = get()
    listeners.add(fn)
    return () => {
      const { listeners: ls } = get()
      ls.delete(fn)
    }
  },
  emit: (msg) => {
    const { listeners } = get()
    listeners.forEach((fn) => {
      try {
        fn(msg)
      } catch {
        // ignore listener errors
      }
    })
  },
}))

export function enqueueUserMessage(content: string) {
  useChatBus.getState().emit({ role: 'user', content })
}

export function enqueueAssistantMessage(content: string) {
  useChatBus.getState().emit({ role: 'assistant', content })
}

export function enqueueSystemMessage(content: string) {
  useChatBus.getState().emit({ role: 'system', content })
}







