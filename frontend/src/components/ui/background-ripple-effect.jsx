"use client";
import React, { useMemo, useRef, useState, useEffect } from "react";
import { cn } from "@/lib/utils";

export const BackgroundRippleEffect = ({
  cellSize = 56
}) => {
  const [clickedCell, setClickedCell] = useState(null);
  const [rippleKey, setRippleKey] = useState(0);
  const ref = useRef(null);
  const [gridSize, setGridSize] = useState({ rows: 0, cols: 0 });

  useEffect(() => {
    const updateSize = () => {
      if (ref.current) {
        const width = window.innerWidth;
        const height = window.innerHeight;
        setGridSize({
          rows: Math.ceil(height / cellSize) + 1,
          cols: Math.ceil(width / cellSize) + 1,
        });
      }
    };
    updateSize();
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, [cellSize]);

  return (
    <div
      ref={ref}
      className="fixed inset-0 h-full w-full z-0 pointer-events-none"
    >
      {/* 1. Custom CSS Keyframes for the Smooth Breathing Effect */}
      <style>{`
        @keyframes cell-breathe {
          0%, 100% {
            border-color: rgba(30, 41, 59, 0.4);
            box-shadow: none;
            background-color: transparent;
          }
          50% {
            border-color: rgba(16, 185, 129, 0.8); /* emerald-500 */
            box-shadow: 0 0 16px rgba(16, 185, 129, 0.6);
            background-color: rgba(16, 185, 129, 0.1);
          }
        }
        .breathe-active {
          /* 6s duration makes it a very slow, relaxing fade-in and out */
          animation: cell-breathe 6s ease-in-out forwards !important;
          z-index: 5 !important;
        }
      `}</style>

      <div 
        className="relative h-full w-full overflow-hidden pointer-events-auto"
        style={{
          maskImage: "linear-gradient(to bottom, white 0%, white 80%, transparent 100%)",
          WebkitMaskImage: "linear-gradient(to bottom, white 0%, white 80%, transparent 100%)"
        }}
      >
        {gridSize.rows > 0 && (
          <DivGrid
            key={`base-${rippleKey}`}
            rows={gridSize.rows}
            cols={gridSize.cols}
            cellSize={cellSize}
            clickedCell={clickedCell}
            onCellClick={(row, col) => {
              setClickedCell({ row, col });
              setRippleKey((k) => k + 1);
            }}
            interactive 
          />
        )}
      </div>
    </div>
  );
};

const DivGrid = ({
  className,
  rows,
  cols,
  cellSize,
  clickedCell = null,
  onCellClick = () => {},
  interactive = true
}) => {
  const cells = useMemo(() => Array.from({ length: rows * cols }, (_, idx) => idx), [rows, cols]);

  // 2. The Random Breathing Engine
  useEffect(() => {
    if (!interactive || rows === 0 || cols === 0) return;

    const breatheEngine = setInterval(() => {
      // Pick 2 to 5 random cells to breathe at the same time
      const numCells = Math.floor(Math.random() * 4) + 2;

      for (let i = 0; i < numCells; i++) {
        const r = Math.floor(Math.random() * rows);
        const c = Math.floor(Math.random() * cols);
        const cell = document.getElementById(`grid-cell-${r}-${c}`);

        // Only trigger if the cell exists and isn't already breathing
        if (cell && !cell.classList.contains("breathe-active")) {
          cell.classList.add("breathe-active");
          
          // Remove the class after 6 seconds (when the CSS animation finishes)
          // This resets the cell so it can be picked again later
          setTimeout(() => {
            if (cell) cell.classList.remove("breathe-active");
          }, 6000); 
        }
      }
    }, 800); // Run this selector engine every 0.8 seconds

    return () => clearInterval(breatheEngine);
  }, [rows, cols, interactive]);

  const gridStyle = {
    display: "grid",
    gridTemplateColumns: `repeat(${cols}, ${cellSize}px)`,
    gridTemplateRows: `repeat(${rows}, ${cellSize}px)`,
    width: cols * cellSize,
    height: rows * cellSize,
    marginInline: "auto",
  };

  return (
    <div className={cn("relative z-0", className)} style={gridStyle}>
      {cells.map((idx) => {
        const rowIdx = Math.floor(idx / cols);
        const colIdx = idx % cols;
        const distance = clickedCell
          ? Math.hypot(clickedCell.row - rowIdx, clickedCell.col - colIdx)
          : 0;
        const delay = clickedCell ? Math.max(0, distance * 55) : 0;
        const duration = 200 + distance * 80;

        const style = clickedCell
          ? {
              "--delay": `${delay}ms`,
              "--duration": `${duration}ms`,
            }
          : {};

        return (
          <div
            key={idx}
            id={`grid-cell-${rowIdx}-${colIdx}`} 
            className={cn(
              "cell relative border border-slate-800/40 transition-all duration-300",
              "hover:border-emerald-500 hover:shadow-[0_0_12px_rgba(16,185,129,0.8)] hover:bg-emerald-500/20 hover:z-10",
              clickedCell && "animate-cell-ripple [animation-fill-mode:none]",
              !interactive && "pointer-events-none"
            )}
            style={{
              backgroundColor: "transparent",
              ...style,
            }}
            onClick={
              interactive ? () => onCellClick?.(rowIdx, colIdx) : undefined
            } 
          />
        );
      })}
    </div>
  );
};





















// "use client";
// import React, { useMemo, useRef, useState, useEffect } from "react";
// import { cn } from "@/lib/utils";

// export const BackgroundRippleEffect = ({
//   cellSize = 56
// }) => {
//   const [clickedCell, setClickedCell] = useState(null);
//   const [rippleKey, setRippleKey] = useState(0);
//   const ref = useRef(null);

//   // Dynamically calculate grid size to perfectly fit any screen resolution
//   const [gridSize, setGridSize] = useState({ rows: 0, cols: 0 });

//   useEffect(() => {
//     const updateSize = () => {
//       if (ref.current) {
//         const width = window.innerWidth;
//         const height = window.innerHeight;
//         setGridSize({
//           rows: Math.ceil(height / cellSize) + 1,
//           cols: Math.ceil(width / cellSize) + 1,
//         });
//       }
//     };
//     updateSize(); // Run once on mount
//     window.addEventListener("resize", updateSize); // Update if user resizes window
//     return () => window.removeEventListener("resize", updateSize);
//   }, [cellSize]);

//   return (
//     <div
//       ref={ref}
//       // "fixed" keeps it pinned to the screen background even while scrolling
//       className="fixed inset-0 h-full w-full z-0 pointer-events-none"
//     >
//       <div 
//         className="relative h-full w-full overflow-hidden pointer-events-auto"
//         // This is the magic CSS that makes the grid smoothly vanish into the dark bg at the bottom
//         style={{
//           maskImage: "linear-gradient(to bottom, white 0%, white 80%, transparent 100%)",
//           WebkitMaskImage: "linear-gradient(to bottom, white 0%, white 80%, transparent 100%)"
//         }}
//       >
//         {/* Only render grid once we know the screen dimensions */}
//         {gridSize.rows > 0 && (
//           <DivGrid
//             key={`base-${rippleKey}`}
//             rows={gridSize.rows}
//             cols={gridSize.cols}
//             cellSize={cellSize}
//             clickedCell={clickedCell}
//             onCellClick={(row, col) => {
//               setClickedCell({ row, col });
//               setRippleKey((k) => k + 1);
//             }}
//             interactive 
//           />
//         )}
//       </div>
//     </div>
//   );
// };

// const DivGrid = ({
//   className,
//   rows,
//   cols,
//   cellSize,
//   clickedCell = null,
//   onCellClick = () => {},
//   interactive = true
// }) => {
//   const cells = useMemo(() => Array.from({ length: rows * cols }, (_, idx) => idx), [rows, cols]);

//   const gridStyle = {
//     display: "grid",
//     gridTemplateColumns: `repeat(${cols}, ${cellSize}px)`,
//     gridTemplateRows: `repeat(${rows}, ${cellSize}px)`,
//     width: cols * cellSize,
//     height: rows * cellSize,
//     marginInline: "auto",
//   };

//   return (
//     <div className={cn("relative z-0", className)} style={gridStyle}>
//       {cells.map((idx) => {
//         const rowIdx = Math.floor(idx / cols);
//         const colIdx = idx % cols;
//         const distance = clickedCell
//           ? Math.hypot(clickedCell.row - rowIdx, clickedCell.col - colIdx)
//           : 0;
//         const delay = clickedCell ? Math.max(0, distance * 55) : 0; // ms
//         const duration = 200 + distance * 80; // ms

//         const style = clickedCell
//           ? {
//               "--delay": `${delay}ms`,
//               "--duration": `${duration}ms`,
//             }
//           : {};

//         return (
//           <div
//             key={idx}
//             className={cn(
//               "cell relative border border-slate-800/40 transition-all duration-300",
//               // HOVER GLOW MAGIC: Lights up the border green and drops a green shadow, no background fill
//               "hover:border-emerald-500 hover:shadow-[0_0_12px_rgba(16,185,129,0.8)] hover:z-10",
//               clickedCell && "animate-cell-ripple [animation-fill-mode:none]",
//               !interactive && "pointer-events-none"
//             )}
//             style={{
//               // backgroundColor: "transparent", // Ensures the middle stays dark
//               ...style,
//             }}
//             onClick={
//               interactive ? () => onCellClick?.(rowIdx, colIdx) : undefined
//             } 
//           />
//         );
//       })}
//     </div>
//   );
// };