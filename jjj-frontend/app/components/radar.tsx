import React from 'react'

const Radar = () => {
  return (
    <>
  <div className="relative flex flex-col items-center justify-center p-6 bg-slate-900/50 backdrop-blur-md rounded-2xl border border-slate-800 shadow-2xl">
    {/* Concentric Radar Ping Rings */}
    <div className="relative flex items-center justify-center h-48 w-48">
      {/* Outer Pulse Ring */}
      <span className="absolute inline-flex h-full w-full animate-[ping_3s_infinite] rounded-full bg-emerald-500/10 opacity-40"></span>
      
      {/* Mid Pulse Ring */}
      <span className="absolute inline-flex h-32 w-32 animate-[ping_2s_infinite] rounded-full bg-emerald-400/20 opacity-60"></span>
      
      {/* Static Inner Glowing Ring */}
      <span className="absolute h-24 w-24 rounded-full border border-emerald-500/30 bg-emerald-900/20 shadow-[0_0_20px_rgba(16,185,129,0.2)] animate-pulse"></span>
      
      {/* Core Active Status Center */}
      <div className="relative flex flex-col items-center justify-center z-10 text-center">
        <span className="flex h-3 w-3 mb-2">
          <span className="absolute inline-flex h-3 w-3 animate-ping rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
        </span>
        <span className="text-xs font-mono tracking-widest text-emerald-400 uppercase font-bold">Radar</span>
        <span className="text-[10px] font-mono tracking-wider text-slate-400 font-medium">ACTIVE</span>
      </div>
    </div>
    
    {/* Quick UX Subtext to back up your Redis layer */}
    <div className="mt-2 text-center">
      <p className="text-xs text-slate-400 font-medium animate-pulse">
        Scanning civic boundaries...
      </p>
    </div>
  </div>
</>
  )
}

export default Radar
