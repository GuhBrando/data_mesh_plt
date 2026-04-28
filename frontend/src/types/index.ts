export interface DataContract {
  id: string
  obj: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface DataProduct {
  id: string
  name: string
  description: string
  data_contracts_id: string
  created_at: string
  updated_at: string
}

export interface User {
  id: string
  username: string
  email: string
  role: string
}

export interface Domain {
  id: string
  name: string
}

// ---- Form input types ----

export interface DataContractFormData {
  obj: string // raw JSON textarea, parsed on submit
}

export interface DataProductFormData {
  name: string
  description: string
  data_contracts_id: string
}

export interface UserFormData {
  username: string
  email: string
}
