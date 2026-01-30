interface BadgeProps {
  children: React.ReactNode;
  variant?: 'critical' | 'high' | 'medium' | 'low' | 'default';
  className?: string;
}

export function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  const variantStyles = {
    critical: 'bg-red/20 text-red border border-red/30',
    high: 'bg-peach/20 text-peach border border-peach/30',
    medium: 'bg-blue/20 text-blue border border-blue/30',
    low: 'bg-green/20 text-green border border-green/30',
    default: 'bg-surface-1 text-subtext-0 border border-surface-2',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variantStyles[variant]} ${className}`}>
      {children}
    </span>
  );
}
