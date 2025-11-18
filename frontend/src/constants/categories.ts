export const AGENT_CATEGORIES = [
  'general',
  'communication',
  'writing',
  'actuariat',
  'marketing',
  'back-office',
  'other'
] as const

export type AgentCategory = typeof AGENT_CATEGORIES[number]

export const CATEGORY_LABELS: Record<AgentCategory, string> = {
  'general': 'Général',
  'communication': 'Communication',
  'writing': 'Écriture',
  'actuariat': 'Actuariat',
  'marketing': 'Marketing',
  'back-office': 'Back-office',
  'other': 'Autre'
}