/**
 * RubricCategoryGrid Component
 * Reusable component for displaying rubric categories in a grid layout
 * Shows category weights, names, and descriptions similar to the overview page
 */

const RubricCategoryGrid = ({ 
  categories, 
  onCategoryClick = null,
  formatCategoryName,
  getCategoryWeight 
}) => {
  if (!categories || categories.length === 0) {
    return null
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {categories.map(([key, category]) => (
          <div 
            key={key} 
            className={`text-center p-3 rounded-lg bg-background/50 hover:bg-background/70 transition-colors ${
              onCategoryClick ? 'cursor-pointer' : ''
            }`}
            onClick={onCategoryClick ? onCategoryClick : undefined}
            title={onCategoryClick ? `Click to view details about ${formatCategoryName(key)}` : undefined}
          >
            <div className="text-lg font-bold">{getCategoryWeight(category)}%</div>
            <div className="text-xs text-muted-foreground font-medium mt-1">{formatCategoryName(key)}</div>
            {category.guidance && (
              <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                {category.guidance}
              </div>
            )}
          </div>
        ))}
      </div>
      {onCategoryClick && (
        <div className="text-xs text-muted-foreground text-center pt-2">
          Click any category to view full rubric details
        </div>
      )}
    </div>
  )
}

export default RubricCategoryGrid

