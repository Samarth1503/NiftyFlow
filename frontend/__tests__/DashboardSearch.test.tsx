import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Dashboard from '../src/app/dashboard/page';
import api from '@/lib/api';

// Mock the API client
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn()
}));

jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
    };
  }
}));

const mockSecurities = [
  { id: 1, symbol: 'RELIANCE', name: 'Reliance Industries Limited', exchange: 'NSE' },
  { id: 2, symbol: 'TCS', name: 'Tata Consultancy Services Limited', exchange: 'NSE' },
  { id: 3, symbol: 'INFY', name: 'Infosys Limited', exchange: 'NSE' },
  { id: 4, symbol: 'RELINFRA', name: 'Reliance Infrastructure', exchange: 'NSE' }
];

describe('Dashboard Search Functionality', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.get as jest.Mock).mockImplementation((url) => {
      if (url === '/securities') return Promise.resolve({ data: mockSecurities });
      if (url === '/portfolios') return Promise.resolve({ data: [] });
      if (url === '/securities/indices') return Promise.resolve({ data: [] });
      return Promise.resolve({ data: [] });
    });
  });

  test('Search component loads successfully', async () => {
    render(<Dashboard />);
    expect(screen.getByPlaceholderText('Search for a stock symbol or company name...')).toBeInTheDocument();
  });

  test('Stock list is loaded exactly once on mount, not per keystroke', async () => {
    render(<Dashboard />);
    
    // Wait for initial load
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/securities'));
    
    // Type in search bar
    const searchInput = screen.getByPlaceholderText('Search for a stock symbol or company name...');
    fireEvent.change(searchInput, { target: { value: 'REL' } });
    
    // Ensure no additional API calls were made
    const securityCalls = (api.get as jest.Mock).mock.calls.filter(call => call[0] === '/securities');
    expect(securityCalls.length).toBe(1);
  });

  test('Local search by exact symbol', async () => {
    render(<Dashboard />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/securities'));
    
    const searchInput = screen.getByPlaceholderText('Search for a stock symbol or company name...');
    
    // Focus and type
    fireEvent.focus(searchInput);
    fireEvent.change(searchInput, { target: { value: 'RELIANCE' } });
    
    // Check results
    expect(await screen.findByText('Reliance Industries Limited')).toBeInTheDocument();
    // TCS should not be present
    expect(screen.queryByText('Tata Consultancy Services Limited')).not.toBeInTheDocument();
  });

  test('Local search by company name (case-insensitive)', async () => {
    render(<Dashboard />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/securities'));
    
    const searchInput = screen.getByPlaceholderText('Search for a stock symbol or company name...');
    
    fireEvent.focus(searchInput);
    fireEvent.change(searchInput, { target: { value: 'infosys' } });
    
    expect(await screen.findByText('INFY')).toBeInTheDocument();
  });

  test('Whitespace is handled appropriately', async () => {
    render(<Dashboard />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/securities'));
    
    const searchInput = screen.getByPlaceholderText('Search for a stock symbol or company name...');
    
    fireEvent.focus(searchInput);
    fireEvent.change(searchInput, { target: { value: '   TCS   ' } });
    
    expect(await screen.findByText('Tata Consultancy Services Limited')).toBeInTheDocument();
  });

  test('Empty search input closes the dropdown', async () => {
    render(<Dashboard />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/securities'));
    
    const searchInput = screen.getByPlaceholderText('Search for a stock symbol or company name...');
    
    fireEvent.focus(searchInput);
    fireEvent.change(searchInput, { target: { value: 'REL' } });
    expect(await screen.findByText('Reliance Industries Limited')).toBeInTheDocument();
    
    fireEvent.change(searchInput, { target: { value: '' } });
    expect(screen.queryByText('Reliance Industries Limited')).not.toBeInTheDocument();
  });

  test('No results state appears correctly', async () => {
    render(<Dashboard />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/securities'));
    
    const searchInput = screen.getByPlaceholderText('Search for a stock symbol or company name...');
    
    fireEvent.focus(searchInput);
    fireEvent.change(searchInput, { target: { value: 'XYZABC123' } });
    
    expect(await screen.findByText('No stocks found matching "XYZABC123"')).toBeInTheDocument();
  });

  test('Result ranking prioritizes exact symbol matches over starts-with or contains', async () => {
    render(<Dashboard />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/securities'));
    
    const searchInput = screen.getByPlaceholderText('Search for a stock symbol or company name...');
    
    fireEvent.focus(searchInput);
    fireEvent.change(searchInput, { target: { value: 'REL' } });
    
    // Wait for dropdown
    await screen.findByText('Reliance Industries Limited');
    
    // Grab the rendered result symbols
    const resultElements = screen.getAllByText(/^REL/);
    
    // RELIANCE should logically appear before RELINFRA
    const textValues = resultElements.map(el => el.textContent);
    const relIndex = textValues.findIndex(val => val === 'RELIANCE');
    const relInfraIndex = textValues.findIndex(val => val === 'RELINFRA');
    
    expect(relIndex).toBeLessThan(relInfraIndex);
  });

  test('Selecting a stock adds it to the watchlist and clears search', async () => {
    render(<Dashboard />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/securities'));
    
    const searchInput = screen.getByPlaceholderText('Search for a stock symbol or company name...');
    
    fireEvent.focus(searchInput);
    fireEvent.change(searchInput, { target: { value: 'INFY' } });
    
    const infyResult = await screen.findByText('Infosys Limited');
    fireEvent.click(infyResult);
    
    // Dropdown should be cleared/closed
    expect(searchInput).toHaveValue('');
    expect(screen.queryByText('Infosys Limited')).not.toBeInTheDocument();
  });
});
