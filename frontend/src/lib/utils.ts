// ============================================
// UTILITIES
// ============================================

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge Tailwind CSS classes with proper precedence
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format date to localized string
 */
export function formatDate(date: Date, locale: string = 'pt-PT'): string {
  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date);
}

/**
 * Format currency with proper symbol
 */
export function formatCurrency(value: number, currency: string = 'USD', locale: string = 'pt-PT'): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Format number with locale
 */
export function formatNumber(value: number, locale: string = 'pt-PT'): string {
  return new Intl.NumberFormat(locale).format(value);
}

/**
 * Calculate days until deadline
 */
export function getDaysUntil(date: Date): number {
  const now = new Date();
  const diff = date.getTime() - now.getTime();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

/**
 * Get status color for badges
 */
export function getStatusColor(status: string): string {
  const statusColors: Record<string, string> = {
    // Opportunity statuses
    new: 'bg-blue-100 text-blue-800 border-blue-200',
    analyzing: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    go: 'bg-green-100 text-green-800 border-green-200',
    no_go: 'bg-red-100 text-red-800 border-red-200',
    proposal_draft: 'bg-purple-100 text-purple-800 border-purple-200',
    proposal_review: 'bg-orange-100 text-orange-800 border-orange-200',
    won: 'bg-green-100 text-green-800 border-green-200',
    lost: 'bg-gray-100 text-gray-800 border-gray-200',
    
    // Proposal statuses
    draft: 'bg-gray-100 text-gray-800 border-gray-200',
    in_review: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    qc_check: 'bg-orange-100 text-orange-800 border-orange-200',
    approved: 'bg-green-100 text-green-800 border-green-200',
    
    // QC statuses
    pass: 'bg-green-100 text-green-800 border-green-200',
    warn: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    fail: 'bg-red-100 text-red-800 border-red-200',
    pending: 'bg-gray-100 text-gray-800 border-gray-200',
    
    // Project statuses
    planning: 'bg-blue-100 text-blue-800 border-blue-200',
    active: 'bg-green-100 text-green-800 border-green-200',
    on_hold: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    completed: 'bg-green-100 text-green-800 border-green-200',
    closed: 'bg-gray-100 text-gray-800 border-gray-200',
    
    // Milestone statuses
    not_started: 'bg-gray-100 text-gray-800 border-gray-200',
    in_progress: 'bg-blue-100 text-blue-800 border-blue-200',
    delayed: 'bg-red-100 text-red-800 border-red-200',
    
    // Deliverable statuses
    under_review: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    accepted: 'bg-green-100 text-green-800 border-green-200',
  };
  
  return statusColors[status] || 'bg-gray-100 text-gray-800 border-gray-200';
}

/**
 * Get status label in Portuguese
 */
export function getStatusLabel(status: string): string {
  const statusLabels: Record<string, string> = {
    new: 'Novo',
    analyzing: 'Em Análise',
    go: 'Go',
    no_go: 'No-Go',
    proposal_draft: 'Proposta em Rascunho',
    proposal_review: 'Proposta em Revisão',
    submitted: 'Submetida',
    won: 'Ganha',
    lost: 'Não Aprovada',
    draft: 'Rascunho',
    in_review: 'Em Revisão',
    qc_check: 'QC em Curso',
    approved: 'Aprovada',
    
    // Project statuses
    planning: 'Em Planeamento',
    active: 'Em Execução',
    on_hold: 'Em Pausa',
    completed: 'Concluído',
    closed: 'Fechado',
    
    // Milestone statuses
    not_started: 'Não Iniciado',
    delayed: 'Atrasado',
    
    // Deliverable statuses
    under_review: 'Em Revisão',
    accepted: 'Aceite',
  };
  
  return statusLabels[status] || status;
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * Generate unique ID
 */
export function generateId(): string {
  return Math.random().toString(36).substring(2, 15);
}
