import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import PrivateRoute from './components/PrivateRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import DataContractsList from './pages/DataContracts'
import DataContractDetail from './pages/DataContracts/DataContractDetail'
import NewDataContract from './pages/DataContracts/NewDataContract'
import DataProductsList from './pages/DataProducts'
import DataProductDetail from './pages/DataProducts/DataProductDetail'
import UsersList from './pages/Users'
import Profile from './pages/Profile'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<PrivateRoute />}>
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="data-contracts" element={<DataContractsList />} />
              <Route path="data-contracts/new" element={<NewDataContract />} />
              <Route path="data-contracts/:id" element={<DataContractDetail />} />
              <Route path="data-products" element={<DataProductsList />} />
              <Route path="data-products/:id" element={<DataProductDetail />} />
              <Route path="users" element={<UsersList />} />
              <Route path="profile" element={<Profile />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
