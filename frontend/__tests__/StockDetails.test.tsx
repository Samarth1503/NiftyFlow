import { render, screen, waitFor } from '@testing-library/react';
import StockDetailsPage from '../src/app/stocks/[symbol]/page';
import api from '@/lib/api';

// Mock the next router
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
  useParams: () => ({ symbol: 'RELIANCE' })
}));

// Mock the API client
jest.mock('@/lib/api', () => ({
  get: jest.fn()
}));

const mockStockDetails = {
  id: 1,
  symbol: 'RELIANCE',
  name: 'Reliance Industries',
  exchange: 'NSE',
  current_price: 2500.0,
  previous_close: 2480.0,
  change: 20.0,
  change_percent: 0.8,
  open_price: 2490.0,
  high_price: 2510.0,
  low_price: 2480.0,
  volume: 1000000,
  avg_volume: 1200000,
  fifty_two_wk_low: 2000.0,
  eps: 80.5,
  last_updated: '2024-01-01T10:00:00Z',
  historical_1m: [
    { timestamp: '2024-01-01', price: 2400 },
    { timestamp: '2024-01-02', price: 2500 }
  ]
};

describe('StockDetailsPage Functionality', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('Shows loading state initially', () => {
    (api.get as jest.Mock).mockReturnValue(new Promise(() => {})); // Never resolves to keep it loading
    render(<StockDetailsPage />);
    expect(screen.getByText('Loading stock details...')).toBeInTheDocument();
  });

  test('Fetches correct stock based on URL symbol', async () => {
    (api.get as jest.Mock).mockImplementation((url) => {
      if (url.includes('/watchlist')) return Promise.resolve({ data: [] });
      if (url.includes('/history')) return Promise.resolve({ data: [] });
      return Promise.resolve({ data: mockStockDetails });
    });
    render(<StockDetailsPage />);
    
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/securities/symbol/RELIANCE');
    });
  });

  test('Displays stock details correctly', async () => {
    (api.get as jest.Mock).mockImplementation((url) => {
      if (url.includes('/watchlist')) return Promise.resolve({ data: [] });
      if (url.includes('/history')) return Promise.resolve({ data: [] });
      return Promise.resolve({ data: mockStockDetails });
    });
    render(<StockDetailsPage />);
    
    // Wait for the data to load and remove the loading spinner
    await waitFor(() => {
      expect(screen.queryByText('Loading stock details...')).not.toBeInTheDocument();
    });
    
    // Title & Name
    expect(screen.getByText('Reliance Industries')).toBeInTheDocument();
    expect(screen.getByText('RELIANCE:NSE')).toBeInTheDocument();
    
    // Prices
    expect(screen.getByText('₹2,500.00')).toBeInTheDocument();
    expect(screen.getByText('₹2,490.00')).toBeInTheDocument(); // Open price
    expect(screen.getByText('₹2,510.00')).toBeInTheDocument(); // High price
  });

  test('Shows 404 state when stock is not found', async () => {
    (api.get as jest.Mock).mockRejectedValue({ response: { status: 404 } });
    render(<StockDetailsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Stock Not Found')).toBeInTheDocument();
      expect(screen.getByText('Stock "RELIANCE" not found.')).toBeInTheDocument();
    });
  });

  test('Shows error state on API failure', async () => {
    (api.get as jest.Mock).mockRejectedValue({ response: { status: 500 } });
    render(<StockDetailsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to fetch stock details. Please try again later.')).toBeInTheDocument();
    });
  });
});
