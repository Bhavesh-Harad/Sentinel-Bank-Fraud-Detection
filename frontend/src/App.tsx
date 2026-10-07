import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import ErrorBoundary from './components/ErrorBoundary';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import LiveAnalyzer from './pages/LiveAnalyzer';
import Transactions from './pages/Transactions';
import TransactionDetail from './pages/TransactionDetail';
import Customers from './pages/Customers';
import CustomerProfile from './pages/CustomerProfile';
import FraudAlerts from './pages/FraudAlerts';
import BehaviorAnalytics from './pages/BehaviorAnalytics';
import GeospatialAnalysis from './pages/GeospatialAnalysis';
import ModelMonitoring from './pages/ModelMonitoring';
import Reports from './pages/Reports';

// Wrap each page in its own ErrorBoundary so one page crash
// never takes down the entire app or leaves a black screen
function SafePage({ children }: { children: React.ReactNode }) {
  return <ErrorBoundary>{children}</ErrorBoundary>
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />

        {/* All protected pages wrapped in Layout + individual ErrorBoundaries */}
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard"    element={<SafePage><Dashboard /></SafePage>} />
          <Route path="live-analyzer" element={<SafePage><LiveAnalyzer /></SafePage>} />
          <Route path="transactions" element={<SafePage><Transactions /></SafePage>} />
          <Route path="transactions/:id" element={<SafePage><TransactionDetail /></SafePage>} />
          <Route path="customers"    element={<SafePage><Customers /></SafePage>} />
          <Route path="customers/:id" element={<SafePage><CustomerProfile /></SafePage>} />
          <Route path="alerts"       element={<SafePage><FraudAlerts /></SafePage>} />
          <Route path="behavior"     element={<SafePage><BehaviorAnalytics /></SafePage>} />
          <Route path="geospatial"   element={<SafePage><GeospatialAnalysis /></SafePage>} />
          <Route path="model"        element={<SafePage><ModelMonitoring /></SafePage>} />
          <Route path="reports"      element={<SafePage><Reports /></SafePage>} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
