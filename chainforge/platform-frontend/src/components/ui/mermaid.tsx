"use client";

import React, { useEffect, useRef, useState, useId } from "react";
import { useTheme } from "next-themes";

// We will import mermaid dynamically inside the effects 
// to avoid bloating the initial compilation of other pages.

interface MermaidProps {
  chart: string;
  id?: string;
  className?: string;
}

const Mermaid: React.FC<MermaidProps> = ({ chart, id = "mermaid-diagram", className }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>("");
  const { theme, resolvedTheme } = useTheme();
  const [isLoaded, setIsLoaded] = useState(false);
  const reactId = useId();

  useEffect(() => {
    const initMermaid = async () => {
      const mermaid = (await import("mermaid")).default;
      const currentTheme = resolvedTheme || theme || "dark";
      
      mermaid.initialize({
        startOnLoad: false,
        theme: currentTheme === "dark" ? "dark" : "default",
        securityLevel: "loose",
        fontFamily: "Inter, sans-serif",
        flowchart: {
          useMaxWidth: false,
          htmlLabels: true,
          curve: "basis",
        },
      });
      
      setIsLoaded(true);
    };

    initMermaid();
  }, [theme, resolvedTheme]);

  useEffect(() => {
    if (!isLoaded || !chart) return;

    const renderDiagram = async () => {
      try {
        const mermaid = (await import("mermaid")).default;
        const uniqueId = `mermaid-${reactId.replace(/:/g, "")}`;
        const { svg: renderedSvg } = await mermaid.render(uniqueId, chart);
        setSvg(renderedSvg);
      } catch (error) {
        console.error("Mermaid rendering failed:", error);
      }
    };

    renderDiagram();
  }, [chart, isLoaded, reactId]);

  return (
    <div 
      ref={containerRef} 
      className={`flex justify-center items-center w-full min-h-[300px] overflow-x-auto ${className || ""}`}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
};

export default Mermaid;
