## UI Component Library Research for LoreGuard

### Executive Summary
For LoreGuard's three-pane layout with large data tables displaying thousands of artifacts, we need a component library that provides excellent performance, accessibility, and matches MAGE's design patterns. Based on research, **shadcn/ui with TanStack Table** emerges as the recommended solution.

### Component Library Comparison

#### shadcn/ui (Recommended)
**Strengths:**
- **Modern Architecture**: Built on Radix UI primitives with Tailwind CSS styling
- **Copy-Paste Components**: No package dependencies, full control over code
- **Accessibility**: WCAG AA compliant through Radix UI foundation
- **Customization**: Highly customizable with consistent design tokens
- **TypeScript Native**: Full TypeScript support with excellent type safety
- **Performance**: Lightweight, tree-shakeable components
- **Active Development**: Rapidly growing ecosystem with frequent updates
- **Dark/Light Mode**: Built-in theme switching capabilities

**Architecture:**
```typescript
// shadcn/ui component structure
import * as React from "react"
import { cn } from "@/lib/utils"

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link"
  size?: "default" | "sm" | "lg" | "icon"
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size }), className)}
        ref={ref}
        {...props}
      />
    )
  }
)
```

**For Large Tables:**
- Integrates seamlessly with TanStack Table for virtualization
- Custom table components with sorting, filtering, pagination
- Optimized for 10K+ row performance

#### Radix UI (Base Primitives)
**Strengths:**
- **Accessibility First**: Comprehensive ARIA support
- **Unstyled**: Complete styling control
- **Composable**: Build complex components from primitives
- **Keyboard Navigation**: Full keyboard support built-in
- **Focus Management**: Automatic focus handling

**Weaknesses:**
- **No Built-in Styling**: Requires significant CSS work
- **Steeper Learning Curve**: More complex implementation
- **Development Time**: Longer initial setup compared to pre-styled solutions

#### Alternative: Mantine
**Strengths:**
- **Complete System**: 100+ components with consistent design
- **Data Tables**: Built-in DataTable component with virtualization
- **Theming**: Comprehensive theming system
- **Hooks**: Extensive collection of utility hooks

**Weaknesses:**
- **Bundle Size**: Larger than shadcn/ui approach
- **Less Customizable**: More opinionated styling decisions
- **Migration Effort**: Different patterns from MAGE if already using other libraries

### Data Virtualization for Large Tables

#### TanStack Table (Recommended with shadcn/ui)
**Strengths:**
- **Headless**: Works with any UI library
- **Performance**: Built-in virtualization for millions of rows
- **Feature Rich**: Sorting, filtering, grouping, selection
- **TypeScript**: Full type safety
- **Extensible**: Plugin architecture for custom features

**Implementation Example:**
```typescript
// LoreGuard artifact table with shadcn/ui + TanStack Table
import { useReactTable, getCoreRowModel, getFilteredRowModel, getSortedRowModel } from '@tanstack/react-table'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface Artifact {
  id: string
  title: string
  source: string
  author: string
  date: string
  score: number
  label: 'Signal' | 'Noise' | 'Review'
  confidence: number
}

const ArtifactTable = ({ artifacts }: { artifacts: Artifact[] }) => {
  const [sorting, setSorting] = useState<SortingState>([])
  const [filtering, setFiltering] = useState('')

  const columns: ColumnDef<Artifact>[] = [
    {
      accessorKey: 'title',
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
        >
          Title <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => (
        <div className="max-w-[300px] truncate font-medium">
          {row.getValue('title')}
        </div>
      ),
    },
    {
      accessorKey: 'source',
      header: 'Source',
      filterFn: 'includesString',
    },
    {
      accessorKey: 'score',
      header: 'Score',
      cell: ({ row }) => {
        const score = parseFloat(row.getValue('score'))
        return (
          <div className="text-right">
            <Badge variant={score >= 4.0 ? 'default' : score >= 3.0 ? 'secondary' : 'destructive'}>
              {score.toFixed(1)}
            </Badge>
          </div>
        )
      },
    },
    {
      accessorKey: 'label',
      header: 'Label',
      cell: ({ row }) => {
        const label = row.getValue('label') as string
        return (
          <Badge variant={
            label === 'Signal' ? 'default' : 
            label === 'Review' ? 'secondary' : 
            'outline'
          }>
            {label}
          </Badge>
        )
      },
    },
  ]

  const table = useReactTable({
    data: artifacts,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: setSorting,
    onGlobalFilterChange: setFiltering,
    state: {
      sorting,
      globalFilter: filtering,
    },
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <Input
          placeholder="Search artifacts..."
          value={filtering}
          onChange={(e) => setFiltering(e.target.value)}
          className="max-w-sm"
        />
        <Button variant="outline" size="sm">
          <Filter className="h-4 w-4 mr-2" />
          Filters
        </Button>
      </div>
      
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder ? null : flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => onRowSelect(row.original)}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
```

