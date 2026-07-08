"""Unit tests for validators."""

import pytest
from app.utils.validators import (
    validate_cpf,
    validate_cnpj,
    validate_phone,
    validate_email,
    format_cpf,
    format_cnpj,
    format_phone,
    detect_document_type,
)


class TestValidateCPF:
    """Tests for CPF validation."""
    
    def test_valid_cpf(self):
        """Test valid CPF numbers."""
        assert validate_cpf("123.456.789-09") is True
        assert validate_cpf("529.982.247-25") is True
        assert validate_cpf("12345678909") is True
    
    def test_invalid_cpf_wrong_length(self):
        """Test CPF with wrong length."""
        assert validate_cpf("123.456.789") is False
        assert validate_cpf("1234567890123") is False
    
    def test_invalid_cpf_all_same_digit(self):
        """Test CPF with all same digits."""
        assert validate_cpf("111.111.111-11") is False
        assert validate_cpf("000.000.000-00") is False
    
    def test_invalid_cpf_wrong_check_digits(self):
        """Test CPF with wrong check digits."""
        assert validate_cpf("123.456.789-00") is False
        assert validate_cpf("529.982.247-26") is False


class TestValidateCNPJ:
    """Tests for CNPJ validation."""
    
    def test_valid_cnpj(self):
        """Test valid CNPJ numbers."""
        assert validate_cnpj("11.444.777/0001-61") is True
        assert validate_cnpj("11222333000181") is True
    
    def test_invalid_cnpj_wrong_length(self):
        """Test CNPJ with wrong length."""
        assert validate_cnpj("11.444.777/0001-6") is False
        assert validate_cnpj("112223330001812") is False
    
    def test_invalid_cnpj_all_same_digit(self):
        """Test CNPJ with all same digits."""
        assert validate_cnpj("11.111.111/1111-11") is False
        assert validate_cnpj("22.222.222/2222-22") is False
    
    def test_invalid_cnpj_wrong_check_digits(self):
        """Test CNPJ with wrong check digits."""
        assert validate_cnpj("11.444.777/0001-62") is False


class TestValidatePhone:
    """Tests for phone validation."""
    
    def test_valid_phone_mobile(self):
        """Test valid mobile phone numbers."""
        assert validate_phone("(11) 91234-5678") is True
        assert validate_phone("11912345678") is True
    
    def test_valid_phone_landline(self):
        """Test valid landline phone numbers."""
        assert validate_phone("(11) 1234-5678") is True
        assert validate_phone("1112345678") is True
    
    def test_invalid_phone_wrong_length(self):
        """Test phone with wrong length."""
        assert validate_phone("119123456") is False  # 9 digits
        assert validate_phone("119123456789") is False  # 12 digits
    
    def test_invalid_phone_invalid_ddd(self):
        """Test phone with invalid DDD."""
        assert validate_phone("(00) 91234-5678") is False
        assert validate_phone("(100) 91234-5678") is False


class TestValidateEmail:
    """Tests for email validation."""
    
    def test_valid_email(self):
        """Test valid email addresses."""
        assert validate_email("test@example.com") is True
        assert validate_email("user.name@domain.co.uk") is True
    
    def test_invalid_email(self):
        """Test invalid email addresses."""
        assert validate_email("invalid-email") is False
        assert validate_email("test@") is False
        assert validate_email("@domain.com") is False


class TestFormatCPF:
    """Tests for CPF formatting."""
    
    def test_format_cpf(self):
        """Test CPF formatting."""
        assert format_cpf("12345678909") == "123.456.789-09"
        assert format_cpf("52998224725") == "529.982.247-25"


class TestFormatCNPJ:
    """Tests for CNPJ formatting."""
    
    def test_format_cnpj(self):
        """Test CNPJ formatting."""
        assert format_cnpj("11222333000181") == "11.222.333/0001-81"


class TestFormatPhone:
    """Tests for phone formatting."""
    
    def test_format_phone_mobile(self):
        """Test mobile phone formatting."""
        assert format_phone("11912345678") == "(11) 91234-5678"
    
    def test_format_phone_landline(self):
        """Test landline phone formatting."""
        assert format_phone("1112345678") == "(11) 1234-5678"


class TestDetectDocumentType:
    """Tests for document type detection."""
    
    def test_detect_cpf(self):
        """Test CPF detection."""
        assert detect_document_type("123.456.789-09") == "cpf"
        assert detect_document_type("529.982.247-25") == "cpf"
    
    def test_detect_cnpj(self):
        """Test CNPJ detection."""
        assert detect_document_type("11.444.777/0001-61") == "cnpj"
    
    def test_detect_invalid(self):
        """Test invalid document detection."""
        assert detect_document_type("12345678901") is None
        assert detect_document_type("invalid") is None
        assert detect_document_type("") is None