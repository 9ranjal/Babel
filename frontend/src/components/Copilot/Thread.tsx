import React from 'react'

export function Thread({ children }: { children?: React.ReactNode }) {
  return <div className="p-4 space-y-3">{children || <div className="text-sm text-gray-500">No messages yet.</div>}</div>
}