#### Virtualization for Massive Datasets
```typescript
// Virtual scrolling for 100K+ rows
import { useVirtualizer } from '@tanstack/react-virtual'

const VirtualizedArtifactTable = ({ artifacts }: { artifacts: Artifact[] }) => {
  const parentRef = useRef<HTMLDivElement>(null)
  
  const rowVirtualizer = useVirtualizer({
    count: artifacts.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50, // Estimated row height
    overscan: 10, // Render extra rows for smooth scrolling
  })

  return (
    <div
      ref={parentRef}
      className="h-[600px] overflow-auto border rounded-md"
    >
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualItem) => {
          const artifact = artifacts[virtualItem.index]
          
          return (
            <div
              key={virtualItem.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
              className="flex items-center space-x-4 px-4 py-2 border-b hover:bg-muted/50"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{artifact.title}</p>
                <p className="text-sm text-muted-foreground">{artifact.source}</p>
              </div>
              <Badge variant={artifact.label === 'Signal' ? 'default' : 'secondary'}>
                {artifact.label}
              </Badge>
              <div className="text-sm text-muted-foreground">
                {artifact.score.toFixed(1)}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

### Three-Pane Layout Implementation

#### Layout Structure with shadcn/ui
```typescript
// LoreGuard three-pane layout
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"

const LoreGuardLayout = () => {
  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <div className="mr-4 flex">
            <a className="mr-6 flex items-center space-x-2">
              <span className="font-bold">LoreGuard</span>
            </a>
          </div>
          <div className="flex flex-1 items-center space-x-2">
            <Input
              type="search"
              placeholder="Search artifacts, sources, jobs..."
              className="md:w-[300px] lg:w-[400px]"
            />
          </div>
          <nav className="flex items-center space-x-2">
            <Button variant="ghost" size="sm">
              <Settings className="h-4 w-4" />
            </Button>
            <ThemeToggle />
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1">
        <ResizablePanelGroup direction="horizontal" className="h-full">
          {/* Side Navigation */}
          <ResizablePanel defaultSize={15} minSize={12} maxSize={25}>
            <div className="flex h-full flex-col">
              <div className="flex items-center justify-between p-4">
                <h2 className="text-lg font-semibold">Navigation</h2>
              </div>
              <Separator />
              <ScrollArea className="flex-1">
                <nav className="space-y-2 p-2">
                  <Button variant="ghost" className="w-full justify-start">
                    <Home className="mr-2 h-4 w-4" />
                    Dashboard
                  </Button>
                  <Button variant="ghost" className="w-full justify-start">
                    <Globe className="mr-2 h-4 w-4" />
                    Sources
                  </Button>
                  <Button variant="default" className="w-full justify-start">
                    <FileText className="mr-2 h-4 w-4" />
                    Artifacts
                  </Button>
                  <Button variant="ghost" className="w-full justify-start">
                    <Brain className="mr-2 h-4 w-4" />
                    Evaluation
                  </Button>
                  <Button variant="ghost" className="w-full justify-start">
                    <Library className="mr-2 h-4 w-4" />
                    Library
                  </Button>
                </nav>
              </ScrollArea>
            </div>
          </ResizablePanel>

          <ResizableHandle />

          {/* Content List */}
          <ResizablePanel defaultSize={50} minSize={30}>
            <div className="flex h-full flex-col">
              <div className="flex items-center justify-between p-4">
                <h2 className="text-lg font-semibold">Artifacts</h2>
                <div className="flex items-center space-x-2">
                  <Button variant="outline" size="sm">
                    <Filter className="h-4 w-4 mr-2" />
                    Filter
                  </Button>
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                </div>
              </div>
              <Separator />
              <div className="flex-1 p-4">
                <ArtifactTable artifacts={artifacts} />
              </div>
            </div>
          </ResizablePanel>

          <ResizableHandle />

          {/* Details Panel */}
          <ResizablePanel defaultSize={35} minSize={25}>
            <div className="flex h-full flex-col">
              <div className="flex items-center justify-between p-4">
                <h2 className="text-lg font-semibold">Details</h2>
                <Button variant="ghost" size="sm">
                  <MessageSquare className="h-4 w-4" />
                </Button>
              </div>
              <Separator />
              <ScrollArea className="flex-1">
                <ArtifactDetails artifact={selectedArtifact} />
              </ScrollArea>
              
              {/* Integrated Chatbot */}
              <Separator />
              <div className="p-4">
                <ChatInterface context={selectedArtifact} />
              </div>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </div>
  )
}
```

### Performance Considerations

#### Optimization Strategies
```typescript
// Performance optimizations for large datasets
import { memo, useMemo, useCallback } from 'react'

// Memoized table row component
const ArtifactRow = memo(({ artifact, onSelect }: { 
  artifact: Artifact
  onSelect: (artifact: Artifact) => void 
}) => {
  const handleClick = useCallback(() => {
    onSelect(artifact)
  }, [artifact, onSelect])

  return (
    <TableRow onClick={handleClick} className="cursor-pointer hover:bg-muted/50">
      <TableCell className="font-medium">{artifact.title}</TableCell>
      <TableCell>{artifact.source}</TableCell>
      <TableCell>
        <Badge variant={artifact.label === 'Signal' ? 'default' : 'secondary'}>
          {artifact.label}
        </Badge>
      </TableCell>
    </TableRow>
  )
})

