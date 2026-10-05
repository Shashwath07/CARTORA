import pytest
from memory.memory_service import get_bank_id
from agent.response import format_response
from agent.prompts import build_support_prompt

def test_bank_id_isolation():
    assert get_bank_id('C1001') == 'customer-c1001'
    assert get_bank_id('C1002') == 'customer-c1002'
    assert get_bank_id('C1001') != get_bank_id('C1002')

def test_bank_id_sanitization():
    assert get_bank_id('  C1001  ') == 'customer-c1001'
    assert get_bank_id('C@#1001') == 'customer-c--1001'

def test_format_response_fallback():
    result = format_response('')
    assert 'unable to generate' in result.lower() or 'apologize' in result.lower()

def test_format_response_strips_prefix():
    result = format_response('Cartora Assist: Hello there!')
    assert result == 'Hello there!'

def test_format_response_length_limit():
    long_text = 'A' * 2000
    result = format_response(long_text)
    assert len(result) <= 1500

def test_prompt_has_system_and_user():
    messages = build_support_prompt('Hello')
    assert len(messages) == 2
    assert messages[0]['role'] == 'system'
    assert messages[1]['role'] == 'user'
    assert messages[1]['content'] == 'Hello'

def test_prompt_includes_profile():
    messages = build_support_prompt('Hello', customer_profile={'name': 'Maya', 'tier': 'Plus'})
    system = messages[0]['content']
    assert 'Maya' in system
    assert 'Plus' in system

def test_prompt_includes_memories():
    messages = build_support_prompt('Hello', memories=['Previous issue about earbuds'])
    system = messages[0]['content']
    assert 'earbuds' in system

def test_prompt_includes_commerce():
    messages = build_support_prompt('Hello', commerce_context='Order CT-824501 delivered')
    system = messages[0]['content']
    assert 'CT-824501' in system
