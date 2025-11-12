import * as React from "react"
import * as ScrollAreaPrimitive from "@radix-ui/react-scroll-area"

import { cn } from "@/lib/utils"

function ScrollArea({
  className,
  children,
  ...props
}) {
  const rootRef = React.useRef(null)

  React.useEffect(() => {
    // Remove any corner elements that Radix might create
    const removeCorner = () => {
      if (rootRef.current) {
        const corner = rootRef.current.querySelector('[data-radix-scroll-area-corner]')
        if (corner) {
          corner.remove()
        }
        // Also check for any elements with the corner class or data attribute
        const corners = rootRef.current.querySelectorAll('[data-radix-scroll-area-corner], .scroll-area-corner')
        corners.forEach(el => el.remove())
      }
    }

    // Remove immediately and on any mutations
    removeCorner()
    
    const observer = new MutationObserver(() => {
      removeCorner()
    })

    if (rootRef.current) {
      observer.observe(rootRef.current, {
        childList: true,
        subtree: true
      })
    }

    return () => {
      observer.disconnect()
    }
  }, [])

  return (
    <ScrollAreaPrimitive.Root 
      ref={rootRef}
      data-slot="scroll-area" 
      className={cn("relative overflow-hidden flex flex-col", className)} 
      {...props}
    >
      <ScrollAreaPrimitive.Viewport
        data-slot="scroll-area-viewport"
        className="focus-visible:ring-ring/50 flex-1 min-h-0 w-full max-w-full box-border rounded-[inherit] transition-[color,box-shadow] outline-none focus-visible:ring-[3px] focus-visible:outline-1"
        style={{ overflowX: 'hidden', overflowY: 'auto', scrollbarGutter: 'stable both-edges' }}
      >
        {children}
      </ScrollAreaPrimitive.Viewport>
      <ScrollBar orientation="vertical" />
    </ScrollAreaPrimitive.Root>
  );
}

function ScrollBar({
  className,
  orientation = "vertical",
  ...props
}) {
  return (
    <ScrollAreaPrimitive.ScrollAreaScrollbar
      data-slot="scroll-area-scrollbar"
      orientation={orientation}
      className={cn(
        "flex touch-none p-px transition-colors select-none",
        orientation === "vertical" &&
          "h-full w-2.5 border-l border-l-transparent",
        orientation === "horizontal" &&
          "h-2.5 flex-col border-t border-t-transparent",
        className
      )}
      {...props}>
      <ScrollAreaPrimitive.ScrollAreaThumb
        data-slot="scroll-area-thumb"
        className="bg-border relative flex-1 rounded-full" />
    </ScrollAreaPrimitive.ScrollAreaScrollbar>
  );
}

export { ScrollArea, ScrollBar }
