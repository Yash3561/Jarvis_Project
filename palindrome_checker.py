def is_palindrome(text):
    processed_text = ''.join(filter(str.isalnum, text)).lower()
    return processed_text == processed_text[::-1]

# Test cases
print(is_palindrome("racecar"))  # True
print(is_palindrome("A man, a plan, a canal: Panama"))  # True
print(is_palindrome("hello"))  # False
print(is_palindrome("Madam, I'm Adam"))  # True