// Optimized filtering and sorting
const useArtifactTable = (artifacts: Artifact[]) => {
  const [filters, setFilters] = useState<FilterState>({})
  const [sorting, setSorting] = useState<SortingState>([])

  const filteredAndSortedArtifacts = useMemo(() => {
    let result = artifacts

    // Apply filters
    if (filters.search) {
      result = result.filter(artifact => 
        artifact.title.toLowerCase().includes(filters.search.toLowerCase()) ||
        artifact.source.toLowerCase().includes(filters.search.toLowerCase())
      )
    }

    if (filters.label) {
      result = result.filter(artifact => artifact.label === filters.label)
    }

    // Apply sorting
    if (sorting.length > 0) {
      result = [...result].sort((a, b) => {
        const { id, desc } = sorting[0]
        const aValue = a[id as keyof Artifact]
        const bValue = b[id as keyof Artifact]
        
        if (aValue < bValue) return desc ? 1 : -1
        if (aValue > bValue) return desc ? -1 : 1
        return 0
      })
    }

    return result
  }, [artifacts, filters, sorting])

  return {
    artifacts: filteredAndSortedArtifacts,
    filters,
    setFilters,
    sorting,
    setSorting
  }
}
```

### Accessibility Features

#### WCAG AA Compliance
```typescript
// Accessible table with keyboard navigation
const AccessibleArtifactTable = ({ artifacts }: { artifacts: Artifact[] }) => {
  const [focusedRowIndex, setFocusedRowIndex] = useState(0)
  const tableRef = useRef<HTMLTableElement>(null)

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault()
        setFocusedRowIndex(prev => Math.min(prev + 1, artifacts.length - 1))
        break
      case 'ArrowUp':
        event.preventDefault()
        setFocusedRowIndex(prev => Math.max(prev - 1, 0))
        break
      case 'Enter':
      case ' ':
        event.preventDefault()
        onRowSelect(artifacts[focusedRowIndex])
        break
    }
  }, [artifacts, focusedRowIndex, onRowSelect])

  useEffect(() => {
    const tableElement = tableRef.current
    if (tableElement) {
      tableElement.addEventListener('keydown', handleKeyDown)
      return () => tableElement.removeEventListener('keydown', handleKeyDown)
    }
  }, [handleKeyDown])

  return (
    <Table ref={tableRef} tabIndex={0} className="focus:outline-none focus:ring-2 focus:ring-ring">
      <TableHeader>
        <TableRow>
          <TableHead>Title</TableHead>
          <TableHead>Source</TableHead>
          <TableHead>Label</TableHead>
          <TableHead>Score</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {artifacts.map((artifact, index) => (
          <TableRow
            key={artifact.id}
            className={cn(
              "cursor-pointer hover:bg-muted/50",
              index === focusedRowIndex && "bg-muted ring-2 ring-ring"
            )}
            onClick={() => onRowSelect(artifact)}
            role="button"
            tabIndex={-1}
            aria-selected={index === focusedRowIndex}
          >
            <TableCell className="font-medium">{artifact.title}</TableCell>
            <TableCell>{artifact.source}</TableCell>
            <TableCell>
              <Badge variant={artifact.label === 'Signal' ? 'default' : 'secondary'}>
                {artifact.label}
              </Badge>
            </TableCell>
            <TableCell>{artifact.score.toFixed(1)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
```

### Integration with MAGE Design System

#### Shared Design Tokens
```typescript
// Shared design tokens for consistency with MAGE
const designTokens = {
  colors: {
    primary: {
      50: '#eff6ff',
      500: '#3b82f6',
      900: '#1e3a8a'
    },
    semantic: {
      signal: '#10b981',   // Green for Signal documents
      review: '#f59e0b',   // Amber for Review required
      noise: '#6b7280'     // Gray for Noise
    }
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem'
  },
  typography: {
    fontFamily: {
      sans: ['Inter', 'system-ui', 'sans-serif'],
      mono: ['JetBrains Mono', 'monospace']
    }
  }
}

// Custom Badge component matching MAGE styling
const LoreGuardBadge = ({ variant, children }: {
  variant: 'signal' | 'review' | 'noise' | 'default'
  children: React.ReactNode
}) => {
  const variantStyles = {
    signal: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    review: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300',
    noise: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
    default: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
  }

  return (
    <span className={cn(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
      variantStyles[variant]
    )}>
      {children}
    </span>
  )
}
```

### Next Steps
1. **Implement shadcn/ui base setup** with theme configuration
2. **Build core table components** with TanStack Table integration
3. **Create three-pane layout** with resizable panels
4. **Implement virtualization** for large dataset performance
5. **Add accessibility features** and keyboard navigation

### Open Questions Resolved
- [x] **Primary UI Library**: shadcn/ui with Radix UI primitives
- [x] **Table Solution**: TanStack Table with virtualization
- [x] **Performance Strategy**: Virtual scrolling + memoization
- [x] **Accessibility**: WCAG AA compliance through Radix UI
- [x] **MAGE Integration**: Shared design tokens and consistent styling
