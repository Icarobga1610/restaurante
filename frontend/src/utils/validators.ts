/**
 * Validation utilities for Brazilian documents and phone numbers.
 */

/**
 * Validate Brazilian CPF number
 */
export function validateCpf(cpf: string): boolean {
  const cleanCpf = cpf.replace(/\D/g, '')
  
  if (cleanCpf.length !== 11) {
    return false
  }
  
  if (cleanCpf === cleanCpf[0].repeat(11)) {
    return false
  }
  
  // Validate first check digit
  let sum = 0
  for (let i = 0; i < 9; i++) {
    sum += parseInt(cleanCpf[i]) * (10 - i)
  }
  let remainder = (sum * 10) % 11
  if (remainder === 10) remainder = 0
  if (remainder !== parseInt(cleanCpf[9])) {
    return false
  }
  
  // Validate second check digit
  sum = 0
  for (let i = 0; i < 10; i++) {
    sum += parseInt(cleanCpf[i]) * (11 - i)
  }
  remainder = (sum * 10) % 11
  if (remainder === 10) remainder = 0
  if (remainder !== parseInt(cleanCpf[10])) {
    return false
  }
  
  return true
}

/**
 * Validate Brazilian CNPJ number
 */
export function validateCnpj(cnpj: string): boolean {
  const cleanCnpj = cnpj.replace(/\D/g, '')
  
  if (cleanCnpj.length !== 14) {
    return false
  }
  
  if (cleanCnpj === cleanCnpj[0].repeat(14)) {
    return false
  }
  
  // Validate first check digit
  const weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
  let sum = 0
  for (let i = 0; i < 12; i++) {
    sum += parseInt(cleanCnpj[i]) * weights1[i]
  }
  let remainder = sum % 11
  const digit1 = remainder < 2 ? 0 : 11 - remainder
  if (digit1 !== parseInt(cleanCnpj[12])) {
    return false
  }
  
  // Validate second check digit
  const weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
  sum = 0
  for (let i = 0; i < 13; i++) {
    sum += parseInt(cleanCnpj[i]) * weights2[i]
  }
  remainder = sum % 11
  const digit2 = remainder < 2 ? 0 : 11 - remainder
  if (digit2 !== parseInt(cleanCnpj[13])) {
    return false
  }
  
  return true
}

/**
 * Validate Brazilian phone number format
 */
export function validatePhone(phone: string): boolean {
  const cleanPhone = phone.replace(/\D/g, '')
  
  // Brazilian phone: 10 or 11 digits
  if (cleanPhone.length !== 10 && cleanPhone.length !== 11) {
    return false
  }
  
  // DDD must be between 11 and 99
  const ddd = parseInt(cleanPhone.substring(0, 2))
  if (ddd < 11 || ddd > 99) {
    return false
  }
  
  // Mobile numbers start with 9
  if (cleanPhone.length === 11 && cleanPhone[2] !== '9') {
    return false
  }
  
  return true
}

/**
 * Validate email format
 */
export function validateEmail(email: string): boolean {
  const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  return pattern.test(email)
}

/**
 * Format CPF as XXX.XXX.XXX-XX
 */
export function formatCpf(cpf: string): string {
  const cleanCpf = cpf.replace(/\D/g, '')
  if (cleanCpf.length !== 11) return cpf
  return `${cleanCpf.substring(0, 3)}.${cleanCpf.substring(3, 6)}.${cleanCpf.substring(6, 9)}-${cleanCpf.substring(9)}`
}

/**
 * Format CNPJ as XX.XXX.XXX/XXXX-XX
 */
export function formatCnpj(cnpj: string): string {
  const cleanCnpj = cnpj.replace(/\D/g, '')
  if (cleanCnpj.length !== 14) return cnpj
  return `${cleanCnpj.substring(0, 2)}.${cleanCnpj.substring(2, 5)}.${cleanCnpj.substring(5, 8)}/${cleanCnpj.substring(8, 12)}-${cleanCnpj.substring(12)}`
}

/**
 * Format phone as (XX) XXXXX-XXXX or (XX) XXXX-XXXX
 */
export function formatPhone(phone: string): string {
  const cleanPhone = phone.replace(/\D/g, '')
  if (cleanPhone.length === 11) {
    return `(${cleanPhone.substring(0, 2)}) ${cleanPhone.substring(2, 7)}-${cleanPhone.substring(7)}`
  } else if (cleanPhone.length === 10) {
    return `(${cleanPhone.substring(0, 2)}) ${cleanPhone.substring(2, 6)}-${cleanPhone.substring(6)}`
  }
  return phone
}

/**
 * Detect if document is CPF or CNPJ
 */
export function detectDocumentType(document: string): 'cpf' | 'cnpj' | null {
  if (!document) return null
  const cleanDoc = document.replace(/\D/g, '')
  if (cleanDoc.length === 11 && validateCpf(cleanDoc)) {
    return 'cpf'
  } else if (cleanDoc.length === 14 && validateCnpj(cleanDoc)) {
    return 'cnpj'
  }
  return null
}