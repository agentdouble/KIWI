import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface AnimatedCreateButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  className?: string;
}

export const AnimatedCreateButton = ({ children, className, disabled, ...props }: AnimatedCreateButtonProps) => {
  // Beams configuration centered around button
  const beams = [
    {
      path: "M80 50H30C24.4772 50 20 54.4772 20 60V90",
      gradientConfig: {
        initial: { x1: "0%", x2: "0%", y1: "80%", y2: "100%" },
        animate: {
          x1: ["0%", "0%", "200%"],
          x2: ["0%", "0%", "180%"],
          y1: ["80%", "0%", "0%"],
          y2: ["100%", "20%", "20%"],
        },
        transition: {
          duration: 2,
          repeat: Infinity,
          repeatType: "loop" as const,
          ease: "linear",
          repeatDelay: 2,
          delay: 0,
        },
      },
      connectionPoints: [
        { cx: 20, cy: 90, r: 3 },
        { cx: 80, cy: 50, r: 3 }
      ]
    },
    {
      path: "M170 50H220C225.523 50 230 45.5228 230 40V20",
      gradientConfig: {
        initial: { x1: "0%", x2: "0%", y1: "80%", y2: "100%" },
        animate: {
          x1: ["20%", "100%", "100%"],
          x2: ["0%", "90%", "90%"],
          y1: ["80%", "80%", "-20%"],
          y2: ["100%", "100%", "0%"],
        },
        transition: {
          duration: 2,
          repeat: Infinity,
          repeatType: "loop" as const,
          ease: "linear",
          repeatDelay: 2,
          delay: 0.5,
        },
      },
      connectionPoints: [
        { cx: 230, cy: 20, r: 3 },
        { cx: 170, cy: 50, r: 3 }
      ]
    },
    {
      path: "M125 75V90C125 95.5228 120.523 100 115 100H60C54.4772 100 50 104.477 50 110V125",
      gradientConfig: {
        initial: { x1: "0%", x2: "0%", y1: "80%", y2: "100%" },
        animate: {
          x1: ["20%", "100%", "100%"],
          x2: ["0%", "90%", "90%"],
          y1: ["80%", "80%", "-20%"],
          y2: ["100%", "100%", "0%"],
        },
        transition: {
          duration: 2,
          repeat: Infinity,
          repeatType: "loop" as const,
          ease: "linear",
          repeatDelay: 2,
          delay: 1,
        },
      },
      connectionPoints: [
        { cx: 50, cy: 125, r: 3 },
        { cx: 125, cy: 75, r: 3 }
      ]
    },
    {
      path: "M125 75V90C125 95.5228 129.477 100 135 100H190C195.523 100 200 104.477 200 110V125",
      gradientConfig: {
        initial: { x1: "40%", x2: "50%", y1: "160%", y2: "180%" },
        animate: {
          x1: "0%",
          x2: "10%",
          y1: "-40%",
          y2: "-20%",
        },
        transition: {
          duration: 2,
          repeat: Infinity,
          repeatType: "loop" as const,
          ease: "linear",
          repeatDelay: 2,
          delay: 1.5,
        },
      },
      connectionPoints: [
        { cx: 200, cy: 125, r: 3 },
        { cx: 125, cy: 75, r: 3 }
      ]
    }
  ];

  // Colors: always grayscale like on home page
  const gradientColors = {
    start: "#9CA3AF",  // gray-400
    middle: "#6B7280", // gray-500
    end: "#4B5563"     // gray-600
  };

  return (
    <div className="relative inline-flex items-center justify-center">
      {/* SVG Beams - positioned behind button */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <svg
          width="250"
          height="150"
          viewBox="0 0 250 150"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="absolute"
          style={{ left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}
        >
            {beams.map((beam, index) => (
              <React.Fragment key={index}>
                <path
                  d={beam.path}
                  stroke="#E5E7EB"
                  strokeWidth="1"
                  opacity="0.2"
                />
                <path
                  d={beam.path}
                  stroke={`url(#grad${index})`}
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  opacity={disabled ? "0.3" : "0.8"}
                />
              </React.Fragment>
            ))}

            <defs>
              {beams.map((beam, index) => (
                <motion.linearGradient
                  key={index}
                  id={`grad${index}`}
                  gradientUnits="userSpaceOnUse"
                  initial={beam.gradientConfig.initial}
                  animate={beam.gradientConfig.animate}
                  transition={beam.gradientConfig.transition}
                >
                  <stop offset="0%" stopColor={gradientColors.start} stopOpacity="0" />
                  <stop offset="20%" stopColor={gradientColors.start} stopOpacity="1" />
                  <stop offset="50%" stopColor={gradientColors.middle} stopOpacity="1" />
                  <stop offset="100%" stopColor={gradientColors.end} stopOpacity="0" />
                </motion.linearGradient>
              ))}
            </defs>
          </svg>
      </div>

      {/* Button */}
      <button 
        className={cn(
          "relative z-10 px-8 py-3 rounded-lg font-medium text-sm transition-all duration-200",
          disabled 
            ? "bg-gray-200 dark:bg-gray-800 text-gray-500 dark:text-gray-400 cursor-not-allowed" 
            : "bg-gray-900 dark:bg-gray-950 text-white hover:bg-gray-800 dark:hover:bg-gray-900 cursor-pointer group",
          className
        )}
        disabled={disabled}
        {...props}
      >
        {/* Subtle glow effect on hover - grayscale */}
        {!disabled && (
          <span className="absolute inset-0 overflow-hidden rounded-lg">
            <span className="absolute inset-0 rounded-lg bg-[image:radial-gradient(75%_100%_at_50%_0%,rgba(156,163,175,0.2)_0%,rgba(156,163,175,0)_75%)] opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
          </span>
        )}
        
        <span className="relative z-10">
          {children}
        </span>
      </button>
    </div>
  );
};