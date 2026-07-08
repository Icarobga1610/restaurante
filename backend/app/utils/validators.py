"""Validation utilities for Brazilian documents and phone numbers."""

import re
from typing import Optional


def validate_cpf(cpf: str) -> bool:
    """Validate Brazilian CPF number."""
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    if len(cpf) != 11:
        return False
    
    if cpf == cpf[0] * 11:
        return False
    
    # Validate first digit
    sum_val = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit1 = (sum_val * 10) % 11
    if digit1 == 10:
        digit1 = 0
    if digit1 != int(cpf[9]):
        return False
    
    # Validate second digit
    sum_val = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit2 = (sum_val * 10) % 11
    if digit2 == 10:
        digit2 = 0
    if digit2 != int(cpf[10]):
        return False
    
    return True


def validate_cnpj(cnpj: str) -> bool:
    """Validate Brazilian CNPJ number."""
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    if len(cnpj) != 14:
        return False
    
    if cnpj == cnpj[0] * 14:
        return False
    
    # Validate first digit
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_val = sum(int(cnpj[i]) * weights1[i] for i in range(12))
    digit1 = sum_val % 11
    digit1 = 0 if digit1 < 2 else 11 - digit1
    if digit1 != int(cnpj[12]):
        return False
    
    # Validate second digit
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_val = sum(int(cnpj[i]) * weights2[i] for i in range(13))
    digit2 = sum_val % 11
    digit2 = 0 if digit2 < 2 else 11 - digit2
    if digit2 != int(cnpj[13]):
        return False
    
    return True


def validate_phone(phone: str) -> bool:
    """Validate Brazilian phone number format."""
    phone = re.sub(r'[^0-9]', '', phone)
    
    # Brazilian phone: 10 or 11 digits
    if len(phone) not in (10, 11):
        return False
    
    # DDD must be between 11 and 99
    ddd = int(phone[:2])
    if ddd < 11 or ddd > 99:
        return False
    
    # Mobile numbers start with 9
    if len(phone) == 11 and phone[2] != '9':
        return False
    
    return True


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def format_cpf(cpf: str) -> str:
    """Format CPF as XXX.XXX.XXX-XX."""
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def format_cnpj(cnpj: str) -> str:
    """Format CNPJ as XX.XXX.XXX/XXXX-XX."""
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def format_phone(phone: str) -> str:
    """Format phone as (XX) XXXXX-XXXX or (XX) XXXX-XXXX."""
    phone = re.sub(r'[^0-9]', '', phone)
    if len(phone) == 11:
        return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    elif len(phone) == 10:
        return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
    return phone


def detect_document_type(document: str) -> Optional[str]:
    """Detect if document is CPF or CNPJ."""
    if not document:
        return None
    doc = re.sub(r'[^0-9]', '', document)
    if len(doc) == 11 and validate_cpf(doc):
        return "cpf"
    elif len(doc) == 14 and validate_cnpj(doc):
        return "cnpj"
    return None