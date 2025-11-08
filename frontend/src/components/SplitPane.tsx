import React from 'react'

export function SplitPane({ left, right }: { left: React.ReactNode; right: React.ReactNode }) {
  return (
    <div className="grid grid-cols-2 h-full">
      <div className="border-r overflow-auto">{left}</div>
      <div className="overflow-auto">{right}</div>
    </div>
  )
}


