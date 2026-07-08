import { describe, it, expect, vi } from 'vitest'
import { validateCpf, validateCnpj, validatePhone, validateEmail } from '../src/utils/validators'

describe('Validators', () => {
  describe('validateCpf', () => {
    it('should return true for valid CPF', () => {
      expect(validateCpf('123.456.789-09')).toBe(true)
      expect(validateCpf('529.982.247-25')).toBe(true)
    })

    it('should return false for invalid CPF', () => {
      expect(validateCpf('123.456.789')).toBe(false)
      expect(validateCpf('111.111.111-11')).toBe(false)
    })
  })

  describe('validateCnpj', () => {
    it('should return true for valid CNPJ', () => {
      expect(validateCnpj('11.444.777/0001-61')).toBe(true)
    })

    it('should return false for invalid CNPJ', () => {
      expect(validateCnpj('11.444.777/0001-6')).toBe(false)
      expect(validateCnpj('11.111.111/1111-11')).toBe(false)
    })
  })

  describe('validatePhone', () => {
    it('should return true for valid phone numbers', () => {
      expect(validatePhone('(11) 91234-5678')).toBe(true)
      expect(validatePhone('11912345678')).toBe(true)
    })

    it('should return false for invalid phone numbers', () => {
      expect(validatePhone('119123456')).toBe(false)
      expect(validatePhone('(00) 91234-5678')).toBe(false)
    })
  })

  describe('validateEmail', () => {
    it('should return true for valid emails', () => {
      expect(validateEmail('test@example.com')).toBe(true)
    })

    it('should return false for invalid emails', () => {
      expect(validateEmail('invalid-email')).toBe(false)
      expect(validateEmail('test@')).toBe(false)
    })
  })
})