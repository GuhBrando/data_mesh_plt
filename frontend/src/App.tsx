import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import DataContractsList from './pages/DataContracts'
import DataContractDetail from './pages/DataContracts/DataContractDetail'
import DataProductsList from './pages/DataProducts'
import DataProductDetail from './pages/DataProducts/DataProductDetail'
import UsersList from './pages/Users'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="data-contracts" element={<DataContractsList />} />
          <Route path="data-contracts/:id" element={<DataContractDetail />} />
          <Route path="data-products" element={<DataProductsList />} />
          <Route path="data-products/:id" element={<DataProductDetail />} />
          <Route path="users" element={<UsersList />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
