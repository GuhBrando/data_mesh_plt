export interface QualityRule {
  dimension: 'completeness' | 'freshness' | 'uniqueness' | 'validity' | 'integrity'
  column: string
  operator: '>=' | '<=' | '='
  threshold: string
  description: string
}

export interface SchemaField {
  name: string
  type: 'string' | 'integer' | 'float' | 'boolean' | 'date' | 'timestamp'
  description: string
  nullable: boolean
  primary_key: boolean
}

export interface DataContract {
  id: string
  title: string
  version: string
  owner: string
  domain: string
  tier: 1 | 2 | 3 | 4
  status: 'draft' | 'in_review' | 'active' | 'deprecated'
  models: { fields: SchemaField[]; quality?: QualityRule[] }
  servicelevels: {
    freshness: string
    availability: string
    retention: string
    latency: string
  }
  created_at: string
  updated_at: string
}

export interface DataContractInput {
  title: string
  version: string
  owner: string
  domain: string
  tier: number
  status: string
  models: { fields: SchemaField[]; quality?: QualityRule[] }
  servicelevels: {
    freshness: string
    availability: string
    retention: string
    latency: string
  }
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
  description: string
  owner_id: string
  created_at: string
  updated_at: string
}

export interface DomainMember {
  user_id: string
  username: string
  role: 'maintainer' | 'member'
}

export interface DomainWithMembers extends Domain {
  owner_username: string
  members: DomainMember[]
  contract_count: number
}

export type DomainAccess = 'owner' | 'maintainer' | 'member' | 'none'

export interface DomainInput {
  name: string
  description: string
  owner_id: string
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
