import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from '../Badge';

describe('Badge', () => {
  it('renders badge with children', () => {
    render(<Badge variant="critical">Critical</Badge>);
    expect(screen.getByText('Critical')).toBeInTheDocument();
  });

  it('applies variant classes correctly', () => {
    const { rerender } = render(<Badge variant="critical">Critical</Badge>);
    expect(screen.getByText('Critical')).toHaveClass('bg-red/20');

    rerender(<Badge variant="high">High</Badge>);
    expect(screen.getByText('High')).toHaveClass('bg-peach/20');

    rerender(<Badge variant="medium">Medium</Badge>);
    expect(screen.getByText('Medium')).toHaveClass('bg-blue/20');

    rerender(<Badge variant="low">Low</Badge>);
    expect(screen.getByText('Low')).toHaveClass('bg-green/20');
  });
});
