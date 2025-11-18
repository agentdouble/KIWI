import React from "react";
import { cn } from "@/lib/utils";

interface PulseButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  className?: string;
}

export const PulseButton = ({ children, className, disabled, ...props }: PulseButtonProps) => {
  return (
    <button 
      className={cn(
        "relative group inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all duration-300",
        disabled && "cursor-not-allowed",
        className
      )}
      disabled={disabled}
      {...props}
    >
      {/* Animated background glow */}
      <div className={cn(
        "absolute -inset-1 rounded-lg bg-gradient-to-r from-blue-600 via-violet-600 to-pink-600 opacity-70 blur transition duration-1000 group-hover:opacity-100 group-hover:duration-200 animate-gradient-xy",
        disabled && "opacity-30 group-hover:opacity-30"
      )} />
      
      {/* Static background for better contrast */}
      <div className="absolute -inset-0.5 rounded-lg bg-gradient-to-r from-blue-500 via-violet-500 to-pink-500 opacity-50 group-hover:opacity-75 transition duration-200" />
      
      {/* Button content */}
      <div className={cn(
        "relative flex items-center justify-center rounded-lg bg-gray-900 dark:bg-gray-950 px-8 py-3 transition-all duration-200",
        !disabled && "group-hover:bg-gray-800 dark:group-hover:bg-gray-900"
      )}>
        <span className={cn(
          "relative z-10 font-semibold",
          disabled ? "text-gray-500" : "text-white"
        )}>
          {children}
        </span>
        
        {/* Inner glow effect */}
        {!disabled && (
          <div className="absolute inset-0 rounded-lg opacity-0 transition-all duration-300 group-hover:opacity-100">
            <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-blue-400/20 via-violet-400/20 to-pink-400/20" />
          </div>
        )}
      </div>
      
      {/* Pulsing dots animation */}
      {!disabled && (
        <>
          <span className="absolute -top-1 -right-1 h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-violet-500"></span>
          </span>
        </>
      )}
    </button>
  );
};