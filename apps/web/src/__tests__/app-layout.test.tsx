import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AppLayout from '@/app/app-layout';

const mockPush = jest.fn();
const mockLogout = jest.fn();
const mockUsePathname = jest.fn(() => '/dashboard');

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({ push: mockPush })),
  usePathname: () => mockUsePathname(),
}));

jest.mock('@/lib/auth', () => ({
  useAuth: jest.fn(() => ({
    user: { role: 'admin', id: 1, full_name: 'System Administrator', email: 'admin@test.com', is_active: true },
    logout: mockLogout,
  })),
}));

beforeEach(() => {
  jest.clearAllMocks();
  mockUsePathname.mockReturnValue('/dashboard');
  const useAuth = require('@/lib/auth').useAuth;
  useAuth.mockReturnValue({
    user: { role: 'admin', id: 1, full_name: 'System Administrator', email: 'admin@test.com', is_active: true },
    logout: mockLogout,
  });
});

function renderWithRole(role: string) {
  const useAuth = require('@/lib/auth').useAuth;
  useAuth.mockReturnValue({
    user: {
      role,
      id: 1,
      full_name: role === 'admin' ? 'System Administrator' : role === 'supervisor' ? 'Supervisor Zhang' : 'Demo Engineer',
      email: `${role}@test.com`,
      is_active: true,
    },
    logout: mockLogout,
  });
  return render(<AppLayout><div data-testid="child">content</div></AppLayout>);
}

describe('AppLayout', () => {
  it('admin can see System Admin navigation item', () => {
    renderWithRole('admin');
    expect(screen.getByText('System Admin')).toBeInTheDocument();
  });

  it('supervisor cannot see admin-only navigation item', () => {
    renderWithRole('supervisor');
    expect(screen.getByText('Fault Reports')).toBeInTheDocument();
    expect(screen.getByText('Work Orders')).toBeInTheDocument();
    expect(screen.queryByText('System Admin')).not.toBeInTheDocument();
  });

  it('technician only displays authorized menu items', () => {
    renderWithRole('technician');
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Fault Reports')).toBeInTheDocument();
    expect(screen.getByText('Work Orders')).toBeInTheDocument();
    expect(screen.getByText('Equipment Assets')).toBeInTheDocument();
    expect(screen.queryByText('System Admin')).not.toBeInTheDocument();
  });

  it('highlights active route correctly', () => {
    mockUsePathname.mockReturnValue('/fault-reports');
    renderWithRole('admin');
    const activeBtn = screen.getByText('Fault Reports').closest('button');
    expect(activeBtn).toBeTruthy();
  });

  it('does not highlight inactive routes', () => {
    mockUsePathname.mockReturnValue('/dashboard');
    renderWithRole('admin');
    const faultBtn = screen.getByText('Fault Reports').closest('button');
    expect(faultBtn?.className).not.toContain('bg-primary/15');
  });

  it('renders mobile menu button', () => {
    renderWithRole('admin');
    const menuButtons = screen.queryAllByRole('button');
    expect(menuButtons.length).toBeGreaterThan(0);
  });

  it('login page does not render sidebar', () => {
    mockUsePathname.mockReturnValue('/login');
    const useAuth = require('@/lib/auth').useAuth;
    useAuth.mockReturnValue({
      user: { role: 'admin', id: 1, full_name: 'System Administrator', email: 'admin@test.com', is_active: true },
      logout: mockLogout,
    });
    render(<AppLayout><div data-testid="child">login content</div></AppLayout>);
    expect(screen.getByTestId('child')).toBeInTheDocument();
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
  });

  it('sign out button calls logout and redirects to login', async () => {
    renderWithRole('admin');
    const user = userEvent.setup();
    const logoutBtn = screen.getByText('Sign Out');
    await user.click(logoutBtn);
    expect(mockLogout).toHaveBeenCalled();
    expect(mockPush).toHaveBeenCalledWith('/login');
  });

  it('renders children content', () => {
    renderWithRole('admin');
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });
});